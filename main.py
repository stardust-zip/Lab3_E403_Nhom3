"""
Lab 3: Chatbot vs ReAct Agent — Tro ly cua hang dien thoai

Usage:
    python main.py chatbot     — Chay chatbot don gian (khong co tools)
    python main.py agent-v1    — Chay Agent v1 (ReAct loop co ban)
    python main.py agent-v2    — Chay Agent v2 (ReAct loop cai tien)
    python main.py compare     — So sanh ca 3 tren cac test cases
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.stdout.reconfigure(encoding="utf-8")


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


def run_chatbot(llm):
    from src.chatbot.chatbot import Chatbot
    bot = Chatbot(llm)
    print("=== Chatbot — Tro ly cua hang (type 'quit' de thoat) ===\n")
    while True:
        user_input = input("Khach: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            break
        response = bot.chat(user_input)
        print(f"Bot: {response}\n")


def run_agent(llm, version="v1"):
    from src.tools import TOOLS
    if version == "v2":
        from src.agent.agent_v2 import ReActAgentV2
        agent = ReActAgentV2(llm, TOOLS)
        print("=== Agent v2 — ReAct cai tien (type 'quit' de thoat) ===\n")
    else:
        from src.agent.agent import ReActAgent
        agent = ReActAgent(llm, TOOLS)
        print("=== Agent v1 — ReAct co ban (type 'quit' de thoat) ===\n")
    while True:
        user_input = input("Khach: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            break
        response = agent.run(user_input)
        print(f"Agent: {response}\n")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    mode = sys.argv[1].lower()
    print(f"Dang tai LLM provider ({os.getenv('DEFAULT_PROVIDER', 'local')})...")
    llm = create_provider()
    print("Provider loaded.\n")

    if mode == "chatbot":
        run_chatbot(llm)
    elif mode == "agent-v1":
        run_agent(llm, "v1")
    elif mode == "agent-v2":
        run_agent(llm, "v2")
    else:
        print(f"Unknown mode: {mode}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()