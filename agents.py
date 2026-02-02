import requests
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_URL = "https://api.openai.com/v1/responses"

HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json"
}

# ===== Agent Prompts =====

AGENTS = {
    "macro": "คุณคือ MacroAgent วิเคราะห์โลก Liquidity, Fed, geopolitics",
    "risk": "คุณคือ RiskAgent หา tail risk, non-linear risk",
    "asset": "คุณคือ AssetAgent วิเคราะห์ผลต่อสินทรัพย์",
    "investor": "คุณคือ InvestorAgent คิดแบบนักลงทุนระยะยาว",
    "skeptic": "คุณคือ SkepticAgent คอยหักล้าง thesis",
    "synth": (
        "คุณคือ SynthAgent (CEO) "
        "รับ input จาก agent อื่น "
        "สรุปภาพรวม + judgment ชัด "
        "ไม่ปลอบใจ ไม่กลาง ๆ"
    )
}

# ===== Call single agent =====

def call_agent(agent_name: str, user_text: str) -> str:
    payload = {
        "model": "gpt-4.1-mini",
        "input": [
            {"role": "system", "content": AGENTS[agent_name]},
            {"role": "user", "content": user_text}
        ]
    }

    r = requests.post(OPENAI_URL, headers=HEADERS, json=payload)
    r.raise_for_status()

    return r.json()["output"][0]["content"][0]["text"]


# ===== Investor Swarm =====

def run_investor_swarm(user_text: str) -> str:
    opinions = {}

    for agent in ["macro", "risk", "asset", "investor", "skeptic"]:
        opinions[agent] = call_agent(agent, user_text)

    synthesis_input = "\n\n".join(
        f"{k.upper()}:\n{v}" for k, v in opinions.items()
    )

    return call_agent("synth", synthesis_input)
