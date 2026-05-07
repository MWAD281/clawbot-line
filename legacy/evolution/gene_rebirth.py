# evolution/gene_rebirth.py
# 🧬 Phase 12.5 – Gene Mutation & Rebirth Engine

import random
import time
from typing import Dict

from memory.agent_weights import get_weight, overwrite_weight
from evolution.capital_allocator import kill_ceo, revive_ceo, is_alive
from evolution.shadow_portfolio import portfolio_value

# -------------------------
# CONFIG
# -------------------------

BASE_CAPITAL = 100_000
MUTATION_RATE = 0.15      # โอกาสกลายพันธุ์
ELITE_RATIO = 0.2        # CEO ที่รอดเป็น elite
MAX_WEIGHT = 1.5
MIN_WEIGHT = 0.3


# -------------------------
# GENE POOL
# -------------------------

_gene_pool: Dict[str, dict] = {}


# -------------------------
# INIT GENE
# -------------------------

def init_gene(ceo_id: str):
    if ceo_id not in _gene_pool:
        _gene_pool[ceo_id] = {
            "risk_bias": random.uniform(0.8, 1.2),
            "conviction_bias": random.uniform(0.8, 1.2),
            "style": random.choice(["macro", "momentum", "defensive"]),
            "birth": time.time()
        }


# -------------------------
# FITNESS
# -------------------------

def fitness_score(ceo_id: str) -> float:
    value = portfolio_value(ceo_id)
    return value / BASE_CAPITAL


# -------------------------
# SELECTION
# -------------------------

def select_elite():
    scores = []
    for ceo_id in _gene_pool:
        if is_alive(ceo_id):
            scores.append((ceo_id, fitness_score(ceo_id)))

    scores.sort(key=lambda x: x[1], reverse=True)
    elite_count = max(1, int(len(scores) * ELITE_RATIO))

    elite = [cid for cid, _ in scores[:elite_count]]
    dead = [cid for cid, _ in scores[elite_count:]]

    return elite, dead


# -------------------------
# MUTATION
# -------------------------

def mutate_gene(parent_gene: dict) -> dict:
    gene = parent_gene.copy()

    if random.random() < MUTATION_RATE:
        gene["risk_bias"] *= random.uniform(0.8, 1.2)
    if random.random() < MUTATION_RATE:
        gene["conviction_bias"] *= random.uniform(0.8, 1.2)
    if random.random() < MUTATION_RATE:
        gene["style"] = random.choice(["macro", "momentum", "defensive"])

    return gene


# -------------------------
# REBIRTH
# -------------------------

def rebirth_cycle():
    """
    🔥 เรียกอันนี้ = Darwinism เต็มรูป
    """
    elite, dead = select_elite()

    # ❌ Kill losers
    for ceo_id in dead:
        kill_ceo(ceo_id)

    # 🧬 Rebirth from elite
    for ceo_id in dead:
        parent = random.choice(elite)
        parent_gene = _gene_pool[parent]

        new_gene = mutate_gene(parent_gene)
        _gene_pool[ceo_id] = new_gene

        revive_ceo(ceo_id)

        # reset weight ตาม gene
        new_weight = min(
            MAX_WEIGHT,
            max(MIN_WEIGHT, get_weight(parent) * new_gene["risk_bias"])
        )
        overwrite_weight(ceo_id, new_weight)

    return {
        "elite": elite,
        "reborn": dead
    }


# -------------------------
# DEBUG / SNAPSHOT
# -------------------------

def gene_snapshot():
    snap = {}
    for cid, gene in _gene_pool.items():
        snap[cid] = {
            "alive": is_alive(cid),
            "fitness": fitness_score(cid),
            "gene": gene
        }
    return snap
