# Baseline

[简体中文](README.md) | English

Baseline: registry.cn-hangzhou.aliyuncs.com/clg_test/clg_test1:v1.0

Baseline Usage:
```bash
bash run.sh
```



## Challenge Specifications<br/>
## Contest Rules
1) The project working directory must be set to /workspace/multiAngleSynthesis/. The launch script is fixed as run.sh. The submitted Docker image must adopt the original run.sh, evaluate.py and generates.py files provided in the baseline package without structural alteration; the folder hierarchy of test data must also be consistent with that of the baseline. <br/>
2) The platform accepts submissions via container image links. Push your local container image to either Alibaba Cloud Container Registry (ACR) or Docker Hub and set the image to public visibility, then enter the image URL on the competition submission page. The platform will pull and run the submitted image automatically; once the execution finishes, evaluation results can be checked on the score page. When uploading images to Alibaba Cloud Container Registry or Docker Hub, refrain from using any competition-related terms in the repository name to avoid information leakage from public search indexing. <br/>
3) No network access is available within the container when running the image. Install all dependent software and packages in the image.<br/>
4) For rational resource allocation, the average processing time for a single view shall not exceed 30 seconds. Programs running beyond this time threshold will be forcibly terminated, and their corresponding outputs will be rejected. <br/>
5) Participants must utilize generative models for this competition. Do not directly copy or paste pixel data from input source images into your generated output results. <br/>
6) If other base models are used, it is recommended to contact the organizing committee for download and mounting to reduce the image size and decrease the time for image upload and download. In the baseline, base models will be mounted to the /workspace/multiAngleSynthesis/diffSynth_studio/models directory.<br/>
<br/>



## Computation Resources<br/>
CPU: 16 cores <br/>
Memory: 64GB <br/>
GPU: 40GB (NVIDIA GeForce A100)<br/>
<br/>


## Alibaba Cloud Docker Registry(Recommend):<br/>
1. Create Your Account and select individual account: https://cr.console.aliyun.com/ap-southeast-1/instances.<br/>
2. select [Instance of Personal Edition] and select [Create ACR Personal Edition].<br/>
3. select [Create Repository]. Create Namespace and Repository Name, and select Public Repository type, and choose [Local Repository].<br/>
4. Log in to Alibaba Cloud Docker Registry Locally:<br/>
```bash
$ docker login --username=[accountId] registry-intl.ap-southeast-1.aliyuncs.com
$ docker tag [ImageId] registry-intl.ap-southeast-1.aliyuncs.com/[namespace]/[repositoryName]:[tag]
$ docker push registry-intl.ap-southeast-1.aliyuncs.com/[namespace]/[repositoryName]:[tag]
Please replace the [accountId], [namespace], [repositoryName], [ImageId] and [tag] parameters based on your image.
```
5. submit your image: registry-intl.ap-southeast-1.aliyuncs.com/[namespace]/[repositoryName]:[tag].<br/>

## LoRA Fine-Tuning Example

The baseline training example depends on the open-source project developed by Alibaba:

https://github.com/modelscope/DiffSynth-Studio

### 1. Pretrained Model Weights

Pretrained model weights are stored in the `diffSynth_studio/models` directory, which is a shared directory.

The model **FLUX.2-klein-base-4B** has already been downloaded. If you would like to use other models, please download them yourself.

### 2. Training Dataset

The example training dataset is located in the `diffSynth_studio/datasets` directory and is provided with **read-only** permissions.

Please generate dataset configuration files in a different directory, as files cannot be modified within the dataset directory.

### 3. LoRA Fine-Tuning

Using **FLUX.2-klein-base-4B** as an example, the LoRA fine-tuning process is as follows:

```bash
cd diffSynth_studio

python make_dataset_jsonfile.py

sh examples/flux2/model_training/lora/FLUX.2-klein-base-4B.sh
```

**Notes:**

- LoRA checkpoints are saved under the corresponding directory in `diffSynth_studio/train` by default.
- You may change the output location using the `--output_path` argument.
- **Do not save checkpoints under `diffSynth_studio/models`**, as that directory is shared and files may be overwritten by other participants.
- The approximate GPU memory requirements are:
  - **FLUX.2-klein-base-4B:** ~19 GB
  - **qwen-image-edit-2511:** ~60 GB
- Participants are responsible for configuring multi-GPU LoRA training when necessary.
- SwanLab logging is enabled in the example scripts. If logging is not required, simply remove the `--enable_swanlab_log` argument.
- You may specify a custom model directory by setting the environment variable:

```bash
export DIFFSYNTH_MODEL_BASE_PATH=/path/to/models
```

### 4. Validate Fine-Tuned Results

```bash
cd diffSynth_studio

python examples/flux2/model_training/validate_lora/FLUX.2-klein-base-4B.py
```

**Note:**

Loss values for generative models are generally less intuitive than those of traditional classification or regression tasks. It is recommended to periodically generate and visualize validation results during training to evaluate model quality.

### 5. Submit Fine-Tuned Results

Participants should refer to and modify the inference code in `generate_images.py` to load their fine-tuned LoRA weights during image generation.

### Other Models

For fine-tuning instructions for other models, please refer to the DiffSynth-Studio documentation:

https://diffsynth-studio-doc.readthedocs.io/zh-cn/latest/

## Reference <br/>
https://github.com/modelscope/DiffSynth-Studio<br/>