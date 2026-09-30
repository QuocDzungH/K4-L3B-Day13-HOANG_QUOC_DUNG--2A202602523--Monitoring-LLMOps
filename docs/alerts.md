# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert mẫu để tham khảo

Ví dụ dưới đây minh họa mức độ cụ thể cần có. Học viên không cần copy nguyên, nhưng ba alert trong bài nộp nên rõ ràng tương tự: điều kiện là gì, kéo dài bao lâu, ảnh hưởng tới user ra sao và người trực cần kiểm tra gì trước.

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh các span chính để xác định bước nào bất thường.
- Mitigation tạm thời: dựa trên evidence thực tế để rollback prompt, khôi phục cấu hình liên quan, tắt practice scenario hoặc giảm tải khi demo.
- Owner: `student-<MSSV>`

## Alert 1

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: request thành công trong tối đa 3000 ms.
- Điều kiện và thời gian duy trì: P95 của `response_sent.latency_ms` > 3000 ms trong 5 phút.
- Ảnh hưởng tới người dùng: câu trả lời đến chậm.
- Ba bước kiểm tra đầu tiên:
  1. Xem panel Latency, ghi thời điểm P95 vượt 3000 ms và đối chiếu P99, TTFT.
  2. Lọc log `response_sent` chậm trong khoảng đó, lấy `correlation_id`.
  3. Mở trace cùng ID, so sánh thời gian retrieval và generation.
- Mitigation tạm thời: rollback prompt nếu trace cho thấy version mới làm tăng token/latency; nếu retrieval chậm, khôi phục cấu hình retrieval hoặc giảm tải.
- Owner: `student-on-call`

## Alert 2

- Tên: `HighErrorRate`
- Severity: `critical`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: tỉ lệ request thành công của primary SLO.
- Điều kiện và thời gian duy trì: `request_failed / request_received * 100` > 2% trong 5 phút.
- Ảnh hưởng tới người dùng: request trả lỗi thay vì câu trả lời.
- Ba bước kiểm tra đầu tiên:
  1. Xem panel Errors, xác nhận error rate và loại lỗi tăng.
  2. Lọc `request_failed` theo `error_type`, lấy một `correlation_id` đại diện.
  3. Mở trace cùng ID, tìm span lỗi đầu tiên và kiểm tra thời điểm phát sinh.
- Mitigation tạm thời: tắt practice incident nếu đang bật; khôi phục dependency/cấu hình bị lỗi sau khi xác nhận nguyên nhân.
- Owner: `student-on-call`

## Alert 3

- Tên: `LowRetrievalSuccess`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: retrieval success guardrail ≥90%.
- Điều kiện và thời gian duy trì: `tool_success == true / tool_success != null * 100` < 90% trong 5 phút, tính cả `response_sent` và `request_failed`.
- Ảnh hưởng tới người dùng: câu hỏi cần context có thể lỗi hoặc trả lời kém tin cậy.
- Ba bước kiểm tra đầu tiên:
  1. Xem panel Errors và tỉ lệ retrieval success trong khoảng 5 phút.
  2. Lọc log có `tool_success=false`, lấy `correlation_id` và `error_type`.
  3. Mở trace cùng ID, kiểm tra observation retrieval và bước generation kế tiếp.
- Mitigation tạm thời: khôi phục retrieval/vector store hoặc cấu hình liên quan; tạm giảm tải nếu timeout tăng.
- Owner: `student-on-call`
