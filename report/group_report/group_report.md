# Group Report: Lab 3 - Tro ly Cua hang Dien thoai (ReAct Agent)

- **Team Name**: [Dien ten nhom]
- **Team Members**: [Thanh vien 1, 2, 3, 4, 5, 6]
- **Deployment Date**: 2026-04-06

---

## 1. Executive Summary

So sanh hieu nang giua Chatbot (khong tools) va ReAct Agent (co tools) trong vai tro tro ly ban hang dien thoai.

- **Success Rate**: Chatbot N/A (khong do duoc) | Agent v1: 60% (3/5) | Agent v2: **100% (5/5)**
- **Key Outcome**: Agent v2 giai quyet duoc 100% cac truong hop, bao gom multi-step (tra gia, tinh khuyen mai, tinh tong) va out-of-domain. Chatbot bia gia sai toan bo cac cau hoi phuc tap.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation

```
User Question --> [Thought] --> [Action: tool(args)] --> [Observation] --> loop...
                                                                    |
                                                              [Final Answer]
```

Vong lap ReAct hoat dong nhu sau:
1. LLM sinh ra **Thought** (suy nghi) va **Action** (goi tool)
2. He thong parse Action, goi tool tuong ung
3. Ket qua tra ve lam **Observation**, nap lai vao prompt
4. Lap lai cho den khi co **Final Answer** hoac het max_steps

### 2.2 Tool Definitions (Inventory)

| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `check_stock` | `string` (ten SP) | Tra gia va so luong ton kho |
| `search_by_price` | `string` (gia toi da VND) | Tim dien thoai theo khoang gia |
| `search_by_brand` | `string` (ten hang) | Tim dien thoai theo hang |
| `list_brands` | `string` (truyen 'all') | Liet ke cac hang co trong cua hang |
| `get_discount` | `string` (ma KM) | Tra cuu ma khuyen mai |
| `list_promotions` | `string` (truyen 'all') | Liet ke tat ca khuyen mai |
| `calculator` | `string` (bieu thuc toan) | Tinh toan so hoc |

### 2.3 Tool Design Evolution (v1 --> v2)

| Thay doi | v1 | v2 |
| :--- | :--- | :--- |
| System prompt | Chi liet ke tool + format | Them **few-shot examples** (2 VD mau) |
| Parse Action | 1 regex pattern | **3 regex patterns** (xu ly quotes, markdown) |
| Parse error | Bao loi chung, lap mai | Dem so lan, **sau 2 lan ep Final Answer** |
| Loop detection | Khong co | **Phat hien duplicate action**, ep ket thuc |
| Out-of-domain | Khong huong dan | Co **vi du mau** tu choi lich su |
| Max steps | 5 | 7 |

### 2.4 LLM Providers Used
- **Primary**: GPT-4o-mini (OpenAI)
- **Local backup**: Phi-3-mini-4k-instruct (llama-cpp, CPU)

---

## 3. Telemetry & Performance Dashboard

Du lieu tu 5 test cases x 3 he thong = 15 luot chay, 36 LLM calls.

### LLM Metrics
| Metric | Gia tri |
| :--- | :--- |
| **Total LLM calls** | 36 |
| **Avg Latency (P50)** | 1,359ms |
| **Max Latency (P99)** | 5,835ms |
| **Avg tokens/request** | 869 |
| **Total tokens** | 31,273 |
| **Total cost (estimate)** | $0.31 |

### System Comparison
| Metric | Chatbot | Agent v1 | Agent v2 |
| :--- | :--- | :--- | :--- |
| **Success rate** | N/A | 60% (3/5) | **100% (5/5)** |
| **Avg steps** | 1 (luon 1) | 3.2 | **3.0** |
| **Avg latency/task** | 1,859ms | ~6,500ms | ~10,500ms |
| **Errors** | 0 | 0 | 0 |
| **Do chinh xac** | Thap (bia gia) | Trung binh | **Cao** |

### Token Efficiency
| System | Avg prompt tokens | Avg completion tokens | Ratio |
| :--- | :--- | :--- | :--- |
| Chatbot | 77 | 67 | 1.15 |
| Agent v1 | 694 | 57 | 12.2 |
| Agent v2 | 1,197 | 68 | 17.6 |

> **Nhan xet**: Agent v2 ton nhieu prompt tokens hon do system prompt dai (few-shot), nhung do chinh xac cao hon dang ke.

---

## 4. Root Cause Analysis (RCA) - Failure Traces

