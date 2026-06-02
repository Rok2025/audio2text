# audio2text 文档索引

## 接口使用

- [API_MANUAL.md](API_MANUAL.md)：接口操作手册，包含同步转写、异步任务、文件下载、调用记录查询和常见错误。

## 服务管理

- [SERVICE_MANAGEMENT_PLAN.md](SERVICE_MANAGEMENT_PLAN.md)：服务日志、调用记录、运行目录和第一版管理范围。
- [UPLOAD_DEPLOYMENT.md](UPLOAD_DEPLOYMENT.md)：通过本地打包上传的方式部署到服务器。

## 变更说明

- [CHANGELOG.md](CHANGELOG.md)：当前工作区接口能力、输入输出、服务管理和文档变更摘要。

## 快速入口

启动服务：

```bash
bash scripts/run_server.sh
```

Docker 启动：

```bash
bash scripts/docker_start.sh
```

国内 Linux 服务器 Docker 启动：

```bash
bash scripts/docker_start_cn.sh
```

检查服务：

```bash
curl http://127.0.0.1:8000/ready
```

同步转写：

```bash
curl -F "file=@/path/to/audio.m4a" \
  "http://127.0.0.1:8000/api/transcribe?thresholdMs=600&format=json"
```

异步转写：

```bash
curl -F "file=@/path/to/video.mp4" \
  "http://127.0.0.1:8000/api/jobs?thresholdMs=600"
```

查询调用记录：

```bash
curl "http://127.0.0.1:8000/api/records?limit=50"
```
