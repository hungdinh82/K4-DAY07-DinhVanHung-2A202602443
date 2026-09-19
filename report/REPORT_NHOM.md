# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** 2 Idiots
**Thành viên:**
- Đinh Văn Hùng — 2A202602443 — Nhóm trưởng; R2 Benchmark; R3 Strategy
- Lê Hoàng Thiên Phú — 2A202602908
**Ngày:** 19/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Quy định mượn và yêu cầu tài liệu của Thư viện University of Sydney (K4-L3A).

**Tại sao nhóm chọn chủ đề này?**
> Đây là nhóm quy định đại học công khai, có nhiều điều kiện, con số và mốc thời gian phù hợp để kiểm tra chất lượng retrieval. Nguồn chính thức cũng phân biệt người học và nhân viên trong dịch vụ Resource Sharing, nhờ đó trường `audience` tạo ra phép thử metadata filter có ý nghĩa thay vì chỉ tồn tại trên schema.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Limits on borrowing | [University of Sydney Library](https://www.library.sydney.edu.au/support/borrowing/limits-on-borrowing) | 2026-09-19 / `not-stated` | 960 | `audience=all`, `category=borrowing-limits`, `department=library`, `language=en` |
| 2 | Borrowing terms and conditions | [University of Sydney Library](https://www.library.sydney.edu.au/about/governance/borrowing-terms-and-conditions) | 2026-09-19 / `not-stated` | 1.400 | `audience=all`, `category=borrowing-policy`, `department=library`, `language=en` |
| 3 | Requesting items | [University of Sydney Library](https://www.library.sydney.edu.au/support/borrowing/requesting-items) | 2026-09-19 / `not-stated` | 1.575 | `audience=all`, `category=requests`, `department=library`, `language=en` |
| 4 | Returning items | [University of Sydney Library](https://www.library.sydney.edu.au/support/borrowing/returning-items) | 2026-09-19 / `not-stated` | 1.195 | `audience=all`, `category=returns`, `department=library`, `language=en` |
| 5 | Resource sharing for eligible students | [University of Sydney Library](https://www.library.sydney.edu.au/support/borrowing/request-an-item-from-outside-our-library) | 2026-09-19 / `not-stated` | 1.404 | `audience=student`, `category=resource-sharing`, `department=library`, `language=en` |
| 6 | Resource sharing for staff | [University of Sydney Library](https://www.library.sydney.edu.au/support/borrowing/request-an-item-from-outside-our-library) | 2026-09-19 / `not-stated` | 1.291 | `audience=staff`, `category=resource-sharing`, `department=library`, `language=en` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `resource-sharing-students` | Định danh ổn định, duy nhất; liên kết file nguồn với chunk và dòng trong `sources.csv`. |
| `title` | string | `Resource sharing for eligible students` | Bổ sung tín hiệu ngữ nghĩa và giúp hiển thị nguồn dễ đọc. |
| `source_url` | URL string | `https://www.library.sydney.edu.au/...` | Truy vết câu trả lời về nguồn chính thức để kiểm chứng. |
| `retrieved_at` | date (`YYYY-MM-DD`) | `2026-09-19` | Cho biết thời điểm chụp dữ liệu, hữu ích khi quy định thay đổi. |
| `document_version` | string | `not-stated` | Lưu phiên bản khi nguồn công bố; dùng `not-stated` để tránh tự đặt phiên bản. |
| `audience` | enum string | `student`, `staff`, `all` | Cho phép lọc đúng đối tượng; đặc biệt tách điều kiện Resource Sharing của sinh viên và nhân viên. |
| `department` | string | `library` | Giới hạn retrieval theo đơn vị cung cấp dịch vụ khi corpus được mở rộng. |
| `category` | string | `returns`, `requests`, `resource-sharing` | Thu hẹp kết quả theo loại quy định hoặc thao tác cần tra cứu. |
| `language` | ISO-like string | `en` | Hỗ trợ chọn embedder và lọc ngôn ngữ cho corpus đa ngữ. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `borrowing-limits.md` | FixedSizeChunker (`fixed_size`) | 2 | 343.0 | Có, nhưng có thể cắt giữa mục |
| `borrowing-limits.md` | SentenceChunker (`by_sentences`) | 3 | 227.0 | Tốt theo ranh giới câu |
| `borrowing-limits.md` | RecursiveChunker (`recursive`) | 2 | 342.0 | Tốt, giữ được đoạn lớn |
| `borrowing-terms.md` | FixedSizeChunker (`fixed_size`) | 3 | 368.7 | Có, nhưng có thể cắt giữa mục |
| `borrowing-terms.md` | SentenceChunker (`by_sentences`) | 4 | 274.8 | Tốt theo ranh giới câu |
| `borrowing-terms.md` | RecursiveChunker (`recursive`) | 3 | 367.3 | Tốt, cân bằng kích thước và ngữ cảnh |
| `requesting-items.md` | FixedSizeChunker (`fixed_size`) | 3 | 438.3 | Có thể cắt giữa quy trình |
| `requesting-items.md` | SentenceChunker (`by_sentences`) | 4 | 327.0 | Mạch lạc, nhưng nhiều chunk hơn |
| `requesting-items.md` | RecursiveChunker (`recursive`) | 4 | 327.2 | Khá tốt cho tài liệu nhiều mục |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — Đinh Văn Hùng (R2 Benchmark + R3 Strategy)**
- **Loại chiến lược:** Custom `HeadingChunker`
- **Mô tả & lý do chọn cho chủ đề này:** Tách tài liệu theo các heading `##`, vì mỗi mục quy định thường là một đơn vị ngữ nghĩa hoàn chỉnh. Nếu section quá dài, tiếp tục dùng recursive chunking và gắn lại heading vào từng chunk con để không mất ngữ cảnh.
- **Code snippet (nếu custom):**
```python
# Chiến lược được triển khai trong `bench.py`: `HeadingChunker`
```

**Thành viên 2 — Lê Hoàng Thiên Phú**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Đinh Văn Hùng | HeadingChunker | 3/10 với filter | Giữ heading và ngữ nghĩa từng mục | Mock embedding làm thứ hạng nhiễu |
| Lê Hoàng Thiên Phú | Chưa cập nhật | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Với số liệu MockEmbedder, FixedSize đạt 4/10, còn Sentence và Recursive đạt 3/10; tuy nhiên đây chỉ là tín hiệu tham khảo vì mock không hiểu ngữ nghĩa. Về cấu trúc, HeadingChunker phù hợp nhất với tài liệu quy định vì giữ nguyên heading và không làm mất ngữ cảnh của từng mục.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | How many Short Loan items may be borrowed at once, and how long does each loan last? | Only two Short Loan items may be borrowed at once; each lasts 3 hours. | `borrowing-limits`, mục Standard limits |
| 2 | Under what conditions may a General Collection item be kept for up to 365 days? | No recall; enrolment or membership remains current; no fines or blocks. | `borrowing-terms`, mục General Collection loans |
| 3 | How do I request a digital copy of a journal article or book chapter? | Sign in, select journal/location, choose Request a digital copy, complete the form and copyright acknowledgement, then submit. | `requesting-items`, mục Collection and digitisation |
| 4 | Where must a Short Loan item be returned? | To the location from which it was borrowed. | `returning-items`, mục Return chutes |
| 5 | How many items can I borrow through Resource Sharing in a calendar year, and who is eligible? | Postgraduate and honours students are eligible; they may borrow up to 100 items per calendar year. | `resource-sharing-students`, mục Eligibility and allowance; filter `audience=student` |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | HeadingChunker | 0 điểm nội dung | Chunk đúng không nằm top-3; chỉ nhìn doc_id sẽ đánh giá sai |
| 2 | HeadingChunker | 0 điểm nội dung | Top-1 cùng tài liệu nhưng là section overdue, không chứa điều kiện 365 ngày |
| 3 | HeadingChunker | 2 điểm | Top-1 `requesting-items#4` chứa đủ gold phrases |
| 4 | HeadingChunker | 0 điểm nội dung | Top-2 cùng tài liệu nhưng là section postal returns, không trả lời câu hỏi |
| 5 | HeadingChunker + `audience=student` | 1 điểm | Chunk đúng ở top-2; filter loại tài liệu staff nhưng chunk request đứng trước chunk eligibility |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có, rõ nhất ở câu 5. Câu hỏi không nêu rõ đối tượng nhưng hai tài liệu Resource Sharing cho student và staff có cùng từ vựng; filter `audience=student` bảo đảm toàn bộ kết quả đến từ tài liệu dành cho sinh viên.

**A/B cho câu 5:**
> Với `HeadingChunker`, có filter đạt 1/2 vì chunk chứa gold đứng top-2; không filter đạt 0/2 vì top-3 không chứa tài liệu student. Với `SentenceChunker`, có filter đạt 2/2 nhưng không filter đạt 0/2; đây là bằng chứng metadata filter cải thiện precision.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> - `doc_id` đúng chưa đủ: top-3 phải chứa đúng section và đúng thông tin trả lời.
> - Mock embedding có thể xếp section cùng chủ đề nhưng sai nội dung lên trước.
> - Metadata `audience` giúp tách hai tài liệu Resource Sharing có từ vựng gần giống nhau.

**Bài học rút ra khi so sánh trong nhóm:**
> Fixed-size tạo ít chunk hơn nhưng dễ gom nhiều mục không liên quan. Sentence và heading giữ ranh giới tự nhiên tốt hơn, nhưng vẫn cần embedding có ngữ nghĩa để xếp đúng section.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ dùng embedding multilingual/local hoặc API thay cho MockEmbedder khi đo retrieval. Ngoài ra, các section chứa số liệu quan trọng có thể dùng overlap nhỏ hoặc thêm trường metadata về loại thông tin để tăng khả năng truy xuất.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
