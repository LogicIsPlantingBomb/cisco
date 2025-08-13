# optimizer.py
"""
optimizer.py
Suggest optimization actions:
- enable ECMP if multiple equal-cost paths (not fully implemented)
- suggest upgrading link if utilization very high
"""

from .logger import get_logger
from . import bandwidth_checker
import networkx as nx

log = get_logger("optimizer")


def suggest_optimizations(G, analysis=None):
    """
    Return list of suggestion strings.
    Uses bandwidth_checker to find high-util links.
    """
    suggestions = []
    bw = bandwidth_checker.check_bandwidth(G)
    for link, stats in bw["links"].items():
        util = stats["utilization"]
        if util > 0.95:
            suggestions.append(f"[CRITICAL] Upgrade link {link} (util {util:.2f}) or add backup path")
        elif util > 0.75:
            suggestions.append(f"[WARN] Consider traffic engineering for {link} (util {util:.2f})")
    # aggregation suggestion: if many leaves exist, recommend aggregation
    leaves = [n for n, d in G.degree() if d == 1]
    if len(leaves) >= 3:
        suggestions.append(f"Many leaf nodes ({len(leaves)}); consider access-layer aggregation")
    log.info("Optimization suggestions produced: %d", len(suggestions))
    return suggestions
