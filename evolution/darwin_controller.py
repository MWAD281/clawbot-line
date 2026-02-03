# evolution/darwin_controller.py

from evolution.agent_state import update_fitness, rebirth, AGENT_STATE
from evolution.fitness import evaluate_fitness
import time

def process_ai_result(ai_text: str, start_time: float):
    latency = time.time() - start_time
    delta = evaluate_fitness(ai_text, latency)

    state = update_fitness(delta)

    if state["status"] == "DEAD":
        print("☠️ AGENT DIED — REBIRTH")
        rebirth()

    return state
