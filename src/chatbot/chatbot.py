from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker


class Chatbot:
    """
    Simple chatbot baseline — no tools, no reasoning loop.
    Just sends user input to LLM and returns response.
    Used to compare against ReAct Agent.
    """

    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def get_system_prompt(self) -> str:
        return (
            "Ban la tro ly ban hang cua mot cua hang dien thoai. "
            "Tra loi cau hoi cua khach hang mot cach ngan gon va lich su. "
            "Neu khong biet cau tra loi, hay noi that."
        )

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