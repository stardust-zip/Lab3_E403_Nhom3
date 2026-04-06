# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Huynh Nhut Huy
- **Student ID**: 2A202600084
- **Date**: 6/4/2026

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implementated**:Module main.py - entry point, CLI routing(chatbot / agent-v1 /agent-v2), create_provider() factory pattern, CLI routing và tiến hành tạo LLM provider. Module src/core/chat.py - class Chatbot, implement chat() method triển khai chatbot baseline không dùng tools
- **Code Highlights**: 
*1. `create_provider()` — Factory Pattern trong `main.py`**

```python
def create_provider():
    provider_type = os.getenv("DEFAULT_PROVIDER", "local")
    if provider_type == "openai":
        from src.core.openai_provider import OpenAIProvider
        return OpenAIProvider(...)
    elif provider_type == "google":
        from src.core.gemini_provider import GeminiProvider
        return GeminiProvider(...)
    else:
        from src.core.local_provider import LocalProvider
        return LocalProvider(...)
```

Module giúp tách biệtvlogic chọn backend (OpenAI / Gemini / Local) khỏi phần chạy chatbot và agent. Các module `run_chatbot()` và `run_agent()` nhận vào một `LLMProvider` duy nhất — không biết và không cần biết backend cụ thể đang chạy là gì. Module này giúp dễ dàng swap model. 

*2. `Chatbot.chat()` — Baseline không có tools**

``` python
def chat(self, user_input: str) -> str:
    logger.log_event("CHATBOT_START", {
        "input": user_input,
        "model": self.llm.model_name,
    })
    result = self.llm.generate(user_input, system_prompt=self.get_system_prompt())
    content = result.get("content", "")
    usage = result.get("usage", {})
    latency = result.get("latency_ms", 0)
    tracker.track_request(
        provider=result.get("provider", "unknown"),
        model=self.llm.model_name,
        usage=usage,
        latency_ms=latency,
    )
    logger.log_event("CHATBOT_END", {
        "output": content,
        "latency_ms": latency,
        "tokens": usage,
    })
    return content
```
Chatbot sẽ nhận vào LLMProvider qua constructor thay vì gọi trực tiếp. Toàn bộ logic: Nhận input -> gọi LLM -> trả output không có loop và không có tool call

- **Documentation**: Vậy thì chatbot tương tác với hệ thống như thế nào. Chatbot không tham gia vào ReAct. Ở đây dùng để tham chiếu với ReAct Agent để kiểm tra xem liệu có câu hỏi nào Agent không vượt qua được Chatbot không, nếu có thì cho thấy chi phí overhead của reasoning hay tool call loop. Ở main.py đã tách rõ routing, chatbot sẽ gọi run_chatbot(), agent-v1/v2 sẽ gọi run_agent() đảm bảo đọc lập và dễ so sánh.

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: Output thường bị lỗi do không nhận đúng format json (đối với agent khi cần sparse nhiều bước và nhiều tools)
- **Log Source**: Chưa rõ file log cụ hể
- **Diagnosis**: LLM trả ra không đúng format json có 2 lý do chính. Một là prompt ban đầu chưa chặt và hai là LLM là mô hình ngôn ngữ nên đôi lúc sẽ trả ra sai dạng format (trừ trường hợp model có hỗ trợ structure output)
- **Solution**: Dùng model xịn hơn và prompt chính xác hơn. Thêm các cơ chế để sparse output

- **Problem Description**: Khi chạy `python main.py chatbot` trên môi trường Windows, terminal xuất ra ký tự lỗi thay vì tiếng Việt
Bot: Xin ch├áo! T├┤i c├│ th╗ ги├║p g├¼ cho b├ín?

Response từ LLM chứa ký tự UTF-8 nhưng `sys.stdout` mặc định của Windows dùng encoding `cp1252`, dẫn đến `UnicodeEncodeError` hoặc hiển thị sai.

- **Log Source**:

Log ghi nhận output bình thường (JSON escaped), nhưng console bị lỗi encoding:

