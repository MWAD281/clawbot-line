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

def call_agent(agent_name, user_text):
    system_prompt = AGENTS[agent_name]

    payload = {
        "model": "gpt-4.1-mini",
        "input": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text}
        ]
    }

    r = requests.post(OPENAI_URL, headers=headers, json=payload)
    r.raise_for_status()
    return r.json()["output"][0]["content"][0]["text"]