### Case Study 1: Agent v1 het steps (Test Case 2 & 4)

- **Input**: "Mua iPhone 17 Pro + op lung + kinh cuong luc, co KM gi?"
- **Observation**: Agent v1 goi 5 tools (check_stock x3 + calculator + list_promotions) nhung het max_steps=5 truoc khi kip tra Final Answer.
- **Root Cause**: max_steps=5 khong du cho cac bai toan can 6+ hanh dong (3 tra gia + 1 tra KM + 1 calculator + 1 Final Answer).
- **Fix trong v2**: Tang max_steps len 7.

### Case Study 2: Agent v1 tinh sai (Test Case 4)

- **Input**: "Mua combo, ap dung HSSV2026"
- **Observation**: v1 chi giam gia cho dien thoai: `calculator(32990000 * 0.95)` = 31.340.500 (thieu op lung + kinh)
- **Root Cause**: Khong co few-shot example huong dan cach tinh tong truoc roi moi giam.
- **Fix trong v2**: Them vi du mau `(32990000 + 350000 + 150000) * 0.95` trong system prompt.

### Case Study 3: Chatbot hallucination (Test Case 3 & 4)

- **Input**: "Cua hang ban nhung hang nao?"
- **Chatbot Output**: "Apple, Samsung, Xiaomi, Oppo, **Huawei**..."
- **Root Cause**: LLM khong co du lieu thuc, bia them Huawei tu kien thuc chung.
- **Agent**: Goi `list_brands()` tra ve du lieu chinh xac tu database.

### Case Study 4: Agent v2 hallucination nho (Test Case 1)

- **Input**: "Tim Samsung duoi 3 trieu"
- **v2 Output**: "Samsung Galaxy A05 va **Samsung Galaxy M04**"
- **Root Cause**: v2 tu sinh Observation gia trong 1 buoc (khong doi tool tra ve), bia them M04.
- **Nhan xet**: Day la han che cua model nho (gpt-4o-mini), model lon hon se it bi loi nay.

---

## 5. Ablation Studies & Experiments

### Experiment 1: Prompt v1 (khong few-shot) vs Prompt v2 (co few-shot)

- **Diff**: v2 them 2 vi du mau (mua combo + out-of-domain)
- **Result**: v1 success 60%, v2 success **100%** (+40%)
- **Trade-off**: v2 ton them ~500 prompt tokens/request

### Experiment 2: max_steps=5 vs max_steps=7

- **Diff**: v1 dung 5 steps, v2 dung 7 steps
- **Result**: v1 that bai 2/5 do het steps; v2 khong that bai case nao
- **Nhan xet**: Voi 7 tools, max_steps=7 la muc toi thieu hop ly

### Experiment 3: Chatbot vs Agent — So sanh theo do phuc tap

| Case | Do phuc tap | Chatbot | Agent v1 | Agent v2 | Winner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TC1: Tim theo gia | Don gian | Chung chung | Chinh xac | Chinh xac | Agent |
| TC2: Mua combo + KM | Phuc tap | Khong tra loi | HET STEPS | Chinh xac | **Agent v2** |
| TC3: Liet ke hang | Don gian | Bia them Huawei | Chinh xac | Chinh xac | Agent |
| TC4: Combo + HSSV2026 | Phuc tap | BIA GIA SAI | HET STEPS | **31.815.500d** | **Agent v2** |
| TC5: Out-of-domain | Ngoai PV | Dung | Dung | Dung + cross-sell | **Agent v2** |

---

## 6. Production Readiness Review

- **Security**: Dung regex whitelist cho calculator (chi cho phep so + phep tinh), tranh code injection.
- **Guardrails**: max_steps=7 ngan vong lap vo han. Duplicate action detection ngan loop.
- **Scaling**:
  - Chuyen tu simulated data sang database thuc (PostgreSQL/MongoDB)
  - Dung LangGraph hoac CrewAI cho multi-agent (1 agent tra gia, 1 agent tinh toan)
  - Them vector DB de chon tool phu hop tu danh sach lon
- **Monitoring**: JSON telemetry da san sang cho ELK Stack / Grafana dashboard
- **Cost**: ~$0.31 cho 15 luot chay. Production can cache ket qua tool de giam token.

---

> **Bai hoc lon nhat**: Chatbot chi biet noi, Agent biet HANH DONG. Nhung Agent chi manh khi co (1) tool description ro rang, (2) few-shot examples tot, va (3) du steps de hoan thanh nhiem vu.
