"""
main.py
Combined CLI for network topology creation, analysis, and simulation.
"""

import sys
import os
from pathlib import Path
import networkx as nx
from typing import Dict, List

# Rich is optional nicety; fallback to print if not present
try:
    from rich.console import Console
    from rich.table import Table
    console = Console()
    use_rich = True
except Exception:
    console = None
    use_rich = False

# Import our topology builder and other modules
from modules.topology_builder import (
    TopologyType, 
    build_topology_by_type, 
    quick_topology, 
    add_topology_metrics,
    export_topology_summary
)

# Import additional modules from the second version
from modules import (
    config_parser,
    analyzer,
    validator,
    optimizer,
    recommender,
    autofix,
    simulator,
    visualizer,
    logger
)

log = logger.get_logger("main")

def print_msg(msg):
    """Print message with rich formatting if available"""
    if use_rich:
        console.print(msg)
    else:
        print(msg)

def simple_visualize(G: nx.Graph, output_file: str = "topology.txt"):
    """Create a simple text-based visualization of the topology"""
    with open(output_file, 'w') as f:
        f.write("=== Network Topology Visualization ===\n\n")
        
        # Node list
        f.write("NODES:\n")
        for node, data in G.nodes(data=True):
            device_type = data.get('device_type', 'unknown')
            role = data.get('role', 'N/A')
            f.write(f"  {node} [{device_type}] (role: {role})\n")
        
        f.write(f"\nCONNECTIONS ({G.number_of_edges()} total):\n")
        for u, v, data in G.edges(data=True):
            bandwidth = data.get('bandwidth', '?')
            link_type = data.get('link_type', 'unknown')
            status = "UP" if data.get('up', True) else "DOWN"
            f.write(f"  {u} <---> {v} [{bandwidth} Mbps, {link_type}, {status}]\n")
        
        # Adjacency representation
        f.write("\nADJACENCY LIST:\n")
        for node in G.nodes():
            neighbors = list(G.neighbors(node))
            f.write(f"  {node}: {', '.join(neighbors) if neighbors else 'isolated'}\n")
    
    print_msg(f"Topology visualization saved to: {output_file}")

def analyze_topology(G: nx.Graph):
    """Perform basic topology analysis"""
    print_msg("\n=== Topology Analysis ===")
    
    metrics = add_topology_metrics(G)
    
    print_msg(f"Nodes: {metrics['node_count']}")
    print_msg(f"Edges: {metrics['edge_count']}")
    print_msg(f"Network Density: {metrics['density']:.3f}")
    print_msg(f"Connected: {'Yes' if metrics['is_connected'] else 'No'}")
    
    if metrics['is_connected']:
        print_msg(f"Network Diameter: {metrics['diameter']}")
        print_msg(f"Average Path Length: {nx.average_shortest_path_length(G):.2f}")
    
    print_msg(f"Average Clustering: {metrics['average_clustering']:.3f}")
    print_msg(f"Average Degree: {metrics.get('avg_degree', 0):.1f}")
    
    # Find critical nodes (highest degree)
    degrees = dict(G.degree())
    if degrees:
        max_degree_node = max(degrees, key=degrees.get)
        print_msg(f"Most Connected Node: {max_degree_node} (degree: {degrees[max_degree_node]})")
    
    # Check for articulation points (critical for connectivity)
    if nx.is_connected(G):
        articulation_points = list(nx.articulation_points(G))
        if articulation_points:
            print_msg(f"Critical Nodes (articulation points): {', '.join(articulation_points)}")
        else:
            print_msg("No critical single points of failure found")

