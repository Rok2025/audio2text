# audio2text 接口操作手册

本文档面向业务系统调用方，说明如何启动服务、检查状态、上传音频或视频、获取转写结果和下载导出文件。

## 1. 服务地址

本地默认地址：

```text
http://127.0.0.1:8000
```

启动服务：

```bash
bash scripts/run_server.sh
```

接口文档页面：

```text
http://127.0.0.1:8000/docs
```

## 2. 快速调用

同步转写一个媒体文件：

```bash
curl -F "file=@/Users/freeman/Downloads/Jingsan Road.m4a" \
  "http://127.0.0.1:8000/api/transcribe?thresholdMs=600&format=json"
```

只返回纯文本：

```bash
curl -F "file=@/Users/freeman/Downloads/Jingsan Road.m4a" \
  "http://127.0.0.1:8000/api/transcribe?format=text"
```

返回 SRT 字幕：

```bash
curl -F "file=@/Users/freeman/Downloads/Jingsan Road.m4a" \
  "http://127.0.0.1:8000/api/transcribe?format=srt"
```

视频文件也使用同一个接口：

```bash
curl -F "file=@/Users/freeman/Downloads/demo.mp4" \
  "http://127.0.0.1:8000/api/transcribe?format=srt"
```

## 3. 接口清单

| 接口 | 方法 | 用途 |
| --- | --- | --- |
| `/` | GET | 查看服务入口信息 |
| `/health` | GET | 检查服务进程是否存活 |
| `/ready` | GET | 检查模型、目录、ffmpeg 是否可用 |
| `/api/models` | GET | 查看当前模型配置和支持格式 |
| `/api/transcribe` | POST | 同步上传音频或视频并返回转写结果 |
| `/api/jobs` | POST | 创建异步转写任务 |
| `/api/jobs/{taskId}` | GET | 查询任务状态 |
| `/api/jobs/{taskId}/result` | GET | 获取任务结果 |
| `/api/jobs/{taskId}/files/{fileType}` | GET | 下载任务生成文件 |
| `/api/jobs/{taskId}` | DELETE | 删除任务状态 JSON |
| `/api/records` | GET | 查询最近调用记录 |
| `/api/records/{taskId}` | GET | 按任务 ID 查询调用记录 |

## 4. 服务检查接口

### 4.1 存活检查

```bash
curl http://127.0.0.1:8000/health
```

正常返回：

```json
{
  "status": "ok"
}
```

### 4.2 就绪检查

```bash
curl http://127.0.0.1:8000/ready
```

正常返回：

```json
{
  "status": "ok",
  "checks": {
    "modelPath": true,
    "vadModelPath": true,
    "inputDir": true,
    "wavDir": true,
    "resultDir": true,
    "jobDir": true,
    "logDir": true,
    "recordDir": true,
    "ffmpeg": true,
    "ffprobe": true
  }
}
```

如果 `status` 是 `not_ready`，说明至少有一个依赖不可用。

### 4.3 模型配置

```bash
curl http://127.0.0.1:8000/api/models
```

返回示例：

```json
{
  "asr": {
    "model": "/Users/freeman/Documents/00-Project/audio2text/models/paraformer-zh",
    "vadModel": "/Users/freeman/Documents/00-Project/audio2text/models/fsmn-vad",
    "device": "cpu",
    "batchSizeS": 60,
    "gapThresholdMs": 600
  },
  "formats": ["json", "text", "srt", "vtt"],
  "allowedAudioSuffixes": [".aac", ".flac", ".m4a", ".mp3", ".ogg", ".opus", ".wav"],
  "allowedVideoSuffixes": [".avi", ".m4v", ".mkv", ".mov", ".mp4", ".webm"],
  "allowedSuffixes": [".aac", ".avi", ".flac", ".m4a", ".m4v", ".mkv", ".mov", ".mp3", ".mp4", ".ogg", ".opus", ".wav", ".webm"]
}
```

## 5. 同步转写接口

### 5.1 请求

```text
POST /api/transcribe
Content-Type: multipart/form-data
```

表单参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `file` | file | 是 | 音频或视频文件 |

Query 参数：

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `thresholdMs` | integer | `600` | 按停顿断句的阈值，范围 `100-5000` 毫秒 |
| `format` | string | `json` | 返回格式：`json`、`text`、`srt`、`vtt` |
| `returnRaw` | boolean | `false` | 是否在 JSON 中返回 FunASR 原始结果 |

支持的音频扩展名：

```text
.aac, .flac, .m4a, .mp3, .ogg, .opus, .wav
```

支持的视频扩展名：

```text
.avi, .m4v, .mkv, .mov, .mp4, .webm
```

视频文件会先通过 `ffmpeg` 提取音轨，再进入同一套 ASR 转写流程。

### 5.2 JSON 返回示例

```bash
curl -F "file=@/path/to/audio.m4a" \
  "http://127.0.0.1:8000/api/transcribe?thresholdMs=600&format=json"
```

返回：

