# audio2text

一个可独立部署的本地音频转文本服务，使用 FunASR Paraformer 中文模型和 FSMN-VAD。

## 目录说明

```text
app/                 服务代码
models/              本地模型目录，GitHub 仓库只保留说明，不提交模型大文件
storage/input/       上传的原始音频
storage/wav/         转码后的 16k 单声道 WAV
storage/result/      识别 JSON、断句 JSON、断句 TXT
scripts/             命令行工具
config.yaml          模型、存储、断句阈值配置
```

## GitHub 大文件策略

GitHub 仓库只保存代码、配置、部署脚本和文档，不提交以下内容：

- `.venv/`：Linux/macOS 环境不可通用，且包含大量第三方依赖文件。
- `storage/` 下的运行产物：上传音频、转码 WAV、识别结果均为运行时数据。
- `models/` 下的模型大文件：例如 `models/paraformer-zh/model.pt` 约 944 MB。

模型交付建议单独处理：

- 私有化交付包：将 `models/` 单独打成 `audio2text-models.tar.gz`。
- 对象存储或内网文件服务：部署时下载到 `./models`。
- GitHub Release Asset：适合随版本发布固定模型包。
- Git LFS：可用，但需要管理 LFS 存储和流量配额，不建议作为默认方案。

从 GitHub 克隆后，需要先把模型文件复制或挂载到 `./models`，再启动服务。

最省事的方式是使用本仓库的 GitHub Release 模型包：

```bash
git clone https://github.com/Rok2025/audio2text.git
cd audio2text
bash scripts/download_models.sh
docker compose up -d --build
```

脚本默认从 `models-v1` release 下载 `audio2text-models-v1.tar.gz`，并解压出：

```text
models/paraformer-zh/
models/fsmn-vad/
```

如果需要改成内网模型地址，可覆盖环境变量：

```bash
AUDIO2TEXT_MODEL_URL="http://内网文件服务器/audio2text-models-v1.tar.gz" \
  bash scripts/download_models.sh
```

## 本地安装

建议使用 Python 3.11。不要直接依赖系统里的 `python` 命令，先初始化本项目自己的 `.venv`：

```bash
cd /Users/freeman/Documents/00-Project/audio2text
bash scripts/setup_env.sh
```

这个脚本会优先使用 `uv` 创建 Python 3.11 虚拟环境，并安装 `PyYAML`、`FunASR`、`FastAPI` 等依赖。

服务器需要安装 `ffmpeg`。Docker 部署时镜像内会安装。

## 命令行识别

```bash
bash scripts/run_cli.sh /path/to/audio.m4a
```

可调整停顿断句阈值：

```bash
bash scripts/run_cli.sh /path/to/audio.m4a --threshold-ms 800
```

## HTTP 服务

启动：

```bash
bash scripts/run_server.sh
```

调用：

```bash
curl -F "file=@/path/to/audio.m4a" "http://127.0.0.1:8000/api/transcribe?thresholdMs=600"
```

返回包含完整文本、按时间间隔切分的 `segments`，以及生成的结果文件路径。

## Docker 部署

### 1. 从 macOS 打包交付目录

在本机打包时，不要把 macOS 的 `.venv` 和运行过程生成的临时音频一起带到服务器：

```bash
cd /Users/freeman/Documents/00-Project
COPYFILE_DISABLE=1 tar \
  --exclude='audio2text/.venv' \
  --exclude='audio2text/storage/input/*' \
  --exclude='audio2text/storage/wav/*' \
  --exclude='audio2text/storage/result/*' \
  -czf audio2text.tar.gz audio2text
```

`COPYFILE_DISABLE=1` 用于减少 macOS 扩展属性写入压缩包。如果服务器解压时仍看到类似
`LIBARCHIVE.xattr.com.apple.provenance`、`SCHILY.fflags` 的提示，一般只是 Linux `tar`
忽略 macOS 扩展属性，不影响文件解压。

### 2. 上传并解压到 Linux 服务器

```bash
scp audio2text.tar.gz root@服务器IP:/opt/

ssh root@服务器IP
cd /opt
tar -xzf audio2text.tar.gz
cd /opt/audio2text
```

如果执行 `docker compose up -d --build` 时提示 `no configuration file provided: not found`，
说明当前目录没有 `docker-compose.yml`。先确认目录：

```bash
ls -la
find /opt -name docker-compose.yml
```

进入包含 `Dockerfile` 和 `docker-compose.yml` 的目录后再启动。

### 3. 构建并启动服务

```bash
docker compose up -d --build
```

旧版 Docker 可使用：

```bash
docker-compose up -d --build
```

### 4. 检查服务

```bash
docker ps
docker logs -f audio2text
curl http://127.0.0.1:8000/health
```

正常返回：

```json
{"status":"ok"}
```

### 5. 测试识别接口

```bash
curl -F "file=@/path/to/test.m4a" "http://127.0.0.1:8000/api/transcribe?thresholdMs=600"
```

私有化交付时复制整个 `audio2text` 文件夹到服务器即可。不要复制 macOS 的 `.venv` 到 Linux；
在服务器上用 Docker 构建，或者重新创建虚拟环境安装依赖。

业务系统与本服务在同一台服务器时，服务地址通常配置为 `http://127.0.0.1:8000`。
业务系统与本服务在同一个 Docker 网络时，服务地址可配置为 `http://audio2text:8000`。
独立 ASR 服务器部署时，服务地址配置为 `http://ASR服务器内网IP:8000`。

## 模型路径

模型路径在 `config.yaml` 中配置：

```yaml
asr:
  model_path: ./models/paraformer-zh
  vad_model_path: ./models/fsmn-vad
```

生产环境建议保持 `disable_update=True`，服务启动和识别时只读取本地模型，不依赖外网下载。
