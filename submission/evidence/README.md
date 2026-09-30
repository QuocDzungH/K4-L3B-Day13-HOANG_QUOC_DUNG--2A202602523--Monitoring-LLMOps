# Evidence cá nhân

Đặt ảnh hoặc output text dùng để chấm vào thư mục này. Danh sách đầy đủ xem tại [docs/SUBMISSION.md](../../docs/SUBMISSION.md).

Tên file evidence hiện có hoặc cần bổ sung:

```text
01-pytest.txt
02-log-validator.png
03-dashboard-validator.png
04-structured-log.png
05-pii-redaction.png
06-trace-list.png
07-trace-waterfall.png
08-trace-metadata.png
09-prompt-versions.png
10a-prompt-promoted.png
10b-prompt-after-rollback.png
10c-after-rollback-request.png
11-dashboard-overview.png
12-incident-metric.png
12a-cp3-baseline.png
13-incident-log.png
14-incident-trace.png
```

Có thể dùng `.txt` cho output của tests/validators. Có thể tách dashboard thành nhiều ảnh nếu một ảnh không đọc rõ.

Đã lưu evidence `01`–`14`, bao gồm `01-pytest.txt` và ảnh `12a-cp3-baseline.png`. Ảnh `02` và `05` có lệnh thử lỗi phía trên nhưng kết quả thành công vẫn đọc được. CP3 gồm baseline, metrics, log và trace.

Ảnh `04`, `05`, `13` lấy từ terminal hoặc `data/logs.jsonl`. Với ảnh `13`, lọc đúng một correlation ID challenge và giữ nguyên `latency_ms`. Ảnh `06`–`10`, `14` lấy từ project Langfuse cá nhân `day13-k4-l3b-<MSSV>` và nên nhìn thấy tên project; ảnh `14` phải hiện correlation ID trùng log và span retrieval. Không mở/chụp trang API Keys.

Từ `submission/REPORT.md`, dẫn ảnh bằng đường dẫn tương đối:

```markdown
![Trace waterfall](evidence/07-trace-waterfall.png)
```

Không commit secret, API key, PII thô hoặc evidence của học viên/lớp khác.
