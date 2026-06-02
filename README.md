# audio2text

一个可独立部署的本地音频/视频转文本服务，使用 FunASR Paraformer 中文模型和 FSMN-VAD。
视频文件会先通过 `ffmpeg` 提取音轨，再进入同一套本地 ASR 转写流程。

## 目录说明

```text
app/                 服务代码
models/              本地模型目录，GitHub 仓库只保留说明，不提交模型大文件
storage/input/       上传的原始音频或视频
storage/wav/         转码后的 16k 单声道 WAV
storage/result/      识别 JSON、断句 JSON、断句 TXT、SRT、VTT
storage/jobs/        异步任务状态 JSON
storage/logs/        服务运行日志
storage/records/     调用审计记录
scripts/             命令行工具
docs/                接口手册和服务管理方案
config.yaml          模型、存储、断句阈值、运行目录配置
```

## GitHub 大文件策略

GitHub 仓库只保存代码、配置、部署脚本和文档，不提交以下内容：

- `.venv/`：Linux/macOS 环境不可通用，且包含大量第三方依赖文件。
- `storage/` 下的运行产物：上传媒体、转码 WAV、识别结果、任务状态、日志、调用记录均为运行时数据。
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

脚本默认从 `models-v1` release 下载 `audio2text-models-v1.tar.gz`，同时下载 `.sha256`
文件进行校验，并解压出：

```text
models/paraformer-zh/
models/fsmn-vad/
```

模型包地址：

```text
https://github.com/Rok2025/audio2text/releases/download/models-v1/audio2text-models-v1.tar.gz
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
curl -F "file=@/path/to/video.mp4" "http://127.0.0.1:8000/api/transcribe?thresholdMs=600"
```

返回包含完整文本、按时间间隔切分的 `segments`，以及生成的结果文件路径。

更完整的接口说明见：[docs/API_MANUAL.md](docs/API_MANUAL.md)。

服务日志与调用记录方案见：[docs/SERVICE_MANAGEMENT_PLAN.md](docs/SERVICE_MANAGEMENT_PLAN.md)。

文档索引见：[docs/README.md](docs/README.md)。

上传部署到服务器见：[docs/UPLOAD_DEPLOYMENT.md](docs/UPLOAD_DEPLOYMENT.md)。

当前 HTTP 接口能力：

- 支持音频：`.aac`、`.flac`、`.m4a`、`.mp3`、`.ogg`、`.opus`、`.wav`
- 支持视频：`.avi`、`.m4v`、`.mkv`、`.mov`、`.mp4`、`.webm`
- 支持返回：`json`、`text`、`srt`、`vtt`
- 支持同步转写和异步任务
- 支持调用记录查询和 JSON Lines 服务日志

同步接口支持指定返回格式：

```bash
curl -F "file=@/path/to/audio.m4a" \
  "http://127.0.0.1:8000/api/transcribe?thresholdMs=600&format=json"

curl -F "file=@/path/to/video.mp4" \
  "http://127.0.0.1:8000/api/transcribe?format=srt"
```

可用格式：

- `json`：完整结构化结果，默认格式。
- `text`：只返回完整文本。
- `srt`：返回 SRT 字幕。
- `vtt`：返回 WebVTT 字幕。

也可以使用异步任务接口，适合较长音频或视频：

```bash
curl -F "file=@/path/to/audio.m4a" "http://127.0.0.1:8000/api/jobs?thresholdMs=600"
curl -F "file=@/path/to/video.mp4" "http://127.0.0.1:8000/api/jobs?thresholdMs=600"

curl "http://127.0.0.1:8000/api/jobs/{taskId}"
curl "http://127.0.0.1:8000/api/jobs/{taskId}/result"
curl "http://127.0.0.1:8000/api/jobs/{taskId}/result?format=vtt"
curl "http://127.0.0.1:8000/api/jobs/{taskId}/files/srt"
```

辅助接口：

```bash
curl http://127.0.0.1:8000/ready
curl http://127.0.0.1:8000/api/models
curl "http://127.0.0.1:8000/api/records?limit=50"
```

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
  --exclude='audio2text/storage/jobs/*' \
  --exclude='audio2text/storage/logs/*' \
  --exclude='audio2text/storage/records/*' \
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

默认配置使用基础镜像自带 Debian 源和默认 PyPI 源，适合 macOS 本地或网络通畅环境。

```bash
docker compose up -d --build
```

也可以使用项目脚本启动默认配置：

```bash
bash scripts/docker_start.sh
```

停止默认配置服务：

```bash
bash scripts/docker_stop.sh
```

中国国内 Linux 服务器建议使用国内源配置，默认启用阿里云 Debian 源和阿里云 PyPI 源：

```bash
docker compose -f docker-compose.cn.yml up -d --build
```

对应脚本：

```bash
bash scripts/docker_start_cn.sh
bash scripts/docker_stop_cn.sh
```

旧版 Docker 可使用：

```bash
docker-compose up -d --build
docker-compose -f docker-compose.cn.yml up -d --build
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
curl -F "file=@/path/to/test.mp4" "http://127.0.0.1:8000/api/jobs?thresholdMs=600"
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
