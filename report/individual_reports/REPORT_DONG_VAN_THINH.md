# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Đồng Văn Thịnh
- **Student ID**: 2A202600365
- **Date**: 06/04/2026

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implementated**: `evaluate.py`
- **Code Highlights**: 
    - `analyze_metrics(events: list)`: đánh giá chất lượng, thông số, hiệu suất, giá cả của mô hình
    - `analyze_agents(events: list)`: so sánh hiệu năng giữa các phiên bản hệ thống (Chatbot, Agent v1, Agent v2)
- **Documentation**: Module đóng vai trò hậu kiểm, giúp phân tích toàn diện đầu ra, kết quả và hiệu suất từ dữ liệu thực tế mà mô hình trả về. Thông qua việc đo lường chính xác sự đánh đổi (trade-off) giữa độ chính xác và chi phí (Token), hệ thống cho phép người dùng so sánh khách quan giữa các cấu hình khác nhau, từ đó xác định và lựa chọn được mô hình tối ưu nhất (ví dụ: Agent v2) cho bài toán Agent.

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: Agent rơi vào trạng thái "kiệt sức" (vượt quá max_steps=5) khi xử lý câu hỏi phức tạp như TC4 (Mua combo iPhone 17 Pro + Ốp lưng + Kính cường lực + Mã giảm giá HSSV). Agent thực hiện đúng các bước tra cứu nhưng dừng lại đột ngột trước khi đưa ra câu trả lời cuối cùng cho khách hàng.
- **Log Source**: `test_result.json`
```
  {
    "id": 4,
    "name": "Mua combo + ap dung ma KM cu the",
    "query": "Toi muon mua dien thoai iPhone 17 Pro + op lung + kinh cuong luc, neu ap dung khuyen mai HSSV2026 thi het bao nhieu tien?",
    "agent_v2": "Xin loi, cua hang chung toi hien chi ban dien thoai. Co ban iPhone 17 Pro, op lung, kinh cuong luc. Co khong ban dien thoai iPhone 17 Pro.\n\n\nTo execute this task correctly, we'll have to follow a step-by-step process, taking into consideration the given constraints and using the appropriate tools to obtain the required information.\n\n\nThought: I need to check the availability of iPhone 17 Pro, a power bank, and a laptop, and determine if there is a discount on the HSSV2026 voucher.\n\nAction: check_stock(iphone 17 pro)"
  },
```
- **Diagnosis**: Nguyên nhân không nằm ở mô hình (Model) hay công cụ (Tool), mà nằm ở cấu hình hệ thống (System Config).

- Quy trình ReAct tiêu tốn 1 bước cho mỗi cặp Action/Observation. Với một yêu cầu có 3 sản phẩm + 1 mã giảm giá, Agent cần ít nhất 6-7 bước để hoàn tất.

- Prompt chưa tối ưu việc "gộp" các suy nghĩ, khiến Agent thực hiện các hành động quá rời rạc (atomic actions), dẫn đến việc hết "quỹ thời gian" trước khi kịp tổng hợp kết quả.
- **Solution**: 
    - Nâng cấp cấu hình: Tăng max_steps từ 5 lên 7 để phù hợp với độ phức tạp của 7 công cụ hiện có.
    - Tối ưu Prompt (Few-shot): Bổ sung ví dụ mẫu trong System Prompt hướng dẫn Agent cách thực hiện nhiều tính toán trong một lần gọi calculator hoặc tra cứu nhanh các phụ kiện đi kèm để tiết kiệm bước đi.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: How did the `Thought` block help the agent compared to a direct Chatbot answer?
- Chatbot: Hoạt động theo cơ chế "dự đoán từ tiếp theo" dựa trên xác suất. Khi gặp câu hỏi phức tạp (như tính giá iPhone 17 kèm phụ kiện), Chatbot trả lời ngay lập tức dẫn đến việc từ chối (do thiếu data) hoặc tệ hơn là bịa đặt dữ liệu (Hallucination) để khớp với ngữ cảnh.

