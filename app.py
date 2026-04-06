"""
Lab 3: Giao dien so sanh Chatbot vs ReAct Agent
Run: streamlit run app.py
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

import streamlit as st

# --- Page config ---
st.set_page_config(
    page_title="Chatbot vs ReAct Agent",
    page_icon="🤖",
    layout="wide",
)

# --- Custom CSS ---
st.markdown("""
<style>
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 15px;
        font-size: 15px;
        line-height: 1.6;
    }
    .fail-box {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 8px;
        padding: 15px;
        font-size: 15px;
    }
    .trace-step {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 8px 12px;
        margin: 5px 0;
        border-radius: 0 6px 6px 0;
        font-family: monospace;
        font-size: 13px;
    }
    .tool-call {
        background: #d1ecf1;
        border-left: 4px solid #17a2b8;
        padding: 8px 12px;
        margin: 5px 0;
        border-radius: 0 6px 6px 0;
        font-family: monospace;
        font-size: 13px;
    }
    .metric-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        border: 1px solid #e0e0e0;
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-label {
        font-size: 13px;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)


# --- Cache provider ---
@st.cache_resource
def load_provider():
    provider_type = os.getenv("DEFAULT_PROVIDER", "local")
    if provider_type == "openai":
        from src.core.openai_provider import OpenAIProvider
        return OpenAIProvider(
            model_name=os.getenv("DEFAULT_MODEL", "gpt-4o-mini"),
            api_key=os.getenv("OPENAI_API_KEY"),
        )
    elif provider_type == "google":
        from src.core.gemini_provider import GeminiProvider
        return GeminiProvider(
            model_name=os.getenv("DEFAULT_MODEL", "gemini-1.5-flash"),
            api_key=os.getenv("GEMINI_API_KEY"),
        )
    else:
        from src.core.local_provider import LocalProvider
        return LocalProvider(
            model_path=os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")
        )


def get_systems(llm):
    from src.chatbot.chatbot import Chatbot
    from src.agent.agent_v2 import ReActAgentV2
    from src.tools import TOOLS

    return {
        "chatbot": Chatbot(llm),
        "agent_v2": ReActAgentV2(llm, TOOLS, max_steps=7),
    }


def run_single(system, system_type, query):
    """Run a query and return answer."""
    if system_type == "chatbot":
        answer = system.chat(query)
    else:
        answer = system.run(query)
    return {"answer": answer}


def count_log_lines(log_path):
    """Count current number of lines in log file."""
    if not os.path.exists(log_path):
        return 0
    with open(log_path, "r", encoding="utf-8") as f:
        return sum(1 for _ in f)


