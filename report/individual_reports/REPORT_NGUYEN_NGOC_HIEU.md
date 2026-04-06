# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Ngọc Hiếu
- **Student ID**: 2A202600187
- **Date**: 06/04/2026

---

## I. Technical Contribution (15 Points)

Trong Lab 3, vai trò chính của tôi là **Tooling Engineer**. Tôi chịu trách nhiệm thiết kế, lập trình và tối ưu hóa toàn bộ bộ công cụ (Tools) trong thư mục `src/tools/` để ReAct Agent có thể tương tác với "môi trường" (cơ sở dữ liệu giả lập của cửa hàng).

### Các Module đã triển khai:

1. **Thiết kế Kho công cụ (`src/tools/__init__.py`)**: Định nghĩa danh sách `TOOLS` bao gồm tên, hàm thực thi và đặc biệt là **Tool Descriptions**. Như tài liệu hướng dẫn đã nhấn mạnh: _"An LLM only knows a tool through its string description"_, tôi đã tinh chỉnh các đoạn mô tả (description) thật chi tiết để LLM hiểu chính xác khi nào nên gọi tool nào và format input ra sao (VD: `calculator` yêu cầu biểu thức toán học thuần túy).
2. **Product Tools (`src/tools/check_stock.py`, `src/tools/search.py`)**:
   - Xây dựng database giả lập `PRODUCTS`.
   - Lập trình các hàm `check_stock` (tìm chính xác và gần đúng), `search_by_price`, `search_by_brand`, `list_brands`.
   - **Tối ưu**: Xử lý chuỗi đầu vào chặt chẽ (strip, lower, loại bỏ dấu phẩy/chữ 'd' trong giá tiền) để tránh lỗi khi LLM truyền tham số không chuẩn xác.
3. **Promotion Tools (`src/tools/get_discount.py`)**: Xây dựng hàm tra cứu mã khuyến mãi, hỗ trợ tìm kiếm linh hoạt (chính xác hoặc chứa chuỗi).
4. **Calculator Tool (`src/tools/calculator.py`)**:
   - Triển khai hàm `calculator` để Agent tính toán tổng tiền.
   - **Bảo mật & Robustness**: Sử dụng Regex `r"^[\d\s\+\-\*\/\.\(\)]+$"` để kiểm tra tính hợp lệ của biểu thức trước khi gọi hàm `eval()`, ngăn chặn rủi ro chạy mã độc (code injection) từ LLM và xử lý lỗi chia cho 0 hoặc sai cú pháp.

---

## II. Debugging Case Study (10 Points)

Trong quá trình tích hợp Tools với ReAct Agent, tôi đã phát hiện và xử lý một lỗi nghiêm trọng liên quan đến cách LLM truyền tham số cho Tool.

- **Vấn đề (Problem Description)**: Khi khách hàng hỏi mua nhiều sản phẩm (Test Case 4), Agent v1 và v2 thi thoảng gặp lỗi tính toán với `calculator()`. Agent gọi Action: `calculator(32,990,000 + 350,000)`, và hệ thống trả về `Observation: Loi: Bieu thuc khong hop le` hoặc crash vòng lặp.
- **Phân tích nguyên nhân (Root Cause Analysis)**: Mặc dù trong system prompt đã dặn LLM truyền số nguyên, LLM (đặc biệt là các model nhỏ) vẫn có thói quen format số tiền với dấu phẩy ngăn cách hàng nghìn cho dễ đọc (vd: `32,990,000`). Hàm `eval()` của Python không hiểu dấu phẩy trong biểu thức toán học, dẫn đến lỗi `SyntaxError`.
- **Cách khắc phục (Solution)**: Thay vì cố gắng ép LLM không dùng dấu phẩy (điều rất khó đảm bảo 100%), tôi đã chủ động sửa lỗi ở phía Tool. Trong `src/tools/calculator.py`, tôi thêm bước tiền xử lý: `cleaned = expression.replace(",", "")` trước khi check Regex và `eval()`. Nhờ đó, tool trở nên "khoan dung" (fault-tolerant) hơn với các output không hoàn hảo của LLM, giúp tỷ lệ thành công của Test Case 4 đạt 100%.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

Qua việc trực tiếp xây dựng các công cụ cung cấp "năng lực" cho LLM, tôi nhận ra sự khác biệt cốt lõi giữa Chatbot truyền thống và Agent:

1. **Khắc phục Hallucination bằng "Ground Truth"**: Chatbot truyền thống hoàn toàn bị mù về dữ liệu hiện tại. Khi hỏi "iPhone 17 Pro giá bao nhiêu?", Chatbot đoán mò dựa trên trọng số mạng nơ-ron (thường bịa ra giá sai). Với ReAct Agent, bước `Observation` sau khi gọi tool `check_stock("iphone 17 pro")` sẽ trả về dữ liệu thực tế (Ground Truth). LLM buộc phải dựa vào dữ liệu này để trả lời, triệt tiêu hoàn toàn sự bịa đặt về giá cả.
2. **Sự phối hợp giữa Suy luận (Reasoning) và Hành động (Acting)**: Chatbot cố gắng tính nhẩm một bài toán giảm giá phức tạp và thường xuyên tính sai. Ngược lại, nhờ có tool `calculator`, Agent chỉ cần đóng vai trò "người lập kế hoạch" (phân rã phép tính) và giao việc tính toán chính xác lại cho Python. Việc chia tách giữa _Language Reasoning_ (LLM làm) và _Symbolic Computation_ (Tool làm) là chìa khóa cho một hệ thống đáng tin cậy.

---

## IV. Future Improvements (5 Points)

Dựa trên cấu trúc Tools hiện tại, để nâng cấp hệ thống này lên mức Production-level (thực tế doanh nghiệp), tôi đề xuất các hướng cải tiến sau cho hệ thống Tooling:

1. **Tích hợp Real Database & RAG**: Thay vì hardcode từ điển `PRODUCTS` trong file Python, các tools như `search_by_brand` hay `check_stock` cần được kết nối qua API tới CSDL thực (PostgreSQL/MongoDB). Ngoài ra, có thể dùng Vector DB (Chroma/Pinecone) để làm RAG tool, giúp Agent trả lời các câu hỏi về thông số kỹ thuật chi tiết của máy.
2. **Dynamic Tool Retrieval (RAG for Tools)**: Hiện tại chúng ta đang nhồi toàn bộ mô tả của 7 tools vào System Prompt. Nếu cửa hàng có 50+ tools (tra cứu trả góp, tra cứu bảo hành, check tồn kho chi nhánh...), prompt sẽ quá dài và tốn chi phí token. Cần xây dựng một cơ chế "Router" để tìm kiếm và chỉ nhúng các tools liên quan nhất vào ngữ cảnh hiện tại.
3. **Thực thi bất đồng bộ (Async Tool Execution)**: Khi người dùng cần tìm giá của 3 phụ kiện cùng lúc, thay vì gọi `check_stock` 3 lần nối tiếp nhau (tốn 3 bước của Agent), có thể thiết kế một "Multi-Action Tool" hoặc dùng `asyncio` để lấy dữ liệu song song, giúp giảm mạnh độ trễ (latency).
