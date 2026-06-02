# audio2text 变更说明

## 当前工作区版本

### 接口能力

- `POST /api/transcribe` 支持音频和视频输入。
- `POST /api/jobs` 支持音频和视频异步转写。
- `GET /api/jobs/{taskId}` 查询异步任务状态。
- `GET /api/jobs/{taskId}/result?format=json|text|srt|vtt` 获取异步任务结果。
- `GET /api/jobs/{taskId}/files/{fileType}` 下载结果文件。
- `GET /api/records?limit=50` 查询最近调用记录。
- `GET /api/records/{taskId}` 按任务 ID 查询调用记录。
- `GET /ready` 检查模型、目录、`ffmpeg`、`ffprobe`、日志目录和记录目录。
- `GET /api/models` 返回模型配置、支持格式、音频后缀和视频后缀。

### 输入与输出

- 支持音频：`.aac`、`.flac`、`.m4a`、`.mp3`、`.ogg`、`.opus`、`.wav`
- 支持视频：`.avi`、`.m4v`、`.mkv`、`.mov`、`.mp4`、`.webm`
- 输出格式：`json`、`text`、`srt`、`vtt`
- 生成文件：`rawJson`、`segmentsJson`、`segmentsText`、`srt`、`vtt`、`wav`

### 服务管理

- 服务日志写入 `storage/logs/app.log`。
- 调用记录写入 `storage/records/records.jsonl`。
- 异步任务状态写入 `storage/jobs/{taskId}.json`。
- 运行产物已加入 `.gitignore`。

### 文档

- 接口操作手册：[API_MANUAL.md](API_MANUAL.md)
- 服务管理方案：[SERVICE_MANAGEMENT_PLAN.md](SERVICE_MANAGEMENT_PLAN.md)
