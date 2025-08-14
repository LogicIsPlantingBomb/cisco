"""
topology_builder.py
Enhanced topology builder with multiple topology types and streamlined functionality.
"""

import os
import networkx as nx
from typing import Dict, List, Tuple, Optional
from enum import Enum
import random
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger("topology_builder")

class TopologyType(Enum):
    """Supported topology types"""
    STAR = "star"
    RING = "ring"
    MESH = "mesh"
    TREE = "tree"
    BUS = "bus"
    HYBRID = "hybrid"
    SPINE_LEAF = "spine_leaf"

def create_star_topology(nodes: List[str]) -> nx.Graph:
    """Create a star topology with first node as center"""
    G = nx.Graph()
    if len(nodes) < 2:
        return G
    
    center = nodes[0]
    G.add_node(center, role="hub", device_type="switch")
    
    for node in nodes[1:]:
        G.add_node(node, role="endpoint", device_type="host")
        G.add_edge(center, node, 
                  bandwidth=1000, 
                  mtu=1500, 
                  up=True, 
                  link_type="ethernet")
    
    log.info(f"Created star topology with center: {center}")
    return G

def create_ring_topology(nodes: List[str]) -> nx.Graph:
    """Create a ring topology"""
    G = nx.Graph()
    if len(nodes) < 3:
        return G
    
    for i, node in enumerate(nodes):
        G.add_node(node, device_type="router")
        
    for i in range(len(nodes)):
        next_node = (i + 1) % len(nodes)
        G.add_edge(nodes[i], nodes[next_node],
                  bandwidth=1000,
                  mtu=1500,
                  up=True,
                  link_type="serial")
    
    log.info(f"Created ring topology with {len(nodes)} nodes")
    return G

def create_mesh_topology(nodes: List[str], partial: bool = False) -> nx.Graph:
    """Create full or partial mesh topology"""
    G = nx.Graph()
    for node in nodes:
        G.add_node(node, device_type="router")
    
    if partial:
        # Create partial mesh (each node connects to 2-3 others randomly)
        for node in nodes:
            targets = random.sample([n for n in nodes if n != node], 
                                  min(3, len(nodes) - 1))
            for target in targets:
                if not G.has_edge(node, target):
                    G.add_edge(node, target,
                              bandwidth=random.choice([100, 1000, 10000]),
                              mtu=1500,
                              up=True,
                              link_type="ethernet")
    else:
        # Create full mesh
        for i, node1 in enumerate(nodes):
            for node2 in nodes[i+1:]:
                G.add_edge(node1, node2,
                          bandwidth=1000,
                          mtu=1500,
                          up=True,
                          link_type="ethernet")
    
    topology_name = "partial mesh" if partial else "full mesh"
    log.info(f"Created {topology_name} topology with {len(nodes)} nodes")
    return G

def create_tree_topology(nodes: List[str], branching_factor: int = 2) -> nx.Graph:
    """Create a tree topology"""
    G = nx.Graph()
    if not nodes:
        return G
    
    root = nodes[0]
    G.add_node(root, role="root", device_type="switch", level=0)
    
    remaining_nodes = nodes[1:]
    current_level_nodes = [root]
    level = 1
    
    while remaining_nodes and current_level_nodes:
        next_level_nodes = []
        for parent in current_level_nodes:
            children_count = min(branching_factor, len(remaining_nodes))
            for _ in range(children_count):
                if not remaining_nodes:
                    break
                child = remaining_nodes.pop(0)
                G.add_node(child, role="branch", device_type="switch", level=level)
                G.add_edge(parent, child,
                          bandwidth=1000,
                          mtu=1500,
                          up=True,
                          link_type="ethernet")
                next_level_nodes.append(child)
        
        current_level_nodes = next_level_nodes
        level += 1
    
    log.info(f"Created tree topology with {len(nodes)} nodes and branching factor {branching_factor}")
    return G

