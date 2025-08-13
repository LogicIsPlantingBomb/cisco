# recommender.py
"""
recommender.py
Higher-level, ranked recommendations (simple heuristics for now).
"""

from .logger import get_logger
from . import optimizer,validator

log = get_logger("recommender")


def generate_recommendations(G, analysis=None):
    recs = []
    # critical optimizations
    opts = optimizer.suggest_optimizations(G, analysis)
    recs.extend(opts)
    # validation issues
    issues = validator.validate_topology(G)
    for it in issues:
        recs.append(f"[VALIDATION] {it}")
    # simple ranking: CRITICAL lines first
    critical = [r for r in recs if "CRITICAL" in r or "Duplicate IP" in r]
    others = [r for r in recs if r not in critical]
    ranked = critical + others
    log.info("Generated %d recommendations", len(ranked))
    return ranked