```json
{
  "taskId": "155ad7c8596041c9bb84dca7deb5f254",
  "status": "success",
  "source": {
    "filename": "audio.m4a",
    "path": "/Users/freeman/Documents/00-Project/audio2text/storage/input/xxx_audio.m4a",
    "mediaType": "audio",
    "durationMs": 25685
  },
  "text": "这是一个测试的一个文文字录音...",
  "segments": [
    {
      "index": 1,
      "startMs": 550,
      "endMs": 3335,
      "start": "00:00.550",
      "end": "00:03.335",
      "text": "这是一个测试的一个文",
      "gapBeforeMs": 0
    }
  ],
  "files": {
    "wav": "/Users/freeman/Documents/00-Project/audio2text/storage/wav/xxx.wav",
    "rawJson": "/Users/freeman/Documents/00-Project/audio2text/storage/result/xxx.json",
    "segmentsJson": "/Users/freeman/Documents/00-Project/audio2text/storage/result/xxx_segments.json",
    "segmentsText": "/Users/freeman/Documents/00-Project/audio2text/storage/result/xxx_segments.txt",
    "srt": "/Users/freeman/Documents/00-Project/audio2text/storage/result/xxx.srt",
    "vtt": "/Users/freeman/Documents/00-Project/audio2text/storage/result/xxx.vtt"
  },
  "meta": {
    "model": "/Users/freeman/Documents/00-Project/audio2text/models/paraformer-zh",
    "vadModel": "/Users/freeman/Documents/00-Project/audio2text/models/fsmn-vad",
    "thresholdMs": 600,
    "device": "cpu"
  }
}
```

### 5.3 返回纯文本

```bash
curl -F "file=@/path/to/audio.m4a" \
  "http://127.0.0.1:8000/api/transcribe?format=text"
```

返回：

```text
这是一个测试的一个文文字录音又用于将来识别识别文字...
```

### 5.4 返回 SRT 字幕

```bash
curl -F "file=@/path/to/audio.m4a" \
  "http://127.0.0.1:8000/api/transcribe?format=srt"
```

返回：

```srt
1
00:00,550 --> 00:03,335
这是一个测试的一个文

2
00:04,740 --> 00:05,655
文字录音
```

### 5.5 返回 WebVTT 字幕

```bash
curl -F "file=@/path/to/audio.m4a" \
  "http://127.0.0.1:8000/api/transcribe?format=vtt"
```

返回：

```vtt
WEBVTT

00:00.550 --> 00:03.335
这是一个测试的一个文

00:04.740 --> 00:05.655
文字录音
```

## 6. 异步任务接口

异步接口适合较长音频或视频，避免 HTTP 请求等待时间过长。

### 6.1 创建任务

```bash
curl -F "file=@/path/to/audio.m4a" \
  "http://127.0.0.1:8000/api/jobs?thresholdMs=600"
```

上传视频：

```bash
curl -F "file=@/path/to/video.mp4" \
  "http://127.0.0.1:8000/api/jobs?thresholdMs=600"
```

返回：

```json
{
  "taskId": "dc3d4a8ae10b45bab289475a2f5fbbc1",
  "status": "queued",
  "statusUrl": "/api/jobs/dc3d4a8ae10b45bab289475a2f5fbbc1",
  "resultUrl": "/api/jobs/dc3d4a8ae10b45bab289475a2f5fbbc1/result"
}
```

### 6.2 查询任务状态

```bash
curl http://127.0.0.1:8000/api/jobs/dc3d4a8ae10b45bab289475a2f5fbbc1
```

可能的状态：

| 状态 | 说明 |
| --- | --- |
| `queued` | 已创建，等待处理 |
| `processing` | 正在转写 |
| `success` | 已完成 |
| `failed` | 失败 |

完成时返回示例：

```json
{
  "taskId": "dc3d4a8ae10b45bab289475a2f5fbbc1",
  "status": "success",
  "source": {
    "filename": "audio.m4a",
    "path": "/Users/freeman/Documents/00-Project/audio2text/storage/input/xxx_audio.m4a",
    "mediaType": "audio",
    "fileSizeBytes": 216456
  },
  "request": {
    "thresholdMs": 600,
    "returnRaw": false,
    "startedAt": "2026-06-02T07:50:22.427853+00:00"
  },
  "resultUrl": "/api/jobs/dc3d4a8ae10b45bab289475a2f5fbbc1/result",
  "files": {
    "segmentsText": "/Users/freeman/Documents/00-Project/audio2text/storage/result/xxx_segments.txt",
    "srt": "/Users/freeman/Documents/00-Project/audio2text/storage/result/xxx.srt",
    "vtt": "/Users/freeman/Documents/00-Project/audio2text/storage/result/xxx.vtt"
  }
}
```

### 6.3 获取任务结果

JSON 结果：

```bash
curl "http://127.0.0.1:8000/api/jobs/{taskId}/result"
```

纯文本：

```bash
curl "http://127.0.0.1:8000/api/jobs/{taskId}/result?format=text"
```

SRT 字幕：

```bash
curl "http://127.0.0.1:8000/api/jobs/{taskId}/result?format=srt"
```

WebVTT 字幕：

```bash
curl "http://127.0.0.1:8000/api/jobs/{taskId}/result?format=vtt"
```

