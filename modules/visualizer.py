# visualizer.py
"""
visualizer.py
Offers ASCII and PNG visualizations via networkx + matplotlib.
"""

import networkx as nx
import matplotlib.pyplot as plt
import os
from .logger import get_logger

log = get_logger("visualizer")
os.makedirs("output", exist_ok=True)


def draw_topology(G, path="output/topology.png"):
    plt.figure(figsize=(10, 8), facecolor='whitesmoke') 

    # Better layout for loops visibility
    pos = nx.circular_layout(G)

    node_colors = ["red" if G.degree(n) == 1 else "green" for n in G.nodes()]

    # Detect edges part of loops (cycles)
    simple_G=nx.Graph(G)
    cycles = list(nx.cycle_basis(simple_G))
    edges_in_cycles = set()
    for cycle in cycles:
        # cycle is list of nodes forming a cycle; get edges in cycle
        edges_in_cycles.update(
            {(cycle[i], cycle[(i+1) % len(cycle)]) for i in range(len(cycle))}
        )
        edges_in_cycles.update(
            {(cycle[(i+1) % len(cycle)], cycle[i]) for i in range(len(cycle))}
        )



    # Edge colors & widths: highlight loop edges
    edge_colors = []
    edge_widths = []
    for u, v, data in G.edges(data=True):
        if (u, v) in edges_in_cycles or (v, u) in edges_in_cycles:
            edge_colors.append("red")
            edge_widths.append(4)
        else:
            edge_colors.append("#2ca02c")
            edge_widths.append(2)

    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=800)
    nx.draw_networkx_edges(G, pos, edge_color=edge_colors, width=edge_widths)

    nx.draw_networkx_labels(G, pos, font_size=12, font_color='black', font_weight='bold')

    # Edge labels: add bandwidth and interfaces
    edge_labels = {}
    for u, v, a in G.edges(data=True):
        bw = a.get("bandwidth", "")
        up = a.get("up", True)
        ifaces = ','.join(a.get("ifaces", []))
        label = f"{ifaces}\n{bw}Mb/s" + ("" if up else " (down)")
        edge_labels[(u, v)] = label

    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='blue')

    plt.gca().set_facecolor('whitesmoke') 
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    log.info(f"Saved topology image to {path}")



def ascii_topology(G):
    s = []
    for n in G.nodes():
        s.append(f"{n} -> {list(G.neighbors(n))}")
    return "\n".join(s)
