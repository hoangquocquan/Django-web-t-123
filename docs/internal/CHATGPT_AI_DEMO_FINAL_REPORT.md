# BÁO CÁO HOÀN THIỆN DEMO AI — MECPRECISION VIETNAM

**Ngày kiểm tra:** 2026-09-19  
**Nhánh:** `codex/demo-database-validation`  
**Phạm vi:** AI bán hàng, trợ lý tài liệu nội bộ và điều kiện tiên quyết của chatbot công khai  
**Kết luận chung:** Hai luồng AI nội bộ đã chạy được từ giao diện với dữ liệu FULL local. Chatbot công khai chưa đủ dữ liệu để demo vì không có tài liệu được duyệt ở mức `public`.

## 1. Nguyên tắc an toàn đã tuân thủ

- Không reset database.
- Không chạy lại seed và không xóa dữ liệu hiện có.
- Không đổi tài liệu nội bộ sang `public`.
- Không gửi email, không duyệt báo giá và không sửa lead/cơ hội kinh doanh từ AI.
- Không áp dụng patch mù quáng. File `AI_ASSISTANT_UPDATE.patch` không tồn tại trong workspace tại thời điểm kiểm tra.
- Không merge vào `main`, không push GitHub và không deploy công khai.
- Working tree đã có nhiều thay đổi chưa commit; toàn bộ thay đổi có sẵn được giữ nguyên.

## 2. Trạng thái môi trường hiện tại

| Hạng mục | Kết quả |
| --- | --- |
| Git branch | `codex/demo-database-validation` |
| Database đích | SQLite local: `django_backend/db.sqlite3` |
| Django API | PASS — `http://127.0.0.1:8001/api/v1/health/` trả HTTP 200 |
| Frontend | PASS — `http://127.0.0.1:5174/` trả HTTP 200 |
| Ollama | PASS — tiến trình đang chạy; có `qwen2.5-coder:7b` và `deepseek-r1:8b` |
| Model dùng cho demo | `qwen2.5-coder:7b` |
| Redis | Không thấy service/process Redis local đang chạy; hai luồng demo trực tiếp vẫn hoạt động. Đây không phải bằng chứng cho stack production-like đầy đủ. |

Số liệu database đọc lại sau demo:

| Dữ liệu | Số lượng |
| --- | ---: |
| SalesLead | 700 |
| SalesOpportunity | 350 |
| KnowledgeDocument | 200 |
| KnowledgeDocument `permission_level="public"` | 0 |
| KnowledgeChunk | 10.601 |
| KnowledgeEmbedding | 10.601 |
| KnowledgeAssistantLog | 9 |
| AIRequestLog | 9 |

Tài khoản `ai.demo@production-demo.invalid` tồn tại trong bảng người dùng nghiệp vụ, đang active và có role `Sales`. Mật khẩu được nhận từ biến môi trường khi tạo/cập nhật, được hash trong database và không được ghi vào mã nguồn, Git hoặc báo cáo này.

## 3. AI bán hàng — PASS

**URL:** `http://127.0.0.1:5174/#/sales-ai`

Giao diện đã được nối với API thật và có trạng thái đang xử lý, lỗi, nguồn, độ tin cậy, cảnh báo, provider và cờ an toàn.

### 3.1 Phân tích lead

**Đầu vào thực tế:**

- Lead ID: `3`
- Lead: `[PDV1] Sales Lead 3`
- Mối quan tâm: `CNC fixture quotation`

**Kết quả trên giao diện:**

- Provider/mode: `OLLAMA`, action `LEAD_ANALYSIS`
- Điểm: `79`
- Hạng: `B`
- Gợi ý: xác nhận nhu cầu kỹ thuật, người ra quyết định, bản vẽ, vật liệu, số lượng, dung sai và thời hạn giao hàng.
- Nguồn hiển thị: `[PDV1] CNC milling capability 1`
- Độ tin cậy nguồn hiển thị: khoảng `95%`
- `autonomous_action=false`
- `human_approval_required=true`

Đây là kết quả do Ollama tạo với model `qwen2.5-coder:7b`, không phải fallback.

### 3.2 Tạo nháp email

**Kết quả trên giao diện:**

- Trạng thái: `DRAFT_ONLY_NOT_SENT`
- Provider/mode: `OLLAMA`, action `EMAIL_DRAFT`
- Tiêu đề nháp: `Follow-Up on CNC Fixture Quotation for Medical Fixture Industry`
- Nguồn: `[PDV1] Material certificate handling 4` và `[PDV1] Material certificate handling 10`
- Độ tin cậy hiển thị: khoảng `72%`
- `autonomous_action=false`
- `human_approval_required=true`

Giao diện chỉ hiển thị nội dung nháp; không có thao tác tự gửi email, sửa CRM hoặc tự duyệt báo giá.