def collect_trace_events(log_path, skip_lines):
    """Read only NEW log events after skip_lines."""
    events = []
    if not os.path.exists(log_path):
        return events
    with open(log_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i < skip_lines:
                continue
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def parse_trace_for_display(events):
    """Extract step-by-step trace for display (with deduplication)."""
    steps = []
    seen = set()
    for ev in events:
        event_type = ev.get("event", "")
        data = ev.get("data", {})

        if event_type == "AGENT_STEP" and data.get("version") == "v2":
            key = ("llm", data.get("step", 0), data.get("llm_output", ""))
            if key in seen:
                continue
            seen.add(key)
            steps.append({
                "type": "llm",
                "step": data.get("step", 0),
                "output": data.get("llm_output", ""),
                "latency": data.get("latency_ms", 0),
                "tokens": data.get("tokens", {}),
            })
        elif event_type == "TOOL_CALL" and data.get("version") == "v2":
            key = ("tool", data.get("tool", ""), data.get("args", ""), data.get("result", ""))
            if key in seen:
                continue
            seen.add(key)
            steps.append({
                "type": "tool",
                "tool": data.get("tool", ""),
                "args": data.get("args", ""),
                "result": data.get("result", ""),
            })
        elif event_type == "AGENT_ERROR":
            key = ("error", data.get("error", ""))
            if key in seen:
                continue
            seen.add(key)
            steps.append({
                "type": "error",
                "error": data.get("error", ""),
            })
    return steps


def render_metric_card(label, value, color="#1f77b4"):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: {color}">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def render_trace(steps):
    if not steps:
        st.info("Khong co trace")
        return
    for s in steps:
        if s["type"] == "llm":
            st.markdown(f"""<div class="trace-step">
<b>Step {s['step']}</b><br>
{s['output'].replace(chr(10), '<br>')}
</div>""", unsafe_allow_html=True)
        elif s["type"] == "tool":
            st.markdown(f"""<div class="tool-call">
<b>Tool:</b> {s['tool']}({s['args']})<br>
<b>Result:</b> {s['result']}
</div>""", unsafe_allow_html=True)
        elif s["type"] == "error":
            st.error(f"Error: {s['error']}")


def load_test_results():
    path = "logs/test_results.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def load_log_events():
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_path = os.path.join("logs", f"{date_str}.log")
    if not os.path.exists(log_path):
        return []
    events = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                events.append(json.loads(line.strip()))
            except (json.JSONDecodeError, ValueError):
                continue
    return events


# ==================== MAIN APP ====================

st.title("Chatbot vs ReAct Agent")
st.caption("Lab 3 — So sanh Chatbot va ReAct Agent trong vai tro tro ly cua hang dien thoai")

# Sidebar
with st.sidebar:
    st.header("Cau hinh")
    provider = os.getenv("DEFAULT_PROVIDER", "local")
    model = os.getenv("DEFAULT_MODEL", "unknown")
    st.info(f"**Provider:** {provider}\n\n**Model:** {model}")

    st.divider()
    st.subheader("Test cases mau")
    sample_queries = [
        "Tim giup toi dien thoai Samsung duoi 3 trieu",
        "Mua dien thoai iPhone 17 Pro + op lung + kinh cuong luc het bao nhieu tien, co khuyen mai gi khi mua nhieu khong?",
        "Cua hang co ban dien thoai cua nhung hang nao?",
        "Toi muon mua dien thoai iPhone 17 Pro + op lung + kinh cuong luc, neu ap dung khuyen mai HSSV2026 thi het bao nhieu tien?",
        "Cua hang co nhan thu mua laptop khong?",
    ]
    selected_sample = st.selectbox(
        "Chon cau hoi mau:",
        ["-- Chon --"] + [f"TC{i+1}: {q[:50]}..." for i, q in enumerate(sample_queries)],
    )

tab1, tab2, tab3 = st.tabs(["So sanh truc tiep", "Ket qua test cases", "Phan tich Telemetry"])

# ==================== TAB 1: Live comparison ====================
with tab1:
    st.subheader("Nhap cau hoi de so sanh Chatbot va ReAct Agent")

    # Auto-fill from sidebar selection
    default_query = ""
    if selected_sample and selected_sample != "-- Chon --":
        idx = int(selected_sample.split(":")[0].replace("TC", "")) - 1
        default_query = sample_queries[idx]

    query = st.text_area(
        "Cau hoi cua khach hang:",
        value=default_query,
        height=80,
        placeholder="VD: Toi muon mua iPhone 17 Pro, co khuyen mai gi khong?",
    )

    run_clicked = st.button("Chay so sanh", type="primary")

    if run_clicked and query.strip():
        llm = load_provider()
        systems = get_systems(llm)

        log_path = os.path.join("logs", f"{datetime.now().strftime('%Y-%m-%d')}.log")
        lines_before = count_log_lines(log_path)

        results = {}

        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("### Chatbot")
            with st.spinner("Dang xu ly..."):
                results["chatbot"] = run_single(systems["chatbot"], "chatbot", query.strip())

        with col_right:
            st.markdown("### ReAct Agent")
            with st.spinner("Dang xu ly..."):
                results["agent_v2"] = run_single(systems["agent_v2"], "agent_v2", query.strip())

        # Show results
        st.divider()
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("### Chatbot")
            ans = results["chatbot"]["answer"]
            st.markdown(f'<div class="success-box">{ans}</div>', unsafe_allow_html=True)

        with col_right:
            st.markdown("### ReAct Agent")
            ans = results["agent_v2"]["answer"]
            if "khong the tra loi" in ans.lower():
                st.markdown(f'<div class="fail-box">{ans}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="success-box">{ans}</div>', unsafe_allow_html=True)

            with st.expander("Xem trace chi tiet (Thought -> Action -> Observation)"):
                events = collect_trace_events(log_path, lines_before)
                steps = parse_trace_for_display(events)
                render_trace(steps)

# ==================== TAB 2: Test case results ====================
with tab2:
    st.subheader("Ket qua 5 test cases")

    test_results = load_test_results()
    if test_results is None:
        st.warning("Chua co ket qua. Chay `python run_test_cases.py` truoc.")
    else:
        for tc in test_results:
            with st.expander(f"Test Case {tc['id']}: {tc['name']}", expanded=False):
                st.markdown(f"**Cau hoi:** {tc['query']}")
                st.divider()

                col_left, col_right = st.columns(2)
                with col_left:
                    st.markdown("**Chatbot**")
                    answer = tc.get("chatbot", "N/A")
                    if isinstance(answer, str) and len(answer) > 0:
                        st.success(answer[:500])
                    else:
                        st.info("Khong co ket qua")

                with col_right:
                    st.markdown("**ReAct Agent**")
                    answer = tc.get("agent_v2", "N/A")
                    if isinstance(answer, str) and len(answer) > 0:
                        is_fail = "khong the tra loi" in answer.lower() or "ERROR" in answer
                        if is_fail:
                            st.error(answer[:500])
                        else:
                            st.success(answer[:500])
                    else:
                        st.info("Khong co ket qua")

        # Summary table
        st.divider()
        st.subheader("Bang tong hop")

        table_data = []
        for tc in test_results:
            row = {"Test Case": f"TC{tc['id']}: {tc['name']}"}
            for key, label in [("chatbot", "Chatbot"), ("agent_v2", "ReAct Agent")]:
                ans = tc.get(key, "N/A")
                if isinstance(ans, str):
                    is_fail = "khong the tra loi" in ans.lower() or "ERROR" in ans
                    row[label] = "FAIL" if is_fail else "OK"
                else:
                    row[label] = "N/A"
            table_data.append(row)

        st.table(table_data)

# ==================== TAB 3: Telemetry analysis ====================
with tab3:
    st.subheader("Phan tich Telemetry tu Logs")

    events = load_log_events()
    if not events:
        st.warning("Chua co logs. Chay test cases truoc.")
    else:
        st.info(f"Loaded {len(events)} events tu logs")

        # LLM Metrics
        metrics = [e["data"] for e in events if e.get("event") == "LLM_METRIC"]
        if metrics:
            st.markdown("### Hieu nang LLM")
            cols = st.columns(4)
            latencies = [m["latency_ms"] for m in metrics]
            total_tokens = [m.get("total_tokens", 0) for m in metrics]
            costs = [m.get("cost_estimate", 0) for m in metrics]

            with cols[0]:
                render_metric_card("Tong LLM calls", str(len(metrics)))
            with cols[1]:
                render_metric_card("Avg Latency", f"{sum(latencies)//len(latencies)}ms")
            with cols[2]:
                render_metric_card("Tong Tokens", f"{sum(total_tokens):,}")
            with cols[3]:
                render_metric_card("Tong Chi phi", f"${sum(costs):.4f}")

            # Latency chart
            st.markdown("### Latency theo tung request")
            st.bar_chart({"Latency (ms)": latencies})

            # Token chart
            st.markdown("### Token usage theo tung request")
            prompt_tokens = [m.get("prompt_tokens", 0) for m in metrics]
            completion_tokens = [m.get("completion_tokens", 0) for m in metrics]
            st.bar_chart({"Prompt Tokens": prompt_tokens, "Completion Tokens": completion_tokens})

        # Agent comparison
        st.markdown("### So sanh Chatbot vs ReAct Agent")

        chatbot_ends = [e["data"] for e in events if e.get("event") == "CHATBOT_END"]
        v2_ends = [e["data"] for e in events if e.get("event") == "AGENT_V2_END"]

        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown("**Chatbot**")
            if chatbot_ends:
                avg_latency = sum(d.get("latency_ms", 0) for d in chatbot_ends) // len(chatbot_ends)
                render_metric_card("So luot chay", str(len(chatbot_ends)))
                render_metric_card("Avg Latency", f"{avg_latency}ms")
            else:
                st.info("Chua co du lieu")

        with col_right:
            st.markdown("**ReAct Agent**")
            if v2_ends:
                success = sum(1 for r in v2_ends if r.get("status") == "success")
                avg_steps = sum(r.get("steps", 0) for r in v2_ends) / len(v2_ends)
                render_metric_card("Success Rate", f"{success}/{len(v2_ends)} ({success*100//len(v2_ends)}%)",
                                   "#28a745" if success == len(v2_ends) else "#dc3545")
                render_metric_card("Avg Steps", f"{avg_steps:.1f}")
            else:
                st.info("Chua co du lieu")

        # Error breakdown
        errors = [e for e in events if e.get("event") == "AGENT_ERROR"]
        if errors:
            st.markdown("### Phan loai loi")
            error_types = {}
            for e in errors:
                msg = e["data"].get("error", "UNKNOWN")
                if "PARSE_ERROR" in msg:
                    t = "Parse Error"
                elif "HALLUCINATION" in msg:
                    t = "Hallucination"
                elif "DUPLICATE" in msg:
                    t = "Duplicate Action"
                else:
                    t = "Other"
                error_types[t] = error_types.get(t, 0) + 1
            st.bar_chart(error_types)
