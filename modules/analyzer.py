# analyzer.py
"""
analyzer.py
Higher-level analysis: bottlenecks, link saturation, resiliency score.
"""

from .logger import get_logger
from . import bandwidth_checker
import statistics

log = get_logger("analyzer")


def analyze_network(G):
    report = {"summary": "", "details": {}}
    # basic stats
    node_count = G.number_of_nodes()
    edge_count = G.number_of_edges()
    report["details"]["nodes"] = node_count
    report["details"]["edges"] = edge_count

    # bandwidth usage
    bw_stats = bandwidth_checker.check_bandwidth(G)
    report["details"]["bandwidth"] = bw_stats

    # detect bottlenecks: links where utilization > 0.8
    bottlenecks = [e for e, v in bw_stats.get("links", {}).items() if v["utilization"] > 0.8]
    report["details"]["bottlenecks"] = bottlenecks

    # resiliency score calculation:
    # simple formula: 50% from redundancy (degree>1), 50% from bandwidth headroom
    degrees = [d for n, d in G.degree()]
    redundancy_score = (sum(1 for d in degrees if d > 1) / (node_count or 1)) * 50
    headrooms = []
    for info in bw_stats.get("links", {}).values():
        headrooms.append(max(0.0, 1 - info["utilization"]))
    headroom_score = (statistics.mean(headrooms) * 50) if headrooms else 25
    resiliency = round(redundancy_score + headroom_score, 2)
    report["details"]["resiliency_score"] = resiliency

    summary = f"Nodes: {node_count}, Edges: {edge_count}, Bottlenecks: {len(bottlenecks)}, Resiliency: {resiliency}/100"
    report["summary"] = summary
    log.info("Analysis complete")
    return report
