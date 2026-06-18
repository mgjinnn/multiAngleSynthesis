# multiAngleSynthesis

简体中文 | [English](README_en.md)

Baseline: registry.cn-hangzhou.aliyuncs.com/clg_test/clg_test1:v1.0

用法：
```bash
bash run.sh
```




## 参赛规范 <br/>
1) 工程开发目录需要在/workspace/multiAngleSynthesis/目录下, 启动脚本固定使用run.sh, 提交镜像中需使用baseline中的run.sh, evaluate.py和generates.py, 需保持和baseline一致, 测试数据目录结构保持与baseline一致. <br/>
2) 平台提供了基于镜像地址提交镜像的方式, 将本地镜像推送至阿里云容器镜像仓库后, 设置为公开镜像, 在比赛平台提交页面中输入镜像地址. 由比赛平台拉取镜像运行, 运行结束即可在成绩页面查询评测结果. 推送至阿里云容器镜像仓库, 镜像仓库名称尽量不关联上比赛相关的词语, 以免被检索从而泄漏.<br/>
3) 运行镜像时，容器内任何网络不可用，请将依赖的软件、包在镜像中装好. <br/>
4) 为了合理分配资源，平均单张生成时间不超过30秒钟，超出后程序自动停止，结果将不被接受.<br/>
5) 请使用生成式模型参与本次比赛，勿直接拷贝或修改原始数据到生成结果中.<br/>
6) 如用到别的底座模型,建议联系组委会下载和挂载,以减少镜像的体积，降低镜像上传和下载的时间. baseline中底座模型会挂载到/workspace/multiAngleSynthesis/diffSynth_studio/models目录下.<br/>
<br/>

## 资源配置：<br/>
CPU: 16核 <br/>
内存: 64 GiB <br/>
GPU: Nvidia A100 40G, 显存开销在40G以内 <br/>
<br/>

## 阿里云镜像仓库使用方法:<br/>
1) 注册阿里云账户: https://cr.console.aliyun.com/cn-hangzhou/instances. <br/>
2) 在工作台搜索[容器镜像服务], 进入后选择[个人实例]. <br/>
3) 创建镜像仓库、命名空间, 设置仓库名称，选择公开或私有仓库(此处选择公开),  选择本地仓库. <br/>
4) 本地登录阿里云Docker Registry示例: <br/>
```bash
$ docker login --username=[阿里云id] registry.cn-hangzhou.aliyuncs.com
$ docker tag [ImageId] registry.cn-hangzhou.aliyuncs.com/xx1/xx2:[镜像版本号]
$ docker push registry.cn-hangzhou.aliyuncs.com/xx1/xx2:[镜像版本号]
请根据实际镜像信息替换示例中的[阿里云id], [ImageId]和[镜像版本号]参数.
```
5) 在比赛提交页面提交: registry.cn-hangzhou.aliyuncs.com/xx1/xx2:[镜像版本号].
<br/>

## Lora示例:<br/>
baseline训练示例依赖阿里开源项目：https://github.com/modelscope/DiffSynth-Studio  <br/>
1) 模型预训练权重文件在/workspace/multiAngleSynthesis/diffSynth_studio/models目录下，该目录为共享目录，FLUX.2-klein-base-4B已下载好，若需要使用其它模型，请参赛者自行下载，下载请参考： <br/>
```bash
$ modelscope download --model Qwen/Qwen-Image-Edit-2511 README.md --local_dir /workspace/multiAngleSynthesis/diffSynth_studio/models
```
2) 训练示例数据集在/workspace/multiAngleSynthesis/diffSynth_studio/datasets目录下. <br/>
3) 以FLUX.2-klein-base-4B模型为例，Lora微调过程如下: <br/>
```bash
$ cd multiAngleSynthesis/diffSynth_studio
$ python make_dataset_jsonfile.py
$ sh examples/flux2/model_training/lora/FLUX.2-klein-base-4B.sh
```

> **注意：**
> - lora结果存放在 `diffSynth_studio/train` 对应目录下，可通过参数 `--output_path` 修改。
> - 请勿将训练结果存放在 `diffSynth_studio/models` 目录下，以免被其它参赛者覆盖。
> - FLUX.2-klein-base-4B 微调显存占用约 19G，qwen-image-edit-2511 约 60G（请自行配置多卡 LoRA）。
> - 示例中开启了 SwanLab 日志，若不需要可删除 `--enable_swanlab_log` 参数。
> - 可通过设置 `DIFFSYNTH_MODEL_BASE_PATH` 环境变量指定模型加载目录。

4) 微调结果验证<br/>
```bash
$ cd multiAngleSynthesis/diffSynth_studio
$ sh examples/flux2/model_training/validate_lora/FLUX.2-klein-base-4B.py
# 生成式模型训练过程loss值不如常规回归/分类任务直观，建议若干epoch可视化验证训练效果
```
5) 提交微调结果：请参赛者参考并修改generate_images.py推理部分代码，加载微调好的权重<br/>

其它模型微调请参考DiffSynth-Studio文档：https://diffsynth-studio-doc.readthedocs.io/zh-cn/latest/
## Reference <br/>
https://github.com/modelscope/DiffSynth-Studio<br/>