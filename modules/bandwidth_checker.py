# modules/bandwidth_checker.py
"""
bandwidth_checker.py
Estimate link utilization with a simple all-to-all demand model.
"""

from .logger import get_logger
from collections import defaultdict
import networkx as nx

log = get_logger("bandwidth_checker")
DEFAULT_BW = 1000.0  # Mbps


def check_bandwidth(G, demand_per_pair_mbps: float = 10.0):
    nodes = list(G.nodes())
    link_load = defaultdict(float)
    for i in range(len(nodes)):
        for j in range(len(nodes)):
            if i == j:
                continue
            a, b = nodes[i], nodes[j]
            try:
                path = nx.shortest_path(G, a, b)
            except nx.NetworkXNoPath:
                continue
            for k in range(len(path) - 1):
                u, v = path[k], path[k + 1]
                key = tuple(sorted([u, v]))
                link_load[key] += demand_per_pair_mbps
    links = {}
    for u, v, attr in G.edges(data=True):
        key = tuple(sorted([u, v]))
        capacity = float(attr.get("bandwidth", DEFAULT_BW))
        load = float(link_load.get(key, 0.0))
        util = load / capacity if capacity > 0 else 0.0
        links[f"{u}-{v}"] = {"capacity": capacity, "load": load, "utilization": util}
    avg_util = sum(x["utilization"] for x in links.values()) / len(links) if links else 0.0
    summary = f"{len(links)} links — avg utilization {avg_util:.2f}"
    log.info("Bandwidth check done: %s", summary)
    return {"summary": summary, "links": links}