def create_spine_leaf_topology(spine_count: int = 2, leaf_count: int = 4) -> nx.Graph:
    """Create a spine-leaf (Clos) topology"""
    G = nx.Graph()
    
    # Create spine nodes
    spine_nodes = [f"spine{i+1}" for i in range(spine_count)]
    for spine in spine_nodes:
        G.add_node(spine, role="spine", device_type="switch", tier="spine")
    
    # Create leaf nodes
    leaf_nodes = [f"leaf{i+1}" for i in range(leaf_count)]
    for leaf in leaf_nodes:
        G.add_node(leaf, role="leaf", device_type="switch", tier="leaf")
    
    # Connect every spine to every leaf
    for spine in spine_nodes:
        for leaf in leaf_nodes:
            G.add_edge(spine, leaf,
                      bandwidth=10000,  # 10G links
                      mtu=9000,         # Jumbo frames
                      up=True,
                      link_type="ethernet")
    
    # Add some hosts to leaves
    host_count = 2
    for leaf in leaf_nodes:
        for i in range(host_count):
            host = f"{leaf}-host{i+1}"
            G.add_node(host, role="host", device_type="server", tier="access")
            G.add_edge(leaf, host,
                      bandwidth=1000,
                      mtu=1500,
                      up=True,
                      link_type="ethernet")
    
    log.info(f"Created spine-leaf topology: {spine_count} spines, {leaf_count} leaves")
    return G

def create_bus_topology(nodes: List[str]) -> nx.Graph:
    """Create a bus topology (linear)"""
    G = nx.Graph()
    if len(nodes) < 2:
        return G
    
    for node in nodes:
        G.add_node(node, device_type="workstation")
    
    for i in range(len(nodes) - 1):
        G.add_edge(nodes[i], nodes[i + 1],
                  bandwidth=100,
                  mtu=1500,
                  up=True,
                  link_type="coax")
    
    log.info(f"Created bus topology with {len(nodes)} nodes")
    return G

def create_hybrid_topology(node_groups: Dict[str, List[str]]) -> nx.Graph:
    """Create a hybrid topology combining different types"""
    G = nx.Graph()
    
    # Create different topology sections
    for group_type, nodes in node_groups.items():
        if group_type == "core":
            # Core as full mesh
            subgraph = create_mesh_topology(nodes, partial=False)
        elif group_type == "distribution":
            # Distribution as ring
            subgraph = create_ring_topology(nodes)
        elif group_type == "access":
            # Access as star (first node is switch, others are hosts)
            subgraph = create_star_topology(nodes)
        else:
            # Default to bus
            subgraph = create_bus_topology(nodes)
        
        # Add to main graph
        G = nx.union(G, subgraph)
    
    # Interconnect different sections
    if "core" in node_groups and "distribution" in node_groups:
        core_nodes = node_groups["core"]
        dist_nodes = node_groups["distribution"]
        # Connect each core to each distribution
        for core in core_nodes[:2]:  # Limit connections
            for dist in dist_nodes[:2]:
                G.add_edge(core, dist,
                          bandwidth=10000,
                          mtu=1500,
                          up=True,
                          link_type="fiber")
    
    if "distribution" in node_groups and "access" in node_groups:
        dist_nodes = node_groups["distribution"]
        access_switches = [node_groups["access"][0]] if node_groups["access"] else []
        # Connect distribution to access switches
        for dist in dist_nodes:
            for access_sw in access_switches:
                G.add_edge(dist, access_sw,
                          bandwidth=1000,
                          mtu=1500,
                          up=True,
                          link_type="ethernet")
    
    log.info(f"Created hybrid topology with {len(G.nodes)} total nodes")
    return G

def build_topology_by_type(topology_type: TopologyType, 
                          nodes: Optional[List[str]] = None,
                          **kwargs) -> nx.Graph:
    """Build topology based on specified type"""
    
    # Default nodes if none provided
    if nodes is None:
        if topology_type == TopologyType.SPINE_LEAF:
            # Special case for spine-leaf
            return create_spine_leaf_topology(
                spine_count=kwargs.get('spine_count', 2),
                leaf_count=kwargs.get('leaf_count', 4)
            )
        else:
            nodes = [f"node{i+1}" for i in range(kwargs.get('node_count', 5))]
    
    if topology_type == TopologyType.STAR:
        return create_star_topology(nodes)
    elif topology_type == TopologyType.RING:
        return create_ring_topology(nodes)
    elif topology_type == TopologyType.MESH:
        return create_mesh_topology(nodes, kwargs.get('partial', False))
    elif topology_type == TopologyType.TREE:
        return create_tree_topology(nodes, kwargs.get('branching_factor', 2))
    elif topology_type == TopologyType.BUS:
        return create_bus_topology(nodes)
    elif topology_type == TopologyType.HYBRID:
        return create_hybrid_topology(kwargs.get('node_groups', {
            'core': ['core1', 'core2'],
            'distribution': ['dist1', 'dist2', 'dist3'],
            'access': ['access1', 'host1', 'host2', 'host3']
        }))
    else:
        log.error(f"Unsupported topology type: {topology_type}")
        return nx.Graph()

