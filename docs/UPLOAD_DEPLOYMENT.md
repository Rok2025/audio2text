# audio2text 上传部署手册

本文档说明如何通过“本地打包上传”的方式，把 audio2text 部署到服务器。

## 1. 本地打包项目

在本机执行：

```bash
cd /Users/freeman/Documents/00-Project

COPYFILE_DISABLE=1 tar \
  --exclude='audio2text/.git' \
  --exclude='audio2text/.venv' \
  --exclude='audio2text/__pycache__' \
  --exclude='audio2text/app/__pycache__' \
  --exclude='audio2text/scripts/__pycache__' \
  --exclude='audio2text/tests/__pycache__' \
  --exclude='audio2text/storage/input/*' \
  --exclude='audio2text/storage/wav/*' \
  --exclude='audio2text/storage/result/*' \
  --exclude='audio2text/storage/jobs/*' \
  --exclude='audio2text/storage/logs/*' \
  --exclude='audio2text/storage/records/*' \
  --exclude='audio2text/models/paraformer-zh' \
  --exclude='audio2text/models/fsmn-vad' \
  -czf audio2text-deploy.tar.gz audio2text
```

这个包不包含：

- Git 仓库目录。
- 本机虚拟环境 `.venv`。
- 运行时上传文件和识别结果。
- 模型大文件。

## 2. 上传到服务器

把 `服务器IP` 换成你的服务器地址：

```bash
scp /Users/freeman/Documents/00-Project/audio2text-deploy.tar.gz root@服务器IP:/opt/
```

## 3. 服务器解压

登录服务器：

```bash
ssh root@服务器IP
```

解压：

```bash
cd /opt
rm -rf audio2text
tar -xzf audio2text-deploy.tar.gz
cd /opt/audio2text
```

## 4. 准备模型

### 方式一：服务器下载模型

如果服务器能访问 GitHub Release：

```bash
cd /opt/audio2text
bash scripts/download_models.sh
```

### 方式二：本地上传模型

如果服务器访问 GitHub 慢，建议本地单独打包模型并上传。

本地执行：

```bash
cd /Users/freeman/Documents/00-Project/audio2text
COPYFILE_DISABLE=1 tar -czf audio2text-models.tar.gz models/paraformer-zh models/fsmn-vad
scp audio2text-models.tar.gz root@服务器IP:/opt/audio2text/
```

服务器执行：

```bash
cd /opt/audio2text
tar -xzf audio2text-models.tar.gz
```

确认模型目录存在：

```bash
ls -la models/paraformer-zh
ls -la models/fsmn-vad
```

## 5. Docker 启动服务

服务器执行：

```bash
cd /opt/audio2text
bash scripts/docker_start_cn.sh
```

`docker_start_cn.sh` 会使用 `Dockerfile.cn` 和 `docker-compose.cn.yml`，默认启用阿里云 Debian 源和阿里云 PyPI 源，适合中国国内 Linux 服务器。

如果服务器网络可以稳定访问 Docker Hub、Debian 源和 PyPI，也可以使用默认脚本：

```bash
bash scripts/docker_start.sh
```

如果不使用脚本，国内服务器可以执行：

```bash
docker-compose -f docker-compose.cn.yml up -d --build
```

或 Docker Compose v2：

```bash
docker compose -f docker-compose.cn.yml up -d --build
```

## 6. 检查服务

```bash
docker ps
docker logs --tail=100 audio2text
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ready
```

正常情况下：

```json
{"status":"ok"}
```

## 7. 测试转写

服务器上有测试音频时：

```bash
curl -F "file=@/path/to/test.m4a" \
  "http://127.0.0.1:8000/api/transcribe?thresholdMs=600&format=json"
```

测试视频异步转写：

```bash
curl -F "file=@/path/to/test.mp4" \
  "http://127.0.0.1:8000/api/jobs?thresholdMs=600"
```

## 8. 后续更新代码

以后更新代码时，重复本地打包和上传即可。

本地：

```bash
cd /Users/freeman/Documents/00-Project

COPYFILE_DISABLE=1 tar \
  --exclude='audio2text/.git' \
  --exclude='audio2text/.venv' \
  --exclude='audio2text/storage/input/*' \
  --exclude='audio2text/storage/wav/*' \
  --exclude='audio2text/storage/result/*' \
  --exclude='audio2text/storage/jobs/*' \
  --exclude='audio2text/storage/logs/*' \
  --exclude='audio2text/storage/records/*' \
  --exclude='audio2text/models/paraformer-zh' \
  --exclude='audio2text/models/fsmn-vad' \
  -czf audio2text-deploy.tar.gz audio2text

scp /Users/freeman/Documents/00-Project/audio2text-deploy.tar.gz root@服务器IP:/opt/
```

服务器：

```bash
cd /opt
tar -xzf audio2text-deploy.tar.gz
cd /opt/audio2text
bash scripts/docker_start_cn.sh
```

模型不用每次重新上传，只要 `/opt/audio2text/models` 还在即可。
