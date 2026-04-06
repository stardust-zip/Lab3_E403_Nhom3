import re
from typing import List, Dict, Any
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker


class ReActAgent:
    """
    Agent v1: ReAct-style Agent for phone shop assistant.
    Basic Thought-Action-Observation loop.
    """

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps

    def get_system_prompt(self) -> str:
        tool_descriptions = "\n".join(
            [f"- {t['name']}: {t['description']}" for t in self.tools]
        )
        return (
            "Ban la tro ly ban hang cua mot cua hang dien thoai.\n"
            "Ban co cac cong cu sau:\n"
            f"{tool_descriptions}\n\n"
            "Ban PHAI dung dinh dang sau cho moi buoc:\n\n"
            "Thought: <suy nghi ve buoc tiep theo>\n"
            "Action: <tool_name>(<argument>)\n\n"
            "HOAC neu da du thong tin:\n\n"
            "Thought: <suy nghi>\n"
            "Final Answer: <cau tra loi day du cho khach hang>\n\n"
            "Quy tac:\n"
            "1. Luon bat dau bang Thought.\n"
            "2. Moi buoc chi dung 1 Action duy nhat.\n"
            "3. Format Action: tool_name(argument) — khong them dau ngoac kep quanh ten tool.\n"
            "4. Doi Observation truoc khi tiep tuc.\n"
            "5. Khi da du thong tin, dung 'Final Answer:' de tra loi.\n"
            "6. Khong bai dat thong tin. Dung tool de tra cuu.\n"
            "7. Neu cau hoi ngoai pham vi (khong lien quan dien thoai/phu kien), "
            "tra loi lich su rang cua hang chi ho tro ve dien thoai va phu kien.\n"
        )

    def run(self, user_input: str) -> str:
        logger.log_event("AGENT_V1_START", {
            "input": user_input,
            "model": self.llm.model_name,
            "max_steps": self.max_steps,
        })

        prompt_history = f"Khach hang hoi: {user_input}\n"
        steps = 0
        errors = []

        while steps < self.max_steps:
            steps += 1

            result = self.llm.generate(prompt_history, system_prompt=self.get_system_prompt())
            content = result.get("content", "")
            usage = result.get("usage", {})
            latency = result.get("latency_ms", 0)

            tracker.track_request(
                provider=result.get("provider", "unknown"),
                model=self.llm.model_name,
                usage=usage,
                latency_ms=latency,
            )

            logger.log_event("AGENT_STEP", {
                "step": steps,
                "version": "v1",
                "llm_output": content,
                "latency_ms": latency,
                "tokens": usage,
            })

            # Check Final Answer
            final_match = re.search(r"Final Answer:\s*(.+)", content, re.DOTALL)
            if final_match:
                answer = final_match.group(1).strip()
                logger.log_event("AGENT_V1_END", {
                    "status": "success",
                    "steps": steps,
                    "answer": answer,
                    "errors": errors,
                })
                return answer

            # Parse Action
            action_match = re.search(r"Action:\s*(\w+)\((.+?)\)", content)
            if not action_match:
                error_msg = "PARSE_ERROR: Khong the doc Action tu output."
                errors.append({"step": steps, "error": error_msg})
                logger.log_event("AGENT_ERROR", {"step": steps, "error": error_msg, "raw": content})
                prompt_history += f"{content}\nObservation: Loi — Khong doc duoc Action. Hay dung format: Action: tool_name(argument)\n"
                continue

            tool_name = action_match.group(1)
            tool_args = action_match.group(2).strip()

            observation = self._execute_tool(tool_name, tool_args)

            logger.log_event("TOOL_CALL", {
                "step": steps,
                "version": "v1",
                "tool": tool_name,
                "args": tool_args,
                "result": observation,
            })

            prompt_history += f"{content}\nObservation: {observation}\n"

        logger.log_event("AGENT_V1_END", {
            "status": "max_steps_exceeded",
            "steps": steps,
            "errors": errors,
        })
        return "Xin loi, toi khong the tra loi trong so buoc cho phep. Vui long thu lai voi cau hoi ngan gon hon."

    def _execute_tool(self, tool_name: str, args: str) -> str:
        for tool in self.tools:
            if tool["name"] == tool_name:
                try:
                    return tool["func"](args)
                except Exception as e:
                    return f"Loi khi goi {tool_name}: {e}"
        available = ", ".join(t["name"] for t in self.tools)
        return f"HALLUCINATION_ERROR: Tool '{tool_name}' khong ton tai. Cac tool co san: {available}"
