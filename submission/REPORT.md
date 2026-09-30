# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Evidence được dẫn bằng link tương đối để mở trực tiếp trên GitHub.

## 1. Thông tin học viên

- **Họ và tên:** Hoàng Quốc Dũng
- **MSSV:** 2A202602523
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/QuocDzungH/K4-L3B-Day13-HOANG_QUOC_DUNG--2A202602523--Monitoring-LLMOps
- **Commit SHA cuối:** Nộp SHA chính xác trên LMS/Codelabs sau khi push; [xem commit mới nhất của nhánh main](https://github.com/QuocDzungH/K4-L3B-Day13-HOANG_QUOC_DUNG--2A202602523--Monitoring-LLMOps/commits/main).
- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân đang dùng:** `day13-k4-l3b-02523`.

## 2. Evidence index

Theo [hướng dẫn nộp](../docs/SUBMISSION.md), bộ chính thức gồm ba output text và năm ảnh runtime. Các ảnh mang tên theo `SCREENSHOT_GUIDE.md` cũng được giữ trong `submission/evidence/`; bảng dưới dẫn đến bộ năm ảnh chính thức.

| Evidence | Đường dẫn | Trạng thái |
|---|---|---|
| Pytest cuối | [pytest.txt](evidence/pytest.txt) | 28 passed; chạy với `--basetemp` trong workspace để tránh lỗi quyền dọn temp của Windows. |
| Log validator | [log-validator.txt](evidence/log-validator.txt) | 100/100; 33 records, 17 correlation ID, 0 PII leak. |
| Dashboard validator | [dashboard-validator.txt](evidence/dashboard-validator.txt) | HỢP LỆ: 6/6 panel. |
| 01 — Incident log | [01-incident-log.png](evidence/01-incident-log.png) | Dòng JSON `response_sent` cho `req-062aca18`; có event, correlation ID, model/env/feature và latency 2,653 ms. |
| 02 — Trace list | [02-trace-list.png](evidence/02-trace-list.png) | Bản sao nguyên gốc từ ảnh trace list; project cá nhân và số lượng trace nhìn thấy. |
| 03 — Incident trace | [03-incident-trace.png](evidence/03-incident-trace.png) | Trace cùng `req-062aca18` với ảnh 01; thấy trace ID, retrieval 2.50 s, generation, prompt `day13-chat` v1, model, token và cost. |
| 04 — Prompt versioning | [04-prompt-versioning.png](evidence/04-prompt-versioning.png) | Ảnh desktop hiển thị trace generation dùng `day13-chat` v2 cạnh trang Versions sau rollback: v1 `production`/`baseline`, v2 `candidate`/`latest`. |
| 05 — Dashboard incident | [05-dashboard-incident.png](evidence/05-dashboard-incident.png) | Bản sao nguyên gốc dashboard 6 panel sau challenge; P95 2,654.6 ms. |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 | CP1: 65 records, 24 correlation ID; lần chạy cuối: 33 records, 17 correlation ID; cả hai lần đều 0 thiếu field/context và 0 PII leak. |
| `validate_dashboard.py` | — | 6/6 | Kết quả lần chạy cuối; dashboard contract hợp lệ. |
| `pytest` | — | 28 passed | Lần chạy cuối: 28 passed trong 3.24 s. |
| Root traces hiển thị trong project | — | 34 | Langfuse hiển thị 34 `lab-agent-run`; workload riêng có ít nhất 10 traces. |
| PII leak trong log | — | 0 | Theo kết quả `validate_logs.py`. |
| Latency P95 / TTFT P95 | — | 661.2 ms / 50.55 ms | Đọc từ dashboard local, cửa sổ 60 phút. |
| Retrieval success rate | — | 100% | Đọc từ dashboard local, cửa sổ 60 phút. |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Middleware nhận `x-request-id` đúng dạng `req-` + 8 ký tự hex hoặc sinh ID mới, bind vào context, truyền sang agent và trả lại trong body/header của response.
- **Các metadata được ghi vào structured log:** `user_id_hash`, `session_id`, `feature`, `model`, `env` cùng `correlation_id`, thời gian, token, cost và quality khi có response.
- **Cách bảo đảm PII được scrub trước khi ghi:** `scrub_event` xử lý giá trị chuỗi kể cả dữ liệu lồng nhau trước `JsonlFileProcessor`; ID người dùng được hash.
- **Kết quả kiểm chứng:** Lần chạy cuối của `validate_logs.py` đạt 100/100: 33 records, 0 thiếu field, 0 thiếu context, 17 correlation ID duy nhất, 0 PII leak. Evidence CP1 trước đó ghi 65 records và 24 correlation ID. Load test trả HTTP 200 và response có correlation ID dạng `req-xxxxxxxx`.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Chạy `scripts/load_test.py` và request `/chat`; project Langfuse đang dùng hiển thị 34 root `lab-agent-run`, trong đó có workload 10 request của tôi.
- **Cấu trúc root/retrieval/generation observations:** `day13-agent-request` → `lab-agent-run` → `retrieval` và `generation`; generation ghi model, token input/output và cost, không capture raw prompt/output.
- **Cách nối trace với log:** Tìm `correlation_id` trong log rồi lọc trace metadata theo cùng ID.
- **Prompt name:** `day13-chat`.
- **Version/label baseline:** `day13-chat` v1, labels `baseline` và `production`.
- **Version/label candidate:** v2 thêm `Answer concisely.`, labels `candidate` và `latest`; đã promote `production` sang v2.
- **Trace ID của mỗi version:** v1: `c4f59d7c4090c72c571d536895fa06e9` (correlation ID `req-e40b5784`); v2: `9f066ccae58bee2fc0fab3590b2c1201` (correlation ID `req-ad9f2c3c`).
- **Cách promote và rollback `production`:** UI lúc promote hiển thị v2 mang `production`; sau đó chuyển `production` về v1. Sau rollback, v1 có `production` + `baseline`, v2 giữ `candidate` + `latest`. Request kiểm chứng sau rollback trả câu trả lời, `tokens_in=35`, correlation ID `req-10c30881`; Linked Generations của v1 tăng lên 12.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Dashboard local tại `/dashboard` đọc `data/logs.jsonl` trong 60 phút gần nhất, refresh 30 giây; gồm latency (P50/P95/P99, TTFT), traffic, errors/retrieval success, cost, tokens và quality. Ảnh runtime đã xem: 10 requests; P50 154 ms, P95 661.2 ms, P99 965.04 ms, TTFT P95 50.55 ms; error 0%, retrieval 100%, cost $0.021009, quality mean 0.88.
- **SLO và lý do chọn:** 99,5% request có `response_sent` trong tối đa 3000 ms trên cửa sổ 28 ngày; ngưỡng cao hơn latency P95 baseline và giúp phát hiện suy giảm rõ rệt. Contract: [config/slo.yaml](../config/slo.yaml).
- **Cách tính error budget:** 100% - 99,5% = 0,5%; với 10.000 request trong 28 ngày, tối đa 50 request được phép lỗi hoặc chậm hơn 3000 ms.
- **Ba alert và runbook tương ứng:** `HighLatencyP95` (>3000 ms), `HighErrorRate` (>2%), `LowRetrievalSuccess` (<90%), mỗi điều kiện duy trì 5 phút; Slack `#k4-l3b-alerts`, chi tiết tại [config/alert_rules.yaml](../config/alert_rules.yaml) và [docs/alerts.md](../docs/alerts.md).

> Ví dụ cách viết error budget: "SLO 99.5% trong 28 ngày nghĩa là error budget 0.5%. Nếu workload có 10,000 request thì tối đa 50 request được phép lỗi hoặc chậm hơn ngưỡng SLO."

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1` (cohort K4, incident `rag_slow`, affected feature `monitoring`). Challenge config được Lab Coach cấp và giữ ngoài Git theo `.gitignore`.
- **Khoảng thời gian điều tra:** 2026-09-30 khoảng 12:44:32–12:44:46 giờ Việt Nam (05:44:32–05:44:46 UTC), sau khi bật incident.
- **Triệu chứng từ metrics:** Baseline trước incident: 10 request, error 0%, retrieval 100%; dashboard P95 1,211 ms. Sau 5 request challenge: 15 request tổng, error 0%, retrieval 100%, P95 2,654.6 ms (tăng khoảng 1,444 ms so với dashboard baseline). Log baseline có cold-start đầu tiên 2,075 ms; 9 request warm là 152–155 ms. Challenge lên 2,653–2,656 ms, tăng khoảng 2.5 giây so với warm baseline. Ảnh: baseline CP3 P95 1,211 ms; [dashboard sau incident](evidence/05-dashboard-incident.png).
- **Log line và correlation ID liên quan:** `response_sent` ghi latency 2,653–2,656 ms cho 5 request challenge. Ví dụ `req-062aca18`: 2,653 ms lúc `2026-09-30T05:44:35.434215Z`; các ID còn lại: `req-66b1086a` (2,654 ms), `req-ddffc015` (2,653 ms), `req-b651d8ba` (2,653 ms), `req-77734de7` (2,656 ms). Tất cả là feature `monitoring`, `tool_name=retrieval`, `tool_success=true`. Ảnh: incident log `req-062aca18` (ảnh chuẩn sẽ nằm tại `evidence/01-incident-log.png`).
- **Trace ID và span gây ảnh hưởng:** Trace ID `9f7e576249ea1051e052750bede8a8d1`, correlation ID `req-062aca18`. Span `retrieval` mất 2.50 s; span `generation` mất 0.15 s. Tổng trace khoảng 2.66 s; generation có 186 tokens và cost `$0.002358`. Ảnh: [incident trace](evidence/03-incident-trace.png).
- **Root cause:** Challenge bật incident `rag_slow`; mã retrieval chủ động chờ 2.5 giây. Trace xác nhận span `retrieval` mất đúng 2.50 s, còn `generation` chỉ 0.15 s; điều này khớp với log 2,653 ms và metrics P95 2,654.6 ms.
- **Fix action:** Tắt incident `rag_slow`; API trả HTTP 200 và `/health` xác nhận cả `rag_slow`, `tool_fail`, `cost_spike` đều `false`. Chưa có request sau khi tắt để đo xác nhận latency phục hồi.
- **Preventive measure:** Alert SLO hiện tại báo khi P95 vượt 3,000 ms, nhưng ngưỡng này cao hơn P95 của challenge (2,654.6 ms) nên sẽ không báo cho sự cố này. Giữ alert SLO cho vi phạm nghiêm trọng và đề xuất thêm cảnh báo thời lượng span retrieval trên 2,000 ms cùng runbook tra correlation ID; đây là đề xuất, chưa cấu hình trong `config/alert_rules.yaml`.

> Gợi ý cách viết ngắn, không thay cho evidence thực tế: "Metric cho thấy `[latency/error/cost/quality]` bất thường trong `[khoảng thời gian]`. Log line `[event]` có `correlation_id=[...]` đại diện cho request bị ảnh hưởng. Trace cùng `correlation_id` cho thấy span `[retrieval/generation/prompt/tool]` có dấu hiệu `[chậm/lỗi/token tăng]`. Root cause là `[nguyên nhân suy ra từ evidence]`. Fix action là `[hành động khôi phục]`; preventive measure là `[alert/runbook/test/guardrail để ngăn tái diễn]`."

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Trace lưu metadata, token và cost nhưng không lưu raw prompt/output để giảm nguy cơ ghi PII.
- **Một lỗi/blocker đã gặp:** PowerShell báo parser error khi dán lệnh kèm số thứ tự/định dạng Markdown.
- **Cách tìm nguyên nhân và xử lý:** Bỏ số thứ tự và dấu Markdown, chạy trực tiếp `Invoke-RestMethod`; API trả response thành công.
- **Cách hiểu luồng Metrics → Logs → Traces:** Dashboard chỉ ra bất thường và khoảng thời gian; `correlation_id` tìm đúng structured log; cùng ID lọc trace để xem retrieval/generation.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** Version/label xác định prompt đã phục vụ request; token/cost và SLO giúp nhận ra thay đổi ảnh hưởng vận hành; rollback đưa `production` về v1 đã biết.
- **Điều quan trọng nhất đã học:** `correlation_id` nối log với trace, còn trace ID định danh trace; chúng phục vụ hai mục đích khác nhau.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** Alert P95 3000 ms không phát hiện challenge có P95 2654.6 ms; report đề xuất thêm alert retrieval trên 2000 ms. CP3 hoàn tất; incident đã tắt và health xác nhận mọi incident `false`.

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
