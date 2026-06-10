# Baseline

[简体中文](README.md) | English

Baseline pending development.

Baseline Usage:
```bash
```



## Challenge Specifications<br/>
## Contest Rules
1) The platform accepts submissions via container image links. Push your local container image to either Alibaba Cloud Container Registry (ACR) or Docker Hub and set the image to public visibility, then enter the image URL on the competition submission page. The platform will pull and run the submitted image automatically; once the execution finishes, evaluation results can be checked on the score page. When uploading images to Alibaba Cloud Container Registry or Docker Hub, refrain from using any competition-related terms in the repository name to avoid information leakage from public search indexing. <br/>
2) No network access is available within the container when running the image. Install all dependent software and packages in the image.<br/>
3) For rational resource allocation, the average processing time for a single dataset shall not exceed 30 seconds. Programs running beyond this time threshold will be forcibly terminated, and their corresponding outputs will be rejected. <br/>
<br/>



## Computation Resources<br/>
CPU: 16 cores <br/>
Memory: 64GB <br/>
GPU: 24GB (NVIDIA GeForce RTX 4090)<br/>
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

## Reference <br/>
<br/>