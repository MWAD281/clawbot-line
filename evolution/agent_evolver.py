# evolution/agent_evolver.py

from evolution.judgment_evolver import evolve_judgment
from memory.judgment_state import save_judgment


def evolve_agents(judgment: dict, outcome: dict):
    """
    evolve agent + worldview ของโลก
    """

    # 🧠 evolve โลกก่อน
    judgment = evolve_judgment(judgment, outcome)
    save_judgment(judgment)

    # 🤖 (placeholder) evolve agents
    # ตรงนี้คุณจะใส่ logic Darwinism ทีหลังได้
    print(f"[EVOLVE] Worldview => {judgment['worldview']}")
