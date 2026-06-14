"""
图像生成脚本
从 raw_data 目录读取 center_medium.png，生成 26 个不同角度的图像
"""

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from generate_images import ImageGenerator

# 定义目录路径
SCRIPT_DIR = Path(__file__).parent
RAW_DATA_DIR = SCRIPT_DIR / "raw_data"
RESULTS_DIR = SCRIPT_DIR / "results"


def main():
    """主函数：从 raw_data 目录生成 results 图像"""
    print("=" * 60)
    print("图像生成流程")
    print("=" * 60)
    
    # 检查 raw_data 目录是否存在
    if not RAW_DATA_DIR.exists():
        print(f"错误: raw_data 目录不存在: {RAW_DATA_DIR}")
        return
    
    # 获取 raw_data 目录下的所有子目录
    subdirs = sorted([d.name for d in RAW_DATA_DIR.iterdir() if d.is_dir()])
    
    if not subdirs:
        print(f"警告: raw_data 目录下没有子目录")
        return
    
    print(f"发现 {len(subdirs)} 个数据组: {subdirs}")
    print()
    
    # 初始化图像生成器并加载模型
    generator = ImageGenerator()
    print("正在加载模型...")
    generator.load_model()
    print()
    
    # 清理旧的 results 目录
    if RESULTS_DIR.exists():
        import shutil
        shutil.rmtree(RESULTS_DIR)
        print("已清理旧的 results 目录")
    
    # 为每个子目录创建对应的 results 子目录
    total_generated = 0
    inference_times = []

    for i, subdir in enumerate(subdirs, 1):
        print(f"\n[{i}/{len(subdirs)}] 处理组: {subdir}")
        print("-" * 40)
        
        # 原始数据路径
        raw_subdir = RAW_DATA_DIR / subdir
        center_image_path = raw_subdir / "center_medium.png"
        
        # 结果输出路径
        result_subdir = RESULTS_DIR / subdir
        result_subdir.mkdir(parents=True, exist_ok=True)
        
        # 检查 center_medium.png 是否存在
        if not center_image_path.exists():
            print(f"  警告: center_medium.png 不存在，跳过")
            continue
        
        print(f"输入图像: {center_image_path}")
        print(f"输出目录: {result_subdir}")
        
        # 调用 generate 函数生成 26 个角度的图像
        try:
            start_time = time.time()
            generator.generate(str(center_image_path), str(result_subdir))
            inference_time = time.time() - start_time
            inference_times.append(inference_time)
            print(f"推理时间: {inference_time:.2f} 秒")
            print(f"成功生成图像到: {result_subdir}")
            total_generated += 1
        except Exception as e:
            print(f"生成失败: {e}")
            import traceback
            traceback.print_exc()

    # 计算平均推理时间
    if inference_times:
        avg_inference_time = sum(inference_times) / len(inference_times)
        print()
        print(f"平均推理时间: {avg_inference_time:.2f} 秒 (共 {len(inference_times)} 组)")

        # 如果平均时间超过 30 秒，写入 results.txt
        if avg_inference_time > 30:
            results_file = SCRIPT_DIR / "results.txt"
            # 如果文件存在则先删除
            if results_file.exists():
                results_file.unlink()
            with open(results_file, "w", encoding="utf-8") as f:
                f.write("生成超时")
            print(f"警告: 平均生成时间超过30秒，已写入 {results_file}")

    print()
    print("=" * 60)
    print(f"生成完成! 成功处理 {total_generated}/{len(subdirs)} 个数据组")
    print(f"results 目录: {RESULTS_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