def add_topology_metrics(G: nx.Graph) -> Dict:
    """Calculate and add topology metrics"""
    metrics = {
        'node_count': G.number_of_nodes(),
        'edge_count': G.number_of_edges(),
        'density': nx.density(G),
        'diameter': nx.diameter(G) if nx.is_connected(G) else float('inf'),
        'average_clustering': nx.average_clustering(G),
        'is_connected': nx.is_connected(G)
    }
    
    # Add degree statistics
    degrees = dict(G.degree())
    if degrees:
        metrics['avg_degree'] = sum(degrees.values()) / len(degrees)
        metrics['max_degree'] = max(degrees.values())
        metrics['min_degree'] = min(degrees.values())
    
    log.info(f"Topology metrics: {metrics}")
    return metrics

def export_topology_summary(G: nx.Graph, filename: str = "topology_summary.txt"):
    """Export topology summary to file"""
    metrics = add_topology_metrics(G)
    
    with open(filename, 'w') as f:
        f.write("=== Network Topology Summary ===\n\n")
        f.write(f"Nodes: {metrics['node_count']}\n")
        f.write(f"Edges: {metrics['edge_count']}\n")
        f.write(f"Network Density: {metrics['density']:.3f}\n")
        f.write(f"Connected: {'Yes' if metrics['is_connected'] else 'No'}\n")
        
        if metrics['is_connected']:
            f.write(f"Network Diameter: {metrics['diameter']}\n")
        
        f.write(f"Average Clustering: {metrics['average_clustering']:.3f}\n")
        f.write(f"Average Degree: {metrics.get('avg_degree', 0):.1f}\n")
        
        f.write("\n=== Node Details ===\n")
        for node, data in G.nodes(data=True):
            device_type = data.get('device_type', 'unknown')
            role = data.get('role', 'N/A')
            f.write(f"{node}: {device_type} (role: {role})\n")
        
        f.write("\n=== Edge Details ===\n")
        for u, v, data in G.edges(data=True):
            bandwidth = data.get('bandwidth', 'unknown')
            link_type = data.get('link_type', 'unknown')
            f.write(f"{u} -- {v}: {bandwidth} Mbps, {link_type}\n")
    
    log.info(f"Topology summary exported to {filename}")

# Convenience function for quick topology creation
def quick_topology(topology_name: str, size: str = "medium") -> nx.Graph:
    """Create common topologies with predefined sizes"""
    
    size_configs = {
        "small": {"node_count": 4, "spine_count": 2, "leaf_count": 2},
        "medium": {"node_count": 6, "spine_count": 2, "leaf_count": 4}, 
        "large": {"node_count": 10, "spine_count": 3, "leaf_count": 6}
    }
    
    config = size_configs.get(size, size_configs["medium"])
    
    topology_map = {
        "star": (TopologyType.STAR, {"node_count": config["node_count"]}),
        "ring": (TopologyType.RING, {"node_count": config["node_count"]}),
        "mesh": (TopologyType.MESH, {"node_count": config["node_count"], "partial": True}),
        "tree": (TopologyType.TREE, {"node_count": config["node_count"], "branching_factor": 2}),
        "spine_leaf": (TopologyType.SPINE_LEAF, {"spine_count": config["spine_count"], "leaf_count": config["leaf_count"]}),
        "bus": (TopologyType.BUS, {"node_count": config["node_count"]}),
        "hybrid": (TopologyType.HYBRID, {})
    }
    
    if topology_name not in topology_map:
        log.error(f"Unknown topology: {topology_name}")
        return nx.Graph()
    
    topo_type, kwargs = topology_map[topology_name]
    return build_topology_by_type(topo_type, **kwargs)

if __name__ == "__main__":
    # Demo different topologies
    print("Creating sample topologies...")
    
    topologies = ["star", "ring", "mesh", "tree", "spine_leaf", "bus", "hybrid"]
    
    for topo_name in topologies:
        print(f"\n--- {topo_name.upper()} TOPOLOGY ---")
        G = quick_topology(topo_name, "small")
        metrics = add_topology_metrics(G)
        print(f"Nodes: {metrics['node_count']}, Edges: {metrics['edge_count']}, Connected: {metrics['is_connected']}")
        
        # Export summary for each
        export_topology_summary(G, f"{topo_name}_topology_summary.txt")
