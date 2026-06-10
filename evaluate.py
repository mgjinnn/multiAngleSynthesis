import os
import sys
import json
import logging
import torch
import pyiqa
import lpips
import numpy as np
import cv2
from pathlib import Path
from PIL import Image
from tqdm import tqdm
from argparse import ArgumentParser
from torchvision import transforms

from LAR_IQA.models.mobilenet_merged import MobileNetMerged
from LAR_IQA.models.mobilenet_merged_with_kan import MobileNetMergedWithKAN


DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
RAW_DATA_DIR = "./raw_data"
RESULTS_DIR = "./results"
REQUIRED_IMAGES_PER_DIR = 26  # results 目录排除 center_medium.png 后需要的数量
SUPPORTED_FORMATS = (".jpg", ".jpeg", ".png", ".bmp", ".tiff")
BATCH_SIZE = 8
ENABLE_COMPILE = True
PSNR_MAX_DB = 40.0  # PSNR 归一化上限（dB）

# LAR-IQA 配置
LAR_IQA_MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "LAR_IQA", "AIM_Training_2branche_KAN-Head.pt")
LAR_IQA_USE_KAN = True
LAR_IQA_COLOR_SPACE = "RGB"

METRICS = {
    "psnr": True,
    "ssim": True,
    "lpips": True,
    "lar_iqa": True,
}
EXCLUDED_FILE = "center_medium.png"  # 不参与评估的文件

# 配置 logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def load_lar_iqa_model(model_path, use_kan, device):
    """加载 LAR-IQA 模型"""
    if use_kan:
        model = MobileNetMergedWithKAN()
    else:
        model = MobileNetMerged()
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    return model


