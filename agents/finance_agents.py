import requests
import os

OPENAI_URL = "https://api.openai.com/v1/responses"

# ===== Finance Agent Prompts =====
AGENTS = {
    "crypto": (
        "คุณคือ CryptoAgent วิเคราะห์ตลาด crypto, tokenomics, liquidity, on-chain data และ sentiment "
        "ไม่ให้คำแนะนำซื้อขายตรง ใช้ภาษาไทยเป็นหลัก แทรก English key terms เฉพาะจำเป็น"
    ),
    "commodity": (
        "คุณคือ CommodityAgent วิเคราะห์ทองคำ น้ำมัน และ commodity market "
        "เน้น macro linkage, USD/THB impact, supply-demand และ geopolitical impact "
        "ไม่ให้คำแนะนำซื้อขายตรง"
    ),
    "watchlist": (
        "คุณคือ WatchlistAgent สรุปข่าวตลาดสำคัญ 2–3 ประเด็น bullet, short & sharp "
        "เน้นสิ่งที่นักลงทุนควรจับตา"
    ),
    "synth": (
        "คุณคือ SynthAgent (CEO) ของ FinanceBot "
        "รับ input จาก agent อื่น (crypto, commodity, watchlist) "
        "สรุปภาพรวม + judgment ชัดเจน "
        "ไม่ปลอบใจ ไม่กลาง ๆ"
    )
}

# ===== Call single agent =====
def call_agent(agent_name: str, user_text: str) -> str:
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-4.1-mini",
        "input": [
            {"role": "system", "content": AGENTS[agent_name]},
            {"role": "user", "content": user_text}
        ]
    }

    r = requests.post(OPENAI_URL, headers=headers, json=payload, timeout=20)
    r.raise_for_status()
    return r.json()["output"][0]["content"][0]["text"]


# ===== Finance Swarm =====
def run_finance_swarm(user_text: str) -> str:
    opinions = {}

    for agent in ["crypto", "commodity", "watchlist"]:
        opinions[agent] = call_agent(agent, user_text)

    synthesis_input = "\n\n---\n\n".join(
        f"[{k.upper()}]\n{v}" for k, v in opinions.items()
    )

    return call_agent("synth", synthesis_input)