def simulate_failure(G: nx.Graph, node_to_fail: str):
    """Simulate node failure and analyze impact"""
    if node_to_fail not in G.nodes():
        print_msg(f"Node {node_to_fail} not found in topology")
        return
    
    print_msg(f"\n=== Simulating failure of node: {node_to_fail} ===")
    
    # Create copy and remove node
    G_failed = G.copy()
    neighbors = list(G_failed.neighbors(node_to_fail))
    G_failed.remove_node(node_to_fail)
    
    print_msg(f"Removed node {node_to_fail} and its {len(neighbors)} connections")
    print_msg(f"Affected neighbors: {', '.join(neighbors)}")
    
    # Analyze impact
    if nx.is_connected(G) and not nx.is_connected(G_failed):
        print_msg("❌ CRITICAL FAILURE: Network is now disconnected!")
        components = list(nx.connected_components(G_failed))
        print_msg(f"Network split into {len(components)} isolated components:")
        for i, comp in enumerate(components, 1):
            print_msg(f"  Component {i}: {', '.join(comp)} ({len(comp)} nodes)")
    else:
        print_msg("✅ Network remains connected after failure")
        if nx.is_connected(G_failed):
            new_diameter = nx.diameter(G_failed)
            original_diameter = nx.diameter(G) if nx.is_connected(G) else float('inf')
            if new_diameter > original_diameter:
                print_msg(f"Network diameter increased: {original_diameter} -> {new_diameter}")

def compare_topologies():
    """Compare different topology types"""
    print_msg("\n--- Topology Comparison ---")
    
    topologies = ["star", "ring", "mesh", "tree", "spine_leaf", "bus"]
    results = []
    
    for topo_name in topologies:
        G = quick_topology(topo_name, "small")
        metrics = add_topology_metrics(G)
        results.append((topo_name, metrics))
    
    # Print comparison table
    print_msg(f"{'Topology':<12} {'Nodes':<6} {'Edges':<6} {'Density':<8} {'Connected':<10} {'Avg Degree':<10}")
    print_msg("-" * 70)
    
    for topo_name, metrics in results:
        connected = "Yes" if metrics['is_connected'] else "No"
        avg_degree = metrics.get('avg_degree', 0)
        print_msg(f"{topo_name:<12} {metrics['node_count']:<6} {metrics['edge_count']:<6} "
              f"{metrics['density']:<8.3f} {connected:<10} {avg_degree:<10.1f}")