def preprocess_lar_iqa(image_path, color_space, device):
    """LAR-IQA 图像预处理"""
    image = Image.open(image_path).convert('RGB')
    if color_space == "HSV":
        image = Image.fromarray(cv2.cvtColor(np.array(image), cv2.COLOR_RGB2HSV))
    elif color_space == "LAB":
        image = Image.fromarray(cv2.cvtColor(np.array(image), cv2.COLOR_RGB2LAB))
    elif color_space == "YUV":
        image = Image.fromarray(cv2.cvtColor(np.array(image), cv2.COLOR_RGB2YUV))
    
    transform_authentic = transforms.Compose([
        transforms.Resize((384, 384)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    transform_synthetic = transforms.Compose([
        transforms.CenterCrop((1280, 1280)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    image_authentic = transform_authentic(image).unsqueeze(0).to(device)
    image_synthetic = transform_synthetic(image).unsqueeze(0).to(device)

    return image_authentic, image_synthetic



def get_image_paths(directory, recursive=False):
    """
    获取目录下所有支持格式的图像路径，按文件名排序

    Args:
        directory: 目录路径（Path 对象）
        recursive: 是否递归查找子目录

    Returns:
        图像路径列表
    """
    image_paths = []
    directory = Path(directory)

    if recursive:
        # 递归查找所有图片
        for img_path in sorted(directory.rglob('*')):
            if img_path.is_file() and img_path.suffix.lower() in SUPPORTED_FORMATS:
                image_paths.append(str(img_path))
    else:
        # 仅查找当前目录
        for file in sorted(os.listdir(directory)):
            if file.lower().endswith(SUPPORTED_FORMATS):
                image_paths.append(str(directory / file))

    return image_paths


def check_directory_structure(raw_data_dir=RAW_DATA_DIR, results_dir=RESULTS_DIR,
                               required_count=REQUIRED_IMAGES_PER_DIR):
    """
    检查目录结构是否符合要求

    Args:
        raw_data_dir: 原始数据目录（不检查图片数量）
        results_dir: 结果目录（需要检查图片数量）
        required_count: results 子目录排除 EXCLUDED_FILE 后应包含的图片数量

    Returns:
        (raw_subdirs, res_subdirs) 子目录列表
    """
    raw_dir = Path(raw_data_dir)
    res_dir = Path(results_dir)

    if not raw_dir.exists():
        raise FileNotFoundError(f"原始数据目录不存在: {raw_data_dir}")
    if not res_dir.exists():
        raise FileNotFoundError(f"结果目录不存在: {results_dir}")

    # 获取子目录列表
    raw_subdirs = sorted([d for d in raw_dir.iterdir() if d.is_dir()])
    res_subdirs = sorted([d for d in res_dir.iterdir() if d.is_dir()])

    if not raw_subdirs and not res_subdirs:
        # 没有子目录，将当前目录作为唯一一组
        logger.info("未发现子目录，将顶层目录作为一组数据处理")
        return [raw_dir], [res_dir]

    if len(raw_subdirs) != len(res_subdirs):
        raise ValueError(
            f"原始数据子目录数量({len(raw_subdirs)})与结果子目录数量({len(res_subdirs)})不一致"
        )

    # 只检查 results 目录的图片数量（排除 EXCLUDED_FILE）
    logger.info(f"检查 results 目录下每个子目录的图片数量（排除 {EXCLUDED_FILE} 后需 {required_count} 张）")
    for subdir in res_subdirs:
        images = [f for f in get_image_paths(subdir) if os.path.basename(f) != EXCLUDED_FILE]
        if len(images) != required_count:
            raise ValueError(
                f"目录 {subdir} 有效图片数量不符合要求: "
                f"实际{len(images)}张，需要{required_count}张（已排除 {EXCLUDED_FILE}）"
            )

    # 检查对应子目录的文件名是否一致
    logger.info("检查原始数据与结果目录的文件名是否匹配")
    for raw_subdir, res_subdir in zip(raw_subdirs, res_subdirs):
        raw_images = sorted([os.path.basename(p) for p in get_image_paths(raw_subdir)])
        res_images = sorted([os.path.basename(p) for p in get_image_paths(res_subdir)])

        # 排除 EXCLUDED_FILE 后比较
        raw_images_filtered = [f for f in raw_images if f != EXCLUDED_FILE]
        res_images_filtered = [f for f in res_images if f != EXCLUDED_FILE]

        if raw_images_filtered != res_images_filtered:
            raise ValueError(
                f"目录 {raw_subdir} 和 {res_subdir} 的文件名不匹配\n"
                f"原始: {raw_images_filtered}\n结果: {res_images_filtered}"
            )

    logger.info(f"目录结构检查通过，共发现 {len(raw_subdirs)} 组数据")
    return raw_subdirs, res_subdirs


def print_evaluation_summary(all_results):
    """打印评估结果汇总"""
    logger.info("\n" + "=" * 80)
    logger.info("图像质量评估结果汇总")
    logger.info("=" * 80)

    group_scores = []

    for group_name, results in all_results.items():
        logger.info(f"\n【组 {group_name}】")
        logger.info("-" * 40)

        for metric, avg_score in results.items():
            logger.info(f"{metric.upper():12} 平均值: {avg_score:.6f}")

        # 收集 group_score
        if "group_score" in results:
            group_scores.append(results["group_score"])

        logger.info("-" * 40)

    # 计算数据集平均得分（所有组 group_score 的平均值）
    dataset_avg_score = sum(group_scores) / len(group_scores) if group_scores else 0.0
    logger.info(f"\n【数据集平均得分】: {dataset_avg_score:.6f}")
    logger.info("=" * 80)



class QualityEvaluator:
    """图像质量评估器，支持全参考和无参考指标"""

    def __init__(self, device=DEVICE, metrics=None, batch_size=BATCH_SIZE,
                 enable_compile=ENABLE_COMPILE):
        """
        Args:
            device: 评估使用的设备
            metrics: 启用的指标字典
            batch_size: 批处理大小
            enable_compile: 是否启用 torch.compile 加速
        """
        self.device = device
        self.metrics_config = metrics if metrics is not None else METRICS
        self.batch_size = batch_size
        self.enable_compile = enable_compile
        self.metrics = {}
        self.lar_iqa_model = None
        self.lar_iqa_color_space = LAR_IQA_COLOR_SPACE
        self._load_metrics()

    def _load_metrics(self):
        """加载所有需要的评估指标"""
        logger.info("正在加载评估模型...")

        # 全参考指标
        if self.metrics_config.get("psnr"):
            self.metrics["psnr"] = pyiqa.create_metric("psnr", device=self.device)
        if self.metrics_config.get("ssim"):
            self.metrics["ssim"] = pyiqa.create_metric("ssim", device=self.device)
        if self.metrics_config.get("lpips"):
            # 使用 pyiqa 创建 LPIPS（通过 HF_ENDPOINT 镜像下载）
            self.metrics["lpips"] = pyiqa.create_metric("lpips", device=self.device)

        # 无参考指标 - LAR-IQA
        if self.metrics_config.get("lar_iqa"):
            if os.path.exists(LAR_IQA_MODEL_PATH):
                logger.info(f"加载 LAR-IQA 模型: {LAR_IQA_MODEL_PATH}")
                self.lar_iqa_model = load_lar_iqa_model(LAR_IQA_MODEL_PATH, LAR_IQA_USE_KAN, self.device)
                if self.enable_compile and self.device.type == "cuda":
                    try:
                        self.lar_iqa_model = torch.compile(self.lar_iqa_model, mode="max-autotune")
                    except Exception as e:
                        logger.warning(f"警告: LAR-IQA 编译失败: {e}")
            else:
                logger.warning(f"LAR-IQA 模型文件不存在: {LAR_IQA_MODEL_PATH}")

        logger.info("所有模型加载完成")

    def _filter_paths(self, paths):
        """过滤掉排除文件"""
        return [p for p in paths if os.path.basename(p) != EXCLUDED_FILE]

    def calculate_full_reference_metrics(self, raw_paths, res_paths):
        """
        计算全参考指标 (PSNR/SSIM/LPIPS)

        Args:
            raw_paths: 原始图片路径列表
            res_paths: 渲染图片路径列表

        Returns:
            指标名字典 {metric_name: avg_score}
        """
        raw_paths = self._filter_paths(raw_paths)
        res_paths = self._filter_paths(res_paths)

        results = {
            metric: [] for metric in ["psnr", "ssim", "lpips"]
            if self.metrics_config.get(metric)
        }

        total_batches = (len(raw_paths) + self.batch_size - 1) // self.batch_size

        for i in tqdm(range(total_batches), desc="计算全参考指标"):
            batch_raw = raw_paths[i * self.batch_size : (i + 1) * self.batch_size]
            batch_res = res_paths[i * self.batch_size : (i + 1) * self.batch_size]

            # 加载图像
            transform = transforms.Compose([
                transforms.ToTensor(),
            ])
            raw_tensors = [transform(Image.open(p).convert('RGB')).to(self.device) for p in batch_raw]
            res_tensors = [transform(Image.open(p).convert('RGB')).to(self.device) for p in batch_res]

            raw_batch = torch.stack(raw_tensors)
            res_batch = torch.stack(res_tensors)

            # 计算指标
            if self.metrics_config.get("psnr"):
                psnr_scores = self.metrics["psnr"](res_batch, raw_batch).detach().cpu().numpy().flatten()
                # 归一化 PSNR 到 [0, 1]，上限为 PSNR_MAX_DB
                normalized_psnr = np.clip(psnr_scores / PSNR_MAX_DB, 0.0, 1.0)
                results["psnr"].extend(normalized_psnr.tolist())

            if self.metrics_config.get("ssim"):
                ssim_scores = self.metrics["ssim"](res_batch, raw_batch).detach().cpu().numpy().flatten()
                results["ssim"].extend(ssim_scores.tolist())

            if self.metrics_config.get("lpips"):
                lpips_scores = self.metrics["lpips"](res_batch, raw_batch).detach().cpu().numpy().flatten()
                # LPIPS 转换为得分：1 - LPIPS（值越小越好，转换为值越大越好）
                lpips_scores_as_score = 1.0 - lpips_scores
                results["lpips"].extend(lpips_scores_as_score.tolist())

        # 计算平均值
        avg_results = {}
        for metric, scores in results.items():
            if scores:
                # 过滤无效值（PSNR 可能为 inf）
                valid_scores = [s for s in scores if np.isfinite(s)]
                if valid_scores:
                    avg_results[metric] = sum(valid_scores) / len(valid_scores)
                else:
                    avg_results[metric] = float('inf')
            else:
                avg_results[metric] = 0.0

        return avg_results, results

    def calculate_no_reference_metrics(self, image_paths):
        """
        计算无参考指标 (LAR-IQA)

        Args:
            image_paths: 图片路径列表

        Returns:
            (指标名平均值字典, 详细分数字典)
        """
        image_paths = self._filter_paths(image_paths)

        results = {
            metric: [] for metric in ["lar_iqa"]
            if self.metrics_config.get(metric)
        }

        if self.metrics_config.get("lar_iqa") and self.lar_iqa_model is not None:
            # LAR-IQA 需要逐张处理
            for img_path in tqdm(image_paths, desc="计算 LAR-IQA 指标"):
                image_authentic, image_synthetic = preprocess_lar_iqa(img_path, self.lar_iqa_color_space, self.device)
                with torch.no_grad():
                    lar_iqa_score = self.lar_iqa_model(image_authentic, image_synthetic).item()
                # LAR-IQA 输出为质量分数，直接使用（值越大越好）
                results["lar_iqa"].append(lar_iqa_score)

        # 计算平均值
        avg_results = {}
        for metric, scores in results.items():
            if scores:
                avg_results[metric] = sum(scores) / len(scores)
            else:
                avg_results[metric] = 0.0

        return avg_results, results

    def evaluate_group(self, raw_dir, res_dir):
        """
        评估一组数据

        Args:
            raw_dir: 原始数据目录
            res_dir: 结果数据目录

        Returns:
            (group_results, per_file_results)
        """
        raw_paths = get_image_paths(raw_dir)
        res_paths = get_image_paths(res_dir)

        # 计算全参考指标
        fr_avg, fr_details = self.calculate_full_reference_metrics(raw_paths, res_paths)

        # 计算无参考指标
        nr_avg, nr_details = self.calculate_no_reference_metrics(res_paths)

        # 合并结果
        group_results = {**fr_avg, **nr_avg}

        # 计算每组得分（PSNR + SSIM + LPIPS + LAR-IQA）
        group_score = 0.0
        for metric in ["psnr", "ssim", "lpips", "lar_iqa"]:
            if metric in group_results:
                group_score += group_results[metric]
        group_results["group_score"] = group_score

        # 整理每个文件的详细结果
        per_file = {}
        raw_paths = self._filter_paths(raw_paths)
        for i, path in enumerate(raw_paths):
            name = os.path.basename(path)
            per_file[name] = {}
            for metric, scores in fr_details.items():
                if i < len(scores):
                    per_file[name][metric] = scores[i]
            for metric, scores in nr_details.items():
                if i < len(scores):
                    per_file[name][metric] = scores[i]

        return group_results, per_file


# ============================================================
# 主函数
# ============================================================
def main():
    parser = ArgumentParser(description="图像质量评估脚本（基于 pyiqa 和 LAR-IQA）")
    parser.add_argument('--raw_dir', '-r', type=str, default=RAW_DATA_DIR,
                        help=f"原始数据目录（默认: {RAW_DATA_DIR}）")
    parser.add_argument('--result_dir', '-s', type=str, default=RESULTS_DIR,
                        help=f"结果数据目录（默认: {RESULTS_DIR}）")
    parser.add_argument('--output_json', '-o', type=str, default=None,
                        help="输出 JSON 路径（可选）")
    parser.add_argument('--output_txt', '-t', type=str, default="evaluation_results.txt",
                        help="输出文本路径（默认: evaluation_results.txt）")
    parser.add_argument('--batch_size', '-b', type=int, default=BATCH_SIZE,
                        help=f"批处理大小（默认: {BATCH_SIZE}）")
    parser.add_argument('--no_compile', action='store_true',
                        help="禁用 torch.compile 加速")
    parser.add_argument('--required_count', type=int, default=REQUIRED_IMAGES_PER_DIR,
                        help=f"每组有效图片数（默认: {REQUIRED_IMAGES_PER_DIR}，已排除 {EXCLUDED_FILE}）")
    args = parser.parse_args()

    try:
        # 打印设备信息
        logger.info(f"使用设备: {DEVICE}")
        if DEVICE.type == "cuda":
            logger.info(f"GPU型号: {torch.cuda.get_device_name(0)}")
            logger.info(f"显存总量: {torch.cuda.get_device_properties(0).total_memory / 1024 ** 3:.1f} GB")

        # 检查目录结构
        logger.info("正在检查目录结构...")
        raw_subdirs, res_subdirs = check_directory_structure(
            args.raw_dir, args.result_dir, args.required_count
        )

        # 初始化评估器
        evaluator = QualityEvaluator(
            device=DEVICE,
            metrics=METRICS,
            batch_size=args.batch_size,
            enable_compile=not args.no_compile,
        )

        # 评估每组数据
        all_results = {}
        all_per_file = {}

        for i, (raw_dir, res_dir) in enumerate(zip(raw_subdirs, res_subdirs)):
            group_name = raw_dir.name
            logger.info(f"\n正在评估第 {i + 1}/{len(raw_subdirs)} 组: {group_name}")
            logger.info("-" * 40)

            group_results, per_file = evaluator.evaluate_group(raw_dir, res_dir)
            all_results[group_name] = group_results
            all_per_file[group_name] = per_file

            # 打印本组结果
            logger.info("本组结果:")
            for metric, avg_score in group_results.items():
                logger.info(f"{metric.upper():12} 平均值: {avg_score:.6f}")

        # 打印最终汇总
        print_evaluation_summary(all_results)

        # 计算整个数据集的平均得分（所有组 group_score 的平均值）
        group_scores = [results.get("group_score", 0.0) for results in all_results.values()]
        dataset_avg_score = sum(group_scores) / len(group_scores) if group_scores else 0.0

        # 保存结果到文本文件
        with open(args.output_txt, "w", encoding="utf-8") as f:
            f.write("图像质量评估结果\n")
            f.write("=" * 50 + "\n\n")

            for group_name, results in all_results.items():
                f.write(f"【组 {group_name}】\n")
                f.write("-" * 30 + "\n")
                for metric, avg_score in results.items():
                    f.write(f"{metric.upper():12} 平均值: {avg_score:.6f}\n")
                f.write("-" * 30 + "\n\n")

            f.write(f"【数据集平均得分】: {dataset_avg_score:.6f}\n")
            f.write("=" * 50 + "\n")

        logger.info(f"结果已保存至: {args.output_txt}")

        # 保存 JSON 结果
        if args.output_json:
            json_result = {
                "device": str(DEVICE),
                "num_groups": len(all_results),
                "excluded_file": EXCLUDED_FILE,
                "dataset_avg_score": dataset_avg_score,
                "groups": {}
            }
            for group_name, results in all_results.items():
                json_result["groups"][group_name] = {
                    "average": results,
                    "per_file": all_per_file.get(group_name, {})
                }
            with open(args.output_json, "w", encoding="utf-8") as f:
                json.dump(json_result, f, indent=2, ensure_ascii=False)
            logger.info(f"JSON 结果已保存至: {args.output_json}")

        # 生成只包含数据集平均得分的 results.txt 文件
        with open("results.txt", "w", encoding="utf-8") as f:
            f.write(f"{dataset_avg_score:.6f}\n")
        logger.info(f"数据集平均得分已保存至: results.txt")

    except Exception as e:
        logger.error(f"评估失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
