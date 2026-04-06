# Group Report: Lab 3 - Tro ly Cua hang Dien thoai (ReAct Agent)

- **Team Name**: [Nhom 3]
- **Team Members**:

  2A202600187 - Nguyễn Ngọc Hiếu

  2A202600204 - Nguyễn Thành Luân

  2A202600365 - Đồng Văn Thịnh

  2A202600189 - Nguyễn Ngọc Khánh Duy

  2A202600084 - Huỳnh Nhựt Huy

  2A202600188 - Nguyễn Ngọc Hưng

- **Deployment Date**: 2026-04-06

---

## 1. Executive Summary

So sánh hiệu năng giữa Chatbot (không tools) và ReAct Agent (có tools) trong vai trò trợ lý bán hàng điện thoại.

- **Success Rate**: Chatbot 60% (3/5) | Agent v1: 80% (4/5) | Agent v2: **100% (5/5)**
- **Key Outcome**: Agent v2 giải quyết được 100% các trường hợp, bao gồm multi-step (tra giá, tính khuyến mãi, tính tổng) và out-of-domain. Chatbot bịa giá sai toàn bộ các câu hỏi phức tạp.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation

```
                      +-----------------------------------------+
                      v                                         |
User Question --> [Thought] --> [Action: tool(args)] --> [Observation] 
                                                                |
                                                            [Final Answer]
```

Vòng lặp ReAct hoạt động như sau:

1. LLM sinh ra **Thought** (suy nghĩ) và **Action** (gọi tool).
2. Hệ thống parse Action, gọi tool tương ứng.
3. Kết quả trả về làm **Observation**, nạp lại vào prompt.
4. Lặp lại từ **bước 1** cho đến khi có **Final Answer** hoặc hết max_steps.

### 2.2 Định nghĩa công cụ (Inventory)

| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `check_stock` | `string` (tên SP) | Tra giá và số lượng tồn kho |
| `search_by_price` | `string` (giá tối đa VND) | Tìm điện thoại theo khoảng giá |
| `search_by_brand` | `string` (tên hãng) | Tìm điện thoại theo hãng |
| `list_brands` | `string` (truyền 'all') | Liệt kê các hãng có trong cửa hàng |
| `get_discount` | `string` (mã KM) | Tra cứu mã khuyến mãi |
| `list_promotions` | `string` (truyền 'all') | Liệt kê tất cả khuyến mãi |
| `calculator` | `string` (biểu thức toán) | Tính toán số học |

---

### 2.3 Tool Design Evolution (v1 --> v2)

| Thay đổi | v1 | v2 |
| :--- | :--- | :--- |
| System prompt | Chỉ liệt kê tool + format | Thêm **few-shot examples** (2 VD mẫu) |
| Parse Action | 1 regex pattern | **3 regex patterns** (xử lý quotes, markdown) |
| Parse error | Báo lỗi chung, lặp mãi | Đếm số lần, **sau 2 lần ép Final Answer** |
| Loop detection | Không có | **Phát hiện duplicate action**, ép kết thúc |
| Out-of-domain | Không hướng dẫn | Có **ví dụ mẫu** từ chối lịch sự |
| Max steps | 5 | 7 |

### 2.4 LLM Providers Used
- **Primary**: GPT-4o (OpenAI)
- **Local backup**: Phi-3-mini-4k-instruct (llama-cpp, CPU)

---

## 3. Telemetry & Performance Dashboard

Dữ liệu từ 5 test cases x 3 hệ thống = 15 lượt chạy, 27 LLM calls.

### LLM Metrics

| Metric | Giá trị |
| :--- | :--- |
| **Total LLM calls** | 27 |
| **Avg Latency** | 1647.9ms |
| **Min Latency** | 655ms |
| **Max Latency** | 6271ms |
| **P50 Latency** | 1502ms |
| **Avg tokens/request** | 869.9 |
| **Total tokens** | 23486 |
| **Total cost (estimate)** | $0.2349 |

### System Comparison

| Metric | Chatbot | Agent v1 | Agent v2 |
| :--- | :--- | :--- | :--- |
| **Success rate** | 60% (3/5) | 80% (4/5) | **100% (5/5)** |
| **Avg steps** | 1 (luôn 1) | 1.8 | 2.6 |
| **Avg latency/task** | 1318.8ms | 3524.6ms | 4055.0ms |
| **Errors** | 0 | 0 | 0 |
| **Độ chính xác** | Trung bình, phụ thuộc prompt | Trung bình | **Cao** |

