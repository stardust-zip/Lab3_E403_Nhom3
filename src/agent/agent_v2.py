import re
from typing import List, Dict, Any
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker


class ReActAgentV2:
    """
    Agent v2: Improved ReAct agent for phone shop assistant.
    Improvements over v1:
    - Few-shot examples in system prompt
    - Better action parsing (handles quotes, markdown)
    - Retry on parse errors with clearer instructions
    - Duplicate action detection (anti-loop)
    - Out-of-domain detection guidance
    """

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 7):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps

    def get_system_prompt(self) -> str:
        tool_descriptions = "\n".join(
            [f"- {t['name']}: {t['description']}" for t in self.tools]
        )
        return (
            "Ban la tro ly ban hang chuyen nghiep cua cua hang dien thoai.\n"
            "Ban co cac cong cu sau:\n"
            f"{tool_descriptions}\n\n"
            "=== DINH DANG BAT BUOC ===\n\n"
            "Thought: <suy nghi>\n"
            "Action: <tool_name>(<argument>)\n\n"
            "Sau khi nhan Observation, tiep tuc Thought/Action,\n"
            "HOAC tra loi khach hang:\n\n"
            "Thought: <suy nghi>\n"
            "Final Answer: <tra loi day du>\n\n"
            "=== QUY TAC ===\n"
            "1. LUON bat dau bang Thought.\n"
            "2. Moi buoc CHI 1 Action. Khong goi 2 tool cung luc.\n"
            "3. Format: tool_name(argument) — KHONG them dau ngoac kep quanh ten tool.\n"
            "4. DOI Observation truoc khi tiep tuc.\n"
            "5. Dung 'Final Answer:' KHI VA CHI KHI da du thong tin.\n"
            "6. KHONG bai dat gia, so luong. PHAI dung tool de tra cuu.\n"
            "7. Voi calculator, truyen bieu thuc thuan toan: calculator(32990000 * 0.95)\n"
            "8. Neu cau hoi NGOAI PHAM VI (khong ve dien thoai/phu kien), "
            "tra loi ngay bang Final Answer: rang cua hang chi ho tro dien thoai va phu kien.\n\n"
            "=== VD 1: Mua dien thoai + phu kien + khuyen mai ===\n"
            "Khach hang hoi: Mua iPhone 17 Pro + op lung + kinh cuong luc, ap dung ma HSSV2026 het bao nhieu?\n\n"
            "Thought: Can tra gia iPhone 17 Pro truoc.\n"
            "Action: check_stock(iphone 17 pro)\n\n"
            "Observation: Iphone 17 Pro: 32,990,000d, con 18 san pham (dien thoai)\n\n"
            "Thought: Tiep theo can gia op lung.\n"
            "Action: check_stock(op lung iphone 17 pro)\n\n"
            "Observation: Op Lung Iphone 17 Pro: 350,000d, con 50 sp\n\n"
            "Thought: Can gia kinh cuong luc.\n"
            "Action: check_stock(kinh cuong luc iphone 17 pro)\n\n"
            "Observation: Kinh Cuong Luc Iphone 17 Pro: 150,000d, con 100 sp\n\n"
            "Thought: Tong truoc giam = 32990000 + 350000 + 150000. Can tra ma HSSV2026.\n"
            "Action: get_discount(HSSV2026)\n\n"
            "Observation: Ma 'HSSV2026': Khuyen mai Hoc sinh - Sinh vien 2026 - Giam 5%.\n\n"
            "Thought: Tinh tong: (32990000 + 350000 + 150000) * 0.95\n"
            "Action: calculator((32990000 + 350000 + 150000) * 0.95)\n\n"
            "Observation: 31.815.500\n\n"
            "Thought: Da du thong tin.\n"
            "Final Answer: iPhone 17 Pro (32.990.000d) + Op lung (350.000d) + Kinh cuong luc (150.000d) = 33.490.000d. Ap dung ma HSSV2026 giam 5%, thanh toan: 31.815.500d.\n\n"
            "=== VD 2: Cau hoi ngoai pham vi ===\n"
            "Khach hang hoi: Cua hang co ban laptop khong?\n\n"
            "Thought: Day la cau hoi ngoai pham vi, cua hang chi ban dien thoai va phu kien.\n"
            "Final Answer: Xin loi, cua hang chung toi hien chi kinh doanh dien thoai va phu kien dien thoai. Chung toi khong ban laptop. Quy khach co can tu van ve dien thoai khong a?\n"
        )

    def run(self, user_input: str) -> str:
        logger.log_event("AGENT_V2_START", {
            "input": user_input,
            "model": self.llm.model_name,
            "max_steps": self.max_steps,
        })

        prompt_history = f"Khach hang hoi: {user_input}\n"
        steps = 0
        errors = []
        parse_retries = 0
        previous_actions = []

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
                "version": "v2",
                "llm_output": content,
                "latency_ms": latency,
                "tokens": usage,
            })

            # Check Final Answer
            final_match = re.search(r"Final Answer:\s*(.+)", content, re.DOTALL)
            if final_match:
                answer = final_match.group(1).strip()
                logger.log_event("AGENT_V2_END", {
                    "status": "success",
                    "steps": steps,
                    "answer": answer,
                    "errors": errors,
                })
                return answer

            # Parse Action — multiple patterns for robustness
            action_match = (
                re.search(r"Action:\s*(\w+)\((.+?)\)", content)
                or re.search(r"Action:\s*(\w+)\((.+)\)", content)
                or re.search(r"Action:\s*`(\w+)\((.+?)\)`", content)
            )

            if not action_match:
                parse_retries += 1
                error_msg = f"PARSE_ERROR (lan {parse_retries}): Khong doc duoc Action."
                errors.append({"step": steps, "error": error_msg})
                logger.log_event("AGENT_ERROR", {"step": steps, "error": error_msg, "raw": content})

                if parse_retries >= 2:
                    prompt_history += (
                        f"{content}\n"
                        "Observation: LOI — Da 2 lan khong doc duoc Action. "
                        "Ban PHAI tra loi ngay bang Final Answer voi thong tin hien co.\n"
                    )
                else:
                    prompt_history += (
                        f"{content}\n"
                        "Observation: LOI — Khong doc duoc Action. "
                        "Dung format: Action: tool_name(argument). Thu lai.\n"
                    )
                continue

            tool_name = action_match.group(1)
            tool_args = action_match.group(2).strip().strip("'\"")
            current_action = f"{tool_name}({tool_args})"

            # Detect duplicate action (anti-loop)
            if current_action in previous_actions:
                logger.log_event("AGENT_ERROR", {
                    "step": steps,
                    "error": "DUPLICATE_ACTION",
                    "action": current_action,
                })
                prompt_history += (
                    f"{content}\n"
                    f"Observation: Ban da goi {current_action} truoc do roi. "
                    "Hay dung thong tin da co de tra loi Final Answer.\n"
                )
                continue

            previous_actions.append(current_action)

            observation = self._execute_tool(tool_name, tool_args)

            logger.log_event("TOOL_CALL", {
                "step": steps,
                "version": "v2",
                "tool": tool_name,
                "args": tool_args,
                "result": observation,
            })

            prompt_history += f"{content}\nObservation: {observation}\n"

        logger.log_event("AGENT_V2_END", {
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
