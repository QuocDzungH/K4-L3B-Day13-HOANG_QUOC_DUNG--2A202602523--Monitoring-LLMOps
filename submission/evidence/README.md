# Evidence cá nhân

Bộ nộp theo [SUBMISSION.md](../../docs/SUBMISSION.md) gồm ba output text và đúng năm ảnh runtime:

```text
pytest.txt
log-validator.txt
dashboard-validator.txt
01-incident-log.png
02-trace-list.png
03-incident-trace.png
04-prompt-versioning.png
05-dashboard-incident.png
```

`01-incident-log.png` là dòng JSON `response_sent` cho request sự cố `req-062aca18`. `03-incident-trace.png` là trace cùng correlation ID, có span retrieval 2.50 giây và generation được chọn. `04-prompt-versioning.png` đặt trace generation dùng prompt v2 cạnh trang Versions sau rollback. Các ảnh theo `SCREENSHOT_GUIDE.md` cũng được giữ trong thư mục evidence.

Không commit `.env`, key, PII thô hoặc challenge khác lớp. Ảnh Langfuse phải thuộc project cá nhân.
