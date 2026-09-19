# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Đinh Văn Hùng
**Mã sinh viên:** 2A202602443
**Vai trò:** Nhóm trưởng; R2 — Benchmark; R3 — Strategy
**Nhóm:** 2 Idiots
**Ngày:** 19/09/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector embedding có hướng gần nhau, cho thấy hai câu có nội dung hoặc ý nghĩa gần nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: Sinh viên cần đăng ký học phần trước hạn.
- Câu B: Người học phải hoàn tất việc ghi danh trước thời hạn.
- Tại sao tương đồng: Hai câu dùng từ khác nhau nhưng cùng diễn đạt một yêu cầu.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Thư viện mở cửa lúc 8 giờ.
- Câu B: Python hỗ trợ lập trình hướng đối tượng.
- Tại sao khác: Hai câu nói về hai chủ đề không liên quan.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine tập trung vào hướng của vector, thường phản ánh ngữ nghĩa tốt hơn và ít bị ảnh hưởng bởi độ dài văn bản. Với vector đã chuẩn hóa, dot product cũng chính là cosine similarity.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Tính: `ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = 23`.
> Đáp án: **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Số chunk tăng lên `ceil((10000 - 100) / (500 - 100)) = 25`. Overlap lớn hơn giúp giữ lại ngữ cảnh ở ranh giới giữa các chunk, nhưng làm tăng chi phí embedding và lưu trữ.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng regex lookbehind `(?<=[.!?])(?:\s+|\n+)` để tách sau dấu câu nhưng vẫn giữ dấu câu. Text rỗng trả về `[]`, sau đó gom các câu theo `max_sentences_per_chunk`. Edge case còn hạn chế là chữ viết tắt như `TS.`, `v.v.` và số thập phân có thể bị tách sai.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán ưu tiên separator lớn như đoạn văn và dòng mới, sau đó đệ quy xuống separator nhỏ hơn khi mảnh vượt `chunk_size`. Các mảnh ngắn liền kề được gom lại gần giới hạn kích thước; nếu không còn separator thì chia theo số ký tự. Base case là text rỗng hoặc độ dài không vượt `chunk_size`.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi `Document` được chuẩn hóa thành một record gồm content, metadata và embedding rồi lưu trong in-memory store. `search` embed query, tính dot product với các vector đã chuẩn hóa, sắp xếp giảm dần theo score và trả về tối đa `top_k` kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Metadata được lọc trước khi similarity search để các vị trí top-k không bị tài liệu sai đối tượng chiếm mất. Metadata được copy và luôn có `doc_id` của file gốc; `delete_document` xóa mọi chunk có `metadata['doc_id']` trùng mã được chỉ định.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Agent truy xuất top-k chunk, đánh số từng context và ghi nguồn từ metadata vào prompt. Prompt yêu cầu chỉ dùng thông tin được cung cấp, nói rõ khi thiếu dữ liệu và trích dẫn số context; nếu store rỗng thì trả thông báo thay vì gọi LLM.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
42 passed in 0.03s
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Sinh viên cần đăng ký học phần trước hạn. | Người học phải hoàn tất việc ghi danh trước thời hạn. | Cao | 0.0639 | Không — MockEmbedder không hiểu đồng nghĩa |
| 2 | Thư viện mở cửa lúc 8 giờ. | Python hỗ trợ lập trình hướng đối tượng. | Thấp | -0.0803 | Có |
| 3 | Mỗi Short Loan kéo dài 3 giờ. | Một khoản mượn ngắn hạn có thời lượng ba tiếng. | Cao | -0.1264 | Không — MockEmbedder không hiểu tương đương số liệu |
| 4 | Tài liệu được gửi qua email. | Bóng đá là môn thể thao đồng đội. | Thấp | -0.0359 | Có |
| 5 | Tài liệu phải trả đúng hạn. | Người mượn cần hoàn trả tài liệu trước ngày hết hạn. | Cao | 0.2109 | Có |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 3 có cùng ý nghĩa và cùng nói về thời lượng 3 giờ nhưng MockEmbedder cho điểm âm. Điều này cho thấy MockEmbedder chỉ tạo vector giả từ MD5, không biểu diễn ngữ nghĩa; vì vậy điểm benchmark bằng mock chỉ dùng để kiểm tra pipeline, không dùng để kết luận chất lượng semantic retrieval.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Short Loan limits | `requesting-items#1` | 0.1292 | Không; gold phrase không nằm top-3 | Không đủ bằng chứng; đáp án chuẩn là tối đa 2 Short Loan, mỗi khoản 3 giờ. |
| 2 | General Collection conditions | `borrowing-terms#2` — mục overdue | 0.2810 | Không; đúng tài liệu nhưng sai section | Không đủ đúng điều kiện 365 ngày; cần section General Collection loans. |
| 3 | Digital copy request | `requesting-items#4` — mục Collection and digitisation | 0.2286 | Có, top-1 | Đăng nhập catalogue, chọn digital copy, hoàn tất form và copyright acknowledgement. |
| 4 | Short Loan return location | `borrowing-limits#0` | 0.3016 | Không; gold phrase không nằm top-3 | Không trả lời chắc chắn; đáp án chuẩn là trả về nơi đã mượn. |
| 5 | Student Resource Sharing | `resource-sharing-students#2` | 0.0587 | Có ở top-2 với filter `audience=student` | Postgraduate/honours students được mượn tối đa 100 items/năm. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 2 / 5 với `MockEmbedder` và filter `audience=student`.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Chunking theo heading giữ được tên mục và giúp người đọc truy vết nguồn dễ hơn. Tuy nhiên benchmark phải dùng embedder có ngữ nghĩa; `MockEmbedder` chỉ phù hợp để kiểm tra cấu trúc nên không thể dùng thứ hạng của nó để kết luận chất lượng retrieval.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 5 / 10 |
| **Tổng phần cá nhân** | **55 / 60** |
