"""
Run 5 structured test cases through Chatbot, Agent v1, and Agent v2.
Scenario: Phone shop assistant (Vietnamese context).

Test Cases:
  1. Tim dien thoai theo gia          — search_by_price
  2. Mua nhieu mon + hoi khuyen mai   — check_stock + list_promotions (thieu thong tin ma KM)
  3. Hoi cac hang dien thoai           — list_brands
  4. Mua combo + ap dung ma KM cu the  — check_stock x3 + get_discount + calculator
  5. Hoi ngoai domain (laptop)         — out-of-domain, agent nen tu choi lich su
"""

import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()

# Fix encoding for Windows console
sys.stdout.reconfigure(encoding="utf-8")

TEST_CASES = [
    {
        "id": 1,
        "name": "Tìm điện thoại theo giá",
        "description": "Khách tìm điện thoại Samsung dưới 3 triệu — cần dùng search_by_price hoặc search_by_brand",
        "query": "Tìm giúp tôi điện thoại Samsung dưới 3 triệu",
        "expected": "Agent dùng search_by_price(3000000) hoặc search_by_brand(Samsung). Kết quả: Samsung Galaxy A05 (2.490.000đ).",
    },
    {
        "id": 2,
        "name": "Hỏi thông tin điện thoại",
        "description": "Câu hỏi đơn giản - thông tin có sẵn",
        "query": "Điện thoại iPhone của hãng nào?",
        "expected": "Apple.",
    },
    {
        "id": 3,
        "name": "Hỏi các hãng điện thoại",
        "description": "Câu hỏi đơn giản - thông tin có sẵn",
        "query": "Liệt kê 3 hãng điện thoại phổ biến ở Việt Nam",
        "expected": "Samsung, Apple, Xiaomi (hoac Oppo).",
    },
    {
        "id": 4,
        "name": "Mua combo + áp dụng mã KM cụ thể",
        "description": "Multi-step phức tạp: check_stock x3 + get_discount + calculator",
        "query": "Tôi muốn mua điện thoại iPhone 17 Pro + ốp lưng + kính cường lực, nếu áp dụng khuyến mãi HSSV2026 thì hết bao nhiêu tiền?",
        "expected": "Agent tra giá 3 món (32.990.000 + 350.000 + 150.000), tra mã HSSV2026 (giảm 5%), tính tổng: 31.815.500đ.",
    },
    {
        "id": 5,
        "name": "Out-of-domain: hỏi mua laptop",
        "description": "Câu hỏi ngoài phạm vi — cửa hàng chỉ bán điện thoại",
        "query": "Cửa hàng có nhận thu mua laptop không?",
        "expected": "Agent/Chatbot từ chối lịch sự. Agent v2 nên nhận biết ngay và trả lời Final Answer không cần gọi tool.",
    },
]


def create_provider():
    provider_type = os.getenv("DEFAULT_PROVIDER", "local")
    if provider_type == "openai":
        from src.core.openai_provider import OpenAIProvider
        return OpenAIProvider(model_name=os.getenv("DEFAULT_MODEL", "gpt-4o"), api_key=os.getenv("OPENAI_API_KEY"))
    elif provider_type == "google":
        from src.core.gemini_provider import GeminiProvider
        return GeminiProvider(model_name=os.getenv("DEFAULT_MODEL", "gemini-1.5-flash"), api_key=os.getenv("GEMINI_API_KEY"))
    else:
        from src.core.local_provider import LocalProvider
        return LocalProvider(model_path=os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf"))


def run_all():
    from src.chatbot.chatbot import Chatbot
    from src.agent.agent import ReActAgent
    from src.agent.agent_v2 import ReActAgentV2
    from src.tools import TOOLS
    from src.telemetry.logger import logger

    print("Loading LLM provider...")
    llm = create_provider()
    print(f"Provider loaded: {llm.model_name}\n")

    chatbot = Chatbot(llm)
    agent_v1 = ReActAgent(llm, TOOLS, max_steps=5)
    agent_v2 = ReActAgentV2(llm, TOOLS, max_steps=7)

    results = []

    for tc in TEST_CASES:
        print("=" * 70)
        print(f"  TEST CASE {tc['id']}: {tc['name']}")
        print(f"  Mo ta: {tc['description']}")
        print(f"  Cau hoi: \"{tc['query']}\"")
        print(f"  Ky vong: {tc['expected']}")
        print("-" * 70)

        logger.log_event("TEST_CASE_START", {"id": tc["id"], "name": tc["name"], "query": tc["query"]})

        case = {"id": tc["id"], "name": tc["name"], "query": tc["query"]}

        # Chatbot
        print("\n  [CHATBOT]")
        try:
            ans = chatbot.chat(tc["query"])
            print(f"  >>> {ans[:500]}")
            case["chatbot"] = ans
        except Exception as e:
            print(f"  ERROR: {e}")
            case["chatbot"] = f"ERROR: {e}"

        # Agent v1
        print("\n  [AGENT v1]")
        try:
            ans = agent_v1.run(tc["query"])
            print(f"  >>> {ans[:500]}")
            case["agent_v1"] = ans
        except Exception as e:
            print(f"  ERROR: {e}")
            case["agent_v1"] = f"ERROR: {e}"

        # Agent v2
        print("\n  [AGENT v2]")
        try:
            ans = agent_v2.run(tc["query"])
            print(f"  >>> {ans[:500]}")
            case["agent_v2"] = ans
        except Exception as e:
            print(f"  ERROR: {e}")
            case["agent_v2"] = f"ERROR: {e}"

        logger.log_event("TEST_CASE_END", {"id": tc["id"], "name": tc["name"]})
        results.append(case)
        print()

    # Save results
    os.makedirs("logs", exist_ok=True)
    with open("logs/test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("=" * 70)
    print("  HOAN THANH — Tat ca 5 test cases da chay xong.")
    print("  Logs:    logs/2026-04-06.log")
    print("  Results: logs/test_results.json")
    print("  Chay 'python evaluate.py' de phan tich hieu nang.")
    print("=" * 70)


if __name__ == "__main__":
    run_all()