def create_topology_menu():
    """Menu for creating different topologies"""
    print_msg("\n--- Create Topology ---")
    print_msg("1) Star topology")
    print_msg("2) Ring topology") 
    print_msg("3) Mesh topology (partial)")
    print_msg("4) Tree topology")
    print_msg("5) Bus topology")
    print_msg("6) Spine-Leaf topology")
    print_msg("7) Hybrid topology")
    print_msg("8) Custom topology")
    print_msg("9) From config files")
    
    topo_choice = input("Topology type> ").strip()
    
    if topo_choice == "9":
        config_dir = input("Config directory [./configs]: ").strip() or "./configs"
        parsed = config_parser.parse_all_configs(config_dir)
        G = topology_builder.build_topology(parsed)
        print_msg(f"Built topology from configs: nodes={G.number_of_nodes()}, edges={G.number_of_edges()}")
        return G
    
    size = input("Size (small/medium/large) [medium]: ").strip() or "medium"
    
    topology_map = {
        "1": "star",
        "2": "ring", 
        "3": "mesh",
        "4": "tree",
        "5": "bus",
        "6": "spine_leaf",
        "7": "hybrid"
    }
    
    if topo_choice in topology_map:
        topo_name = topology_map[topo_choice]
        print_msg(f"Creating {topo_name} topology ({size})...")
        G = quick_topology(topo_name, size)
        print_msg(f"Created topology with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
        return G
    
    elif topo_choice == "8":
        return create_custom_topology()
    
    else:
        print_msg("Invalid choice")
        return None

def create_custom_topology():
    """Create a custom topology with user-specified nodes and connections"""
    print_msg("\n--- Custom Topology ---")
    
    # Get nodes
    nodes_input = input("Enter node names (comma-separated): ").strip()
    if not nodes_input:
        print_msg("No nodes specified")
        return None
    
    nodes = [n.strip() for n in nodes_input.split(",")]
    
    # Create graph with nodes
    G = nx.Graph()
    for node in nodes:
        device_type = input(f"Device type for {node} [router]: ").strip() or "router"
        G.add_node(node, device_type=device_type)
    
    print_msg(f"Added {len(nodes)} nodes")
    
    # Get connections
    print_msg("Enter connections (format: node1-node2, or 'done' to finish):")
    while True:
        connection = input("Connection> ").strip()
        if connection.lower() == 'done':
            break
        
        if '-' not in connection:
            print_msg("Invalid format. Use: node1-node2")
            continue
        
        try:
            node1, node2 = connection.split('-', 1)
            node1, node2 = node1.strip(), node2.strip()
            
            if node1 not in nodes or node2 not in nodes:
                print_msg(f"Unknown nodes. Available: {', '.join(nodes)}")
                continue
            
            if G.has_edge(node1, node2):
                print_msg(f"Connection {node1}-{node2} already exists")
                continue
            
            bandwidth = input(f"Bandwidth for {node1}-{node2} [1000]: ").strip()
            bandwidth = int(bandwidth) if bandwidth.isdigit() else 1000
            
            G.add_edge(node1, node2, bandwidth=bandwidth, mtu=1500, up=True, link_type="ethernet")
            print_msg(f"Added connection: {node1} <-> {node2}")
            
        except Exception as e:
            print_msg(f"Error adding connection: {e}")
    
    print_msg(f"Custom topology created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    return G

def main_pipeline(config_path: str):
    """
    Run full pipeline end-to-end:
    1. Parse configs and links, build topology
    2. Validate
    3. Analyze & bandwidth check
    4. Optimize and recommend
    5. Generate autofix suggestions
    6. Visualize
    """
    print_msg("[bold cyan]NetSimPro — Running Full Pipeline[/bold cyan]" if use_rich else "NetSimPro — Running Full Pipeline")
    
    parsed = config_parser.parse_all_configs(config_path)
    if not parsed:
        print_msg("[red]No configurations parsed. Check config directory and links file.[/red]" if use_rich else "No configurations parsed. Check config directory and links file.")
        return
    
    G = topology_builder.build_topology(parsed)
    if G.number_of_nodes() == 0:
        print_msg("[red]No topology nodes found. Check config directory and links file.[/red]" if use_rich else "No topology nodes found. Check config directory and links file.")
        return

    log.info("Topology built: %d nodes, %d edges", G.number_of_nodes(), G.number_of_edges())

    # 1. validation
    issues = validator.validate_topology(G)
    if issues:
        print_msg(f"[yellow]Validation found {len(issues)} issues[/yellow]" if use_rich else f"Validation found {len(issues)} issues")
        for it in issues:
            print_msg(f"- {it}")
    else:
        print_msg("[green]No validation issues found[/green]" if use_rich else "No validation issues found")

    # 2. analysis & bandwidth
    analysis = analyzer.analyze_network(G)
    print_msg(f"[blue]{analysis['summary']}[/blue]" if use_rich else analysis["summary"])

    # 3. optimizer & recommender
    suggestions = optimizer.suggest_optimizations(G, analysis)
    recs = recommender.generate_recommendations(G, analysis)
    if recs:
        print_msg("[magenta]Recommendations:[/magenta]" if use_rich else "Recommendations:")
        for r in recs:
            print_msg(f"- {r}")

    # 4. autofix
    fixes = autofix.generate_auto_fixes(G)
    print_msg(f"[green]Auto-fix suggestions written to ./auto_fixes/auto_fixes.txt[/green]" if use_rich else "Auto-fix suggestions written to ./auto_fixes/auto_fixes.txt")

    # 5. visualization
    out_png = Path.cwd() / "output" / "topology.png"
    visualizer.draw_topology(G, path=str(out_png))
    print_msg(f"[green]Topology saved to {out_png}[/green]" if use_rich else f"Topology saved to {out_png}")

def interactive_menu():
    """Main interactive menu"""
    print_msg("=== Network Topology Builder ===")
    print_msg("Create and analyze different network topologies\n")
    
    current_topology = None
    
    while True:
        print_msg("\n--- Main Menu ---")
        print_msg("1) Create topology")
        print_msg("2) Analyze current topology") 
        print_msg("3) Visualize current topology")
        print_msg("4) Export topology summary")
        print_msg("5) Simulate node failure")
        print_msg("6) Compare topologies")
        print_msg("7) Run full pipeline (configs)")
        print_msg("8) Validate topology")
        print_msg("9) Generate auto-fixes")
        print_msg("10) Simulate Day-1")
        print_msg("11) Simulate link failure")
        print_msg("0) Exit")
        
        choice = input("\nChoice> ").strip()
        
        if choice == "1":
            current_topology = create_topology_menu()
        
        elif choice == "2":
            if current_topology is None:
                print_msg("No topology loaded. Please create one first.")
            else:
                analyze_topology(current_topology)
        
        elif choice == "3":
            if current_topology is None:
                print_msg("No topology loaded. Please create one first.")
            else:
                print_msg("1) Simple text visualization")
                print_msg("2) Graphical visualization")
                viz_choice = input("Visualization type> ").strip()
                
                if viz_choice == "1":
                    filename = input("Output file [topology.txt]: ").strip() or "topology.txt"
                    simple_visualize(current_topology, filename)
                elif viz_choice == "2":
                    out_png = input("Output file [topology.png]: ").strip() or "topology.png"
                    visualizer.draw_topology(current_topology, path=out_png)
                    print_msg(f"Topology visualization saved to: {out_png}")
                else:
                    print_msg("Invalid choice")
        
        elif choice == "4":
            if current_topology is None:
                print_msg("No topology loaded. Please create one first.")
            else:
                filename = input("Summary file [topology_summary.txt]: ").strip() or "topology_summary.txt"
                export_topology_summary(current_topology, filename)
                print_msg(f"Summary exported to {filename}")
        
        elif choice == "5":
            if current_topology is None:
                print_msg("No topology loaded. Please create one first.")
            else:
                print_msg(f"Available nodes: {', '.join(current_topology.nodes())}")
                node = input("Node to fail: ").strip()
                simulate_failure(current_topology, node)
        
        elif choice == "6":
            compare_topologies()
        
        elif choice == "7":
            config_dir = input("Config directory [./configs]: ").strip() or "./configs"
            main_pipeline(config_dir)
        
        elif choice == "8":
            if current_topology is None:
                print_msg("No topology loaded. Please create one first.")
            else:
                issues = validator.validate_topology(current_topology)
                if issues:
                    print_msg(f"Validation found {len(issues)} issues")
                    for it in issues:
                        print_msg(f"- {it}")
                else:
                    print_msg("No validation issues found")
        
        elif choice == "9":
            if current_topology is None:
                print_msg("No topology loaded. Please create one first.")
            else:
                autofix.generate_auto_fixes(current_topology)
                print_msg("Auto-fixes generated.")
        
        elif choice == "10":
            if current_topology is None:
                print_msg("No topology loaded. Please create one first.")
            else:
                simulator.run_day1_simulation(current_topology)
        
        elif choice == "11":
            if current_topology is None:
                print_msg("No topology loaded. Please create one first.")
            else:
                link = input("Link to fail (NODE1-NODE2): ").strip()
                simulator.simulate_link_failure(current_topology, link)
        
        elif choice == "0":
            print_msg("Goodbye!")
            sys.exit(0)
        
        else:
            print_msg("Invalid choice. Please try again.")

if __name__ == "__main__":
    try:
        interactive_menu()
    except KeyboardInterrupt:
        print_msg("\nExiting...")
        sys.exit(0)
    except Exception as e:
        print_msg(f"Error: {e}")
        sys.exit(1)