### 3.3 Gợi ý công việc trong tuần

**Kết quả trên giao diện:**

- Mode: `FALLBACK`, action `WEEKLY_RECOMMENDATION`
- Đề xuất ưu tiên lead đang ở trạng thái contacted/meeting và rà soát cơ hội giá trị lớn nhưng xác suất thấp.
- Trả về 5 lead: `206`, `309`, `515`, `618`, `1`.
- Trả về 5 cơ hội: `182`, `181`, `180`, `177`, `176`.
- Độ tin cậy hiển thị: khoảng `70%`; source confidence `0%`.

Kết quả này là fallback xác định từ dữ liệu CRM/Sales local, **không phải kết quả do Ollama tạo**.

### 3.4 Kiểm tra không thay đổi dữ liệu kinh doanh

- Trước và sau demo vẫn có 700 lead và 350 cơ hội.
- Các thao tác AI chỉ tạo log kiểm toán và kết quả tư vấn.
- Không gửi email và không gọi luồng ghi dữ liệu kinh doanh tự động.

## 4. Trợ lý tài liệu nội bộ — PASS

**URL:** `http://127.0.0.1:5174/#/sales-docs`

Đã đăng nhập bằng tài khoản demo role Sales. Giao diện gọi API thật, hiển thị câu trả lời, nguồn, confidence, warning, provider, trạng thái sinh câu trả lời và trạng thái lỗi/đang xử lý.

### 4.1 Câu hỏi CNC

**Câu hỏi:** `Quy trình first article inspection cho CNC cần kiểm tra gì?`

- Provider: `OLLAMA-LOCAL`
- Trạng thái: `GENERATED`
- Model: `qwen2.5-coder:7b`
- Nội dung trả lời đề cập dimensional report, dung sai, bằng chứng kiểm tra, deburring và capability note.
- Nguồn: `[PDV1] CNC milling capability 1`
- Confidence câu trả lời: khoảng `60%`; source confidence khoảng `78%`.
- Cảnh báo: câu trả lời chưa nhắc trực tiếp tên tài liệu nguồn.

### 4.2 Câu hỏi RFQ

**Câu hỏi:** `Khi RFQ có bản vẽ STEP/PDF thì cần xử lý tài liệu như thế nào?`

- Provider: `OLLAMA-LOCAL`
- Trạng thái: `GENERATED`
- Nội dung trả lời đề cập tiếp nhận/kiểm tra bản vẽ, revision, dung sai, vật liệu, số lượng, due date, xác nhận quản lý và theo dõi.
- Nguồn: `[PDV1] RFQ intake checklist 6`, `12`, `18`, `24`, `30`.
- Confidence/source confidence: khoảng `59%`.
- Có cảnh báo về việc câu trả lời chưa nhắc trực tiếp tên tài liệu.

### 4.3 Câu hỏi quy trình báo giá

**Câu hỏi:** `Quy trình báo giá SUS304 cần kiểm tra những điểm nào?`

- Provider: `OLLAMA-LOCAL`
- Trạng thái: `GENERATED`
- Nội dung trả lời đề cập chứng từ vật liệu, dung sai, ghi chú kỹ thuật và thời hạn rõ ràng.
- Nguồn: `[PDV1] Material certificate handling 4`, `10`, `16`, `22`, `28`.
- Confidence/source confidence: khoảng `56%`.

### 4.4 Câu hỏi ngoài phạm vi

**Câu hỏi:** `Kết quả bóng đá hôm qua của Brazil là gì?`

- Provider: `SOURCE-FALLBACK`
- Trạng thái: `BLOCKED_NO_CONTEXT`
- Trả lời: `Không tìm thấy tài liệu phù hợp để trả lời chắc chắn.`
- Số nguồn trả về: `0`
- Source confidence: `0%`
- Cảnh báo: độ liên quan thấp hơn ngưỡng; hệ thống không gửi câu hỏi cho model để tự suy đoán.

Đây là cơ chế chặn/fallback dựa trên nguồn, **không phải câu trả lời do Ollama tạo**. Kiểm tra này xác nhận trợ lý không tự bịa đáp án ngoài phạm vi.

## 5. Chatbot AI công khai — BLOCKED / CHƯA ĐỦ DỮ LIỆU

Database hiện có `0` tài liệu `KnowledgeDocument` với `permission_level="public"`. Không tài liệu nội bộ nào được đổi quyền trong nhiệm vụ này.

Vì vậy kết luận đúng là: **chưa đủ dữ liệu để demo chatbot công khai**.

Tài liệu nên được biên soạn và duyệt riêng trước khi triển khai:

- Tổng quan năng lực gia công CNC có thể công khai.
- Hướng dẫn khách hàng chuẩn bị RFQ và bản vẽ.
- FAQ quy trình báo giá ở mức công khai, không chứa giá, tên khách hàng hoặc quy tắc phê duyệt nội bộ.
- Tổng quan vật liệu, dung sai, kiểm tra chất lượng có thể công khai.
- Chính sách liên hệ và bảo mật dữ liệu khách hàng.

Chỉ sau khi tài liệu được kiểm duyệt và gắn `public` mới nên chạy kiểm tra chống rò rỉ thông tin khách hàng, kho, giá và quy trình nội bộ.

## 6. Kiểm thử đã chạy

| Kiểm tra | Kết quả |
| --- | --- |
| `python manage.py check` | PASS |
| Frontend typecheck | PASS |
| Frontend production build | PASS |
| Frontend test suite | PASS — 143 test |
| API smoke: Sales lead analysis | PASS — `generation_mode=ollama`, score 79, autonomous false |
| API smoke: email draft safety | PASS — draft only, not sent |
| API smoke: weekly recommendation | PASS — fallback, 5 lead + 5 cơ hội |
| API smoke: knowledge in-scope | PASS — `ollama-local/generated`, có nguồn |
| API smoke: out-of-scope | PASS — `source-fallback/blocked_no_context`, 0 nguồn |

Phân biệt quan trọng: dữ liệu FULL chứa **150 ca đánh giá AI**. Con số 150 là số fixture/case có trong dữ liệu và báo cáo seed; nhiệm vụ này **không chạy lại toàn bộ 150 ca**. Các ca thực sự chạy trong demo này là ba thao tác AI bán hàng, ba câu hỏi nội bộ, một câu ngoài phạm vi, các API smoke và 143 frontend test nêu trên.

## 7. Thay đổi mã chính phục vụ demo

- `figma_make_frontend/src/api/aiDemo.ts`: client API cho hai màn hình AI.
- `figma_make_frontend/src/App.tsx`: thay nội dung mock bằng giao diện API thật.
- `django_backend/apps/core/management/commands/ensure_local_ai_demo_user.py`: tạo/cập nhật tài khoản demo từ biến môi trường, không lưu plaintext password.
- `django_backend/config/settings/development.py`: dùng model Ollama đã cài `qwen2.5-coder:7b`.
- `django_backend/apps/knowledge/services/assistant_service.py`: thêm ngưỡng confidence để chặn câu hỏi ngoài phạm vi trước khi gọi model.

Tất cả thay đổi hiện vẫn ở working tree của nhánh hiện tại và chưa được commit/push/merge.

## 8. Cách tự mở demo trên máy

Backend:

```powershell
cd "C:\Users\hoang\Documents\ChatGPT\WEB Ô TÔ DJANGO\django_backend"
python manage.py runserver 127.0.0.1:8001 --noreload
```

Frontend:

```powershell
cd "C:\Users\hoang\Documents\ChatGPT\WEB Ô TÔ DJANGO\figma_make_frontend"
$env:PHASE6_VITE_PORT="5174"
$env:VITE_DJANGO_ORIGIN="http://127.0.0.1:8001"
npm.cmd run dev -- --host 127.0.0.1 --port 5174
```

Nếu cần đặt lại mật khẩu demo local, tự chọn mật khẩu và chỉ truyền qua biến môi trường:

```powershell
$env:MEC_AI_DEMO_PASSWORD="<mat-khau-local-tu-chon>"
python manage.py ensure_local_ai_demo_user --email ai.demo@production-demo.invalid --role Sales
Remove-Item Env:\MEC_AI_DEMO_PASSWORD
```

URL:

- Health: `http://127.0.0.1:8001/api/v1/health/`
- AI bán hàng: `http://127.0.0.1:5174/#/sales-ai`
- Trợ lý tài liệu: `http://127.0.0.1:5174/#/sales-docs`

## 9. Tổng kết trạng thái

| Chức năng | Trạng thái | Bằng chứng chính |
| --- | --- | --- |
| AI bán hàng | **PASS** | Ba thao tác chạy từ UI; lead analysis và email draft do Ollama tạo; weekly recommendation được ghi rõ là fallback; không gửi email/không sửa dữ liệu kinh doanh. |
| Trợ lý tài liệu nội bộ | **PASS** | Bốn câu hỏi chạy từ UI; ba câu in-scope có nguồn và confidence; câu ngoài phạm vi bị chặn, không gọi model để bịa đáp án. |
| Chatbot AI công khai | **BLOCKED** | Database có 0 tài liệu `public`; chưa đủ dữ liệu để demo và không tự đổi quyền tài liệu nội bộ. |

Ảnh giao diện đã được quan sát/chụp trong phiên in-app browser khi chạy demo. Phiên này không lưu file PNG độc lập vào repository, nên báo cáo dùng kết quả hiển thị và log/API đã kiểm tra làm bằng chứng tái lập.
