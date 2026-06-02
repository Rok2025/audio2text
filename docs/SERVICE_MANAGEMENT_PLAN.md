# audio2text 服务管理第一版方案

本方案用于把 audio2text 从“可调用工具”升级为“可运营服务”。第一版范围聚焦本地文件化管理，不引入数据库和外部日志平台。

## 1. 目标

服务需要能够回答这些问题：

- 谁在什么时候调用了服务。
- 上传的文件名、大小、媒体类型是什么。
- 使用了哪些参数。
- 调用是同步还是异步。
- 调用成功还是失败。
- 转写耗时、文本长度、分段数量是多少。
- 结果文件保存在哪里。
- 失败原因是什么。

## 2. 存储目录

新增运行目录：

```text
storage/logs/       服务运行日志
storage/records/    调用审计记录
```

配置项：

```yaml
storage:
  log_dir: ./storage/logs
  record_dir: ./storage/records
```

这些目录属于运行时数据，不提交 Git。

## 3. 服务日志

日志文件：

```text
storage/logs/app.log
```

格式：JSON Lines，一行一条。

示例：

```json
{"time":"2026-06-02T07:20:01+00:00","level":"INFO","event":"transcribe.start","message":"transcribe.start","filename":"demo.mp4","mediaType":"video"}
```

第一版记录事件：

| event | 说明 |
| --- | --- |
| `transcribe.start` | 同步转写开始 |
| `transcribe.success` | 同步转写成功 |
| `transcribe.failed` | 同步转写失败 |
| `job.queued` | 异步任务已创建 |
| `job.processing` | 异步任务开始处理 |
| `job.success` | 异步任务成功 |
| `job.failed` | 异步任务失败 |

日志只记录运行摘要和错误信息，不直接写入完整 ASR 原始结果。完整结果以文件形式保存在 `storage/result/`。

## 4. 调用记录

记录文件：

```text
storage/records/records.jsonl
```

格式：JSON Lines，一行一条调用状态记录。

记录行为：

- 同步成功：追加一条 `sync/success` 记录。
- 同步失败：追加一条 `sync/failed` 记录。
- 异步创建：追加一条 `async/queued` 记录。
- 异步成功：追加一条 `async/success` 记录。
- 异步失败：追加一条 `async/failed` 记录。

成功记录示例：

```json
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
  "files": {
    "segmentsText": "/Users/freeman/Documents/00-Project/audio2text/storage/result/xxx_segments.txt",
    "srt": "/Users/freeman/Documents/00-Project/audio2text/storage/result/xxx.srt",
    "vtt": "/Users/freeman/Documents/00-Project/audio2text/storage/result/xxx.vtt"
  },
  "error": null,
  "startedAt": "2026-06-02T07:20:01+00:00",
  "finishedAt": "2026-06-02T07:20:18+00:00",
  "elapsedMs": 17000
}
```

失败记录示例：

```json
{
  "taskId": "sync-xxx",
  "mode": "sync",
  "status": "failed",
  "filename": "bad.txt",
  "mediaType": null,
  "error": "Unsupported media suffix: .txt"
}
```

## 5. 查询接口

最近调用记录：

```text
GET /api/records?limit=50
```

说明：

- `limit` 范围是 `1-500`。
- 默认返回最近 `50` 条。
- 返回顺序是新记录在前。

按任务查询：

```text
GET /api/records/{taskId}
```

说明：

- 同步任务通常有一条记录。
- 异步任务通常有多条记录，例如 `queued` 和 `success`。
- 删除 `storage/jobs/{taskId}.json` 不会删除调用记录。

## 6. 第一版边界

第一版不做：

- 用户身份认证。
- 数据库持久化。
- 日志轮转。
- 记录删除。
- 按日期、状态、媒体类型的复杂筛选。

后续可以继续演进到：

```text
SQLite -> PostgreSQL -> 日志平台 / 监控平台
```