```json
{
  "timestamp": "2026-04-06T13:22:10.441Z",
  "event": "CHATBOT_END",
  "data": {
    "output": "Xin chào! Tôi có thể giúp gì cho bạn?",
    "latency_ms": 843,
    "tokens": {"prompt_tokens": 42, "completion_tokens": 18}
  }
}
```
- **Diagnosis**: IndustryLogger ghi log dưới dạng JSON qua logging.FileHandler — file handler mặc định dùng UTF-8 nên log file không bị lỗi. Vấn đề nằm ở sys.stdout của Python trên Windows mặc định dùng encoding cp125, không hỗ trợ ký tự tiếng Việt khi print ra terminal.
- **Solution**: Thêm dòng sau ngay sau import sys trong main.py:

```python
sys.stdout.reconfigure(encoding="utf-8")
```

Dòng này ép stdout dùng UTF-8, đồng bộ với encoding mà LLMProvider trả về và IndustryLogger ghi file. Sau fix, terminal hiển thị đúng tiếng Việt và log file nhất quán với console output.
---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: Chatbot.chat() là oneshot: LLM nhận input từ user và trả ra output trực tiếp dựa trên internal knowledge đã được huấn luyện. Ví dụ khi hỏi cửa hàng của bạn có những loại điện thoại nào, chatbot chỉ có thể trả lời chung chung dựa trên những hãng điện thoại có sẵn trong training data của nó vì nó không thể kiểm tra chính xác. Còn ngược lại khi dùng ReAct, Agent 1 và 2 có bước Thought nó buộc agent lập kế hoạch -> Sau đó xác định được rằng -> Tôi nên kiểm tra hàng trong kho -> check_inventory - sau đó điều chỉnh bước tiếp theo dựa trên observation thực tế. Thought hay reasoning chính là nơi LLM tự giải thích lý do để nếu có sai xót thì sẽ phát hiện sớm.
2.  **Reliability**: 
    Trường hợp câu hỏi đơn giản: Ví dụ xin chào, cảm ơn. Agent vẫn phải suy nghĩ phức tạp, làm tăng latency không cần thiết.
    Câu hỏi kiến thức mang tính chất tổng quát: Ví dụ Iphone của hãng nào, LLM có thể trả lời nhanh trong khi Agent phải suy luận và chọn tools rồi kiểm tra xem Iphone của hãng nào, đôi khi sẽ gọi tool không phù hợp hoặc output sai hoặc bị loop.
    Trường hợp nữa là khi chúng ta so sánh về chi phí: Mỗi lượt ReAct loop sẽ tốn thêm tokens, làm tăng chi phí đáng kể so với dùng Chatbot cho cùng một câu đơn giản
3.  **Observation**: 
    Đối với chatbot thì nó không có loop nên nếu response sai là sai luôn, không có thể tự sửa.
    ReAct Agent thì ngược lại: Mỗi Observation LLM sẽ nhận được kết quả mới và đưa lại vào context, cho phép LLM điều chỉnh hướng đi tiếp theo nếu cần thiết. Vì dụ nếu check_inventory() trả về hết hàng, LLM có thể lựa chọn search các sản phẩm tương đương. 
---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: Thêm conversation_history: List[Dict] vào Chatbot để lưu lịch sử hội thoại qua nhiều lượt, truyền vào llm.generate() dưới dạng messages list. Kết hợp với async I/O asyncio để xử lý nhiều user đồng thời mà không block.
- **Safety**:  Thêm một lớp **Input/Output Guard** trước và sau llm.generate() — validate input không chứa prompt injection, kiểm tra output không leak thông tin nhạy cảm (giá nội bộ, tên kho, v.v.). Có thể implement bằng một LLMProvider wrapper bọc ngoài provider hiện tại mà không cần sửa Chatbot.
- **Performance**: Cache system_prompt thành constant thay vì gọi get_system_prompt() mỗi request để tránh tạo string thừa.

---