- Agent: Khối `thought` đóng vai trò như một "không gian nháp" (Scratchpad). Nó buộc mô hình phải phân rã câu hỏi lớn thành các nhiệm vụ nhỏ (Sub-tasks). Thay vì đoán mò, `thought` giúp Agent xác định: "Mình đang thiếu giá của sản phẩm X, mình cần gọi công cụ Y". Điều này tạo ra một chuỗi lập luận logic (Chain-of-Thought) có kiểm soát trước khi đưa ra kết quả cuối cùng.

2.  **Reliability**: In which cases did the Agent actually perform *worse* than the Chatbot?

- Tốc độ và Chi phí: Agent tốn trung bình 3-5 bước lặp (LLM calls) cho một câu hỏi, dẫn đến độ trễ (Latency) cao hơn gấp nhiều lần so với Chatbot (trả lời trong 1 lần gọi).

- Câu hỏi xã giao/đơn giản: Với các câu hỏi như "Chào bạn" hoặc "Cửa hàng ở đâu?", Agent vẫn có xu hướng "suy nghĩ" quá mức hoặc cố gắng tìm kiếm công cụ không cần thiết, làm lãng phí token và thời gian của người dùng.

- Sự cố lặp (Looping): Nếu công cụ trả về kết quả lỗi hoặc không rõ ràng, Agent đôi khi bị rơi vào vòng lặp vô hạn (Infinite loop) cùng một hành động, trong khi Chatbot thường sẽ xin lỗi và dừng lại ngay.

3.  **Observation**: How did the environment feedback (observations) influence the next steps?

- `observation` chính là "đôi mắt" giúp Agent tiếp xúc với thực tế. Nó đóng vai trò là chốt chặn sửa lỗi (Error correction) giúp Agent xử lý nghiệp vụ, gọi tools hợp lý.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: 
    - Asynchronous Tool Execution (Thực thi công cụ bất đồng bộ): Thay vì đợi từng công cụ trả về kết quả (Sequential), hệ thống có thể gọi đồng thời nhiều công cụ (Parallel) nếu bước Thought xác định được các tác vụ độc lập. Điều này giúp giảm đáng kể tổng thời gian phản hồi (E2E Latency).

    - Distributed Task Queue (Hàng đợi công việc phân tán): Sử dụng Celery hoặc Redis để quản lý các yêu cầu gọi Tool. Khi số lượng người dùng tăng lên, hệ thống có thể tăng số lượng "Worker" để xử lý các phép tính phức tạp mà không làm nghẽn luồng chính của Chatbot.

- **Safety**: [e.g., Implement a 'Supervisor' LLM to audit the agent's actions]
    - Supervisor LLM Layer (Lớp LLM giám sát): Triển khai một mô hình AI nhỏ (như GPT-4o-mini hoặc Llama 3-8B) chuyên trách việc kiểm duyệt đầu ra. Mô hình này sẽ kiểm tra xem câu trả lời cuối cùng có vi phạm chính sách bảo mật, tiết lộ thông tin nhạy cảm của khách hàng khác, hoặc hứa hẹn mức giảm giá vượt quá quyền hạn hay không.

    - Human-in-the-loop (HITL): Đối với các hành động quan trọng như "Xác nhận đặt hàng" hoặc "Thanh toán", hệ thống cần một bước dừng để con người phê duyệt (Approval step) trước khi thực hiện giao dịch thực tế trên database.

- **Performance**: [e.g., Vector DB for tool retrieval in a many-tool system]
    - Vector Database cho Tool Retrieval: Khi hệ thống phát triển lên hàng trăm công cụ (Tra cứu bảo hành, Trả góp, Ship hàng...), việc nạp tất cả vào Prompt sẽ gây lãng phí token và làm loãng sự tập trung của AI. Sử dụng Vector DB để tìm kiếm và chỉ nạp những công cụ liên quan nhất (RAG for Tools) vào ngữ cảnh hiện tại.

    - Semantic Caching: Lưu trữ các kết quả của vòng lặp ReAct cho các câu hỏi tương tự nhau (ví dụ: "Giá iPhone 15 hôm nay"). Nếu một câu hỏi tương đương xuất hiện, Agent có thể lấy kết quả từ Cache thay vì phải thực hiện lại toàn bộ chu trình suy nghĩ và gọi Tool, giúp tiết kiệm chi phí cực lớn.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
