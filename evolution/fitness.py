# evolution/fitness.py

def evaluate_fitness(ai_text: str, latency: float) -> int:
    score = 0

    # 1. Clarity (ฟันธงไหม)
    if any(k in ai_text for k in ["ชัดเจน", "ฟันธง", "แนวโน้มหลัก"]):
        score += 1
    if any(k in ai_text for k in ["ขึ้นอยู่กับ", "อย่างไรก็ตาม", "อาจจะ"]):
        score -= 1

    # 2. Signal vs Noise
    if len(ai_text) < 50:
        score -= 1
    if len(ai_text) > 1200:
        score -= 1

    # 3. Latency
    if latency > 5:
        score -= 1

    return score