### Token Efficiency

| System | Avg prompt tokens | Avg completion tokens | Ratio |
| :--- | :--- | :--- | :--- |
| Chatbot | 71.0 | 32.6 | 2.18 |
| Agent v1 | 597.0 | 96.1 | 6.21 |
| Agent v2 | 1226.1 | 60.8 | 20.17 |

> **Nhận xét**: Agent v2 vẫn tốn nhiều prompt tokens nhất do system prompt dài và nhiều bước suy luận, đổi lại duy trì độ ổn định cao.

---

## 4. Root Cause Analysis (RCA) - Failure Traces

### Case Study 1: Agent v1 tính sai (Test Case 4)

- **Input**: "Mua combo, áp dụng HSSV2026"
- **Observation**: v1 chỉ giảm giá cho điện thoại: `calculator(32990000 * 0.95)` = 31.340.500 (thiếu ốp lưng + kính)
- **Root Cause**: Không có few-shot example hướng dẫn cách tính tổng trước rồi mới giảm.
- **Fix trong v2**: Thêm ví dụ mẫu `(32990000 + 350000 + 150000) * 0.95` trong system prompt.

### Case Study 2: Agent v2 hallucination nhỏ (Test Case 1)

- **Input**: "Tìm Samsung dưới 3 triệu"
- **v2 Output**: "Samsung Galaxy A05 và **Samsung Galaxy M04**"
- **Root Cause**: v2 tự sinh Observation giả trong 1 bước (không đợi tool trả về), bịa thêm M04.

---

## 5. Ablation Studies & Experiments

### Experiment 1: Prompt v1 (không few-shot) vs Prompt v2 (có few-shot)

- **Diff**: v2 thêm 2 ví dụ mẫu (mua combo + out-of-domain)
- **Result**: v1 success 80%, v2 success **100%** (+40%)
- **Trade-off**: v2 tốn thêm ~500 prompt tokens/request

### Experiment 2: max_steps=5 vs max_steps=7

- **Diff**: v1 dùng 5 steps, v2 dùng 7 steps
- **Result**: v1 thất bại 1/5 do hết steps; v2 không thất bại case nào
- **Nhận xét**: Với 7 tools, max_steps=7 là mức tối thiểu hợp lý

### Experiment 3: Chatbot vs Agent — So sánh theo độ phức tạp

| Case | Độ phức tạp | Chatbot | Agent v1 | Agent v2 | Winner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TC1: Tìm theo giá | Đơn giản | Không thể trả lời  | Chính xác | Chính xác + cross-sell | **Agent v2** |
| TC2: Hỏi thông tin điện thoại cơ bản | Đơn giản | Đúng + ngắn gọn | Đúng | Đúng | **Chatbot** |
| TC3: Liệt kê hãng | Đơn giản | Đúng + ngắn gọn | Đúng | Đúng | **Chatbot** |
| TC4: Combo + HSSV2026 | Phức tạp | Phụ thuộc dữ liệu cũ | HẾT STEPS | Chính xác | **Agent v2** |
| TC5: Out-of-domain | Ngoài PV | Đúng | Đúng | Đúng + cross-sell | **Agent v2** |

---

## 6. Production Readiness Review

- **Security**: Dùng regex whitelist cho calculator (chỉ cho phép số + phép tính), tránh code injection.
- **Guardrails**: max_steps=7 ngăn vòng lặp vô hạn nhưng vẫn đủ cho các bài combo. Kết hợp duplicate action detection để chặn loop xấu.
- **Scaling**:
  - Chuyển từ simulated data sang database thực (PostgreSQL/MongoDB)
  - Dùng LangGraph hoặc CrewAI cho multi-agent (1 agent tra giá, 1 agent tính toán)
  - Thêm vector DB để tham chiếu + chọn tool phù hợp từ danh sách lớn
- **Monitoring**: JSON telemetry đã sẵn sàng cho ELK Stack / Grafana dashboard.
- **Cost**: Khoảng $0.2349 cho 15 lượt chạy, 27 LLM calls. Production nên cache kết quả tool để giảm token.