### 6.4 下载生成文件

```bash
curl -O "http://127.0.0.1:8000/api/jobs/{taskId}/files/txt"
curl -O "http://127.0.0.1:8000/api/jobs/{taskId}/files/srt"
curl -O "http://127.0.0.1:8000/api/jobs/{taskId}/files/vtt"
curl -O "http://127.0.0.1:8000/api/jobs/{taskId}/files/wav"
```

可用的 `fileType`：

| fileType | 说明 |
| --- | --- |
| `raw-json` | FunASR 原始 JSON |
| `segments-json` | 断句后的 JSON |
| `txt` | 断句文本 |
| `text` | 同 `txt` |
| `srt` | SRT 字幕 |
| `vtt` | WebVTT 字幕 |
| `wav` | 转码后的 16k 单声道 WAV |

### 6.5 删除任务状态

```bash
curl -X DELETE "http://127.0.0.1:8000/api/jobs/{taskId}"
```

返回：

```json
{
  "taskId": "dc3d4a8ae10b45bab289475a2f5fbbc1",
  "deleted": true
}
```

注意：此接口只删除任务状态 JSON，不删除已经生成的音频、视频、结果文件和调用记录。

## 7. 参数建议

### 7.1 thresholdMs

`thresholdMs` 决定根据多长的停顿切分句子。

| 值 | 效果 |
| --- | --- |
| `300-500` | 切得更碎，适合逐句字幕 |
| `600` | 默认值，适合一般语音转写 |
| `800-1200` | 切得更长，适合会议纪要或段落文本 |

### 7.2 format

| format | 适用场景 |
| --- | --- |
| `json` | 业务系统结构化接入 |
| `text` | 只需要完整文本 |
| `srt` | 视频字幕、剪辑软件 |
| `vtt` | 网页播放器字幕 |

### 7.3 returnRaw

默认不返回 FunASR 原始结果：

```text
returnRaw=false
```

调试模型输出时可以开启：

```text
returnRaw=true
```

开启后 JSON 会更大，不建议业务常规调用开启。

## 8. 调用记录接口

服务会把同步和异步调用记录追加到：

```text
storage/records/records.jsonl
```

运行日志写入：

```text
storage/logs/app.log
```

查询最近调用：

```bash
curl "http://127.0.0.1:8000/api/records?limit=50"
```

`limit` 范围是 `1-500`，默认 `50`。返回按新到旧排序。

返回：

```json
{
  "records": [
    {
      "taskId": "155ad7c8596041c9bb84dca7deb5f254",
      "mode": "sync",
      "status": "success",
      "filename": "demo.mp4",
      "mediaType": "video",
      "fileSizeBytes": 262144,
      "durationMs": 28760,
      "thresholdMs": 600,
      "format": "json",
      "returnRaw": false,
      "textLength": 58,
      "segmentCount": 7,
      "error": null,
      "elapsedMs": 17000
    }
  ],
  "limit": 50,
  "count": 1
}
```

按任务查询：

```bash
curl "http://127.0.0.1:8000/api/records/{taskId}"
```

异步任务通常会返回多条记录，例如 `queued` 和 `success`。同步调用通常返回一条 `success` 或 `failed` 记录。

运行日志为 JSON Lines，常见事件：

| event | 说明 |
| --- | --- |
| `transcribe.start` | 同步转写开始 |
| `transcribe.success` | 同步转写成功 |
| `transcribe.failed` | 同步转写失败 |
| `job.queued` | 异步任务已创建 |
| `job.processing` | 异步任务开始处理 |
| `job.success` | 异步任务成功 |
| `job.failed` | 异步任务失败 |

## 9. 常见错误

| HTTP 状态码 | 场景 | 处理方式 |
| --- | --- | --- |
| `400` | 上传文件扩展名不支持 | 检查音频格式 |
| `413` | 上传文件超过大小限制 | 压缩音频或改服务端限制 |
| `422` | 参数不合法 | 检查 `thresholdMs`、`format` |
| `409` | 异步任务尚未完成 | 继续查询任务状态 |
| `404` | 任务或文件不存在 | 检查 `taskId` 和 `fileType` |
| `500` | 服务端异常 | 查看服务日志、模型路径、ffmpeg |
| `500` | 视频没有音轨 | 换一个包含音轨的视频或先单独提供音频 |

## 10. 结果文件目录

默认运行产物目录：

```text
storage/input/    上传的原始音频或视频
storage/wav/      转码后的 WAV
storage/result/   JSON、TXT、SRT、VTT 结果
storage/jobs/     异步任务状态 JSON
storage/logs/     服务运行日志
storage/records/  调用审计记录
```

这些目录属于运行时数据，不建议提交到 Git。

## 11. 推荐接入流程

短音频、短视频或内部工具：

```text
POST /api/transcribe -> 直接拿 JSON/text/srt/vtt
```

长音频、长视频或生产业务：

```text
POST /api/jobs
GET /api/jobs/{taskId}
GET /api/jobs/{taskId}/result
GET /api/jobs/{taskId}/files/{fileType}
```

生产环境建议先调用 `/ready`，确认依赖可用后再接收业务请求。
