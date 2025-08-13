"""
main.py
Final CLI orchestrator for NetSimPro (executable pipeline).
"""

import sys
from pathlib import Path

# Rich is optional nicety; fallback to print if not present
try:
    from rich.console import Console
    from rich.table import Table
    console = Console()
    use_rich = True
except Exception:
    console = None
    use_rich = False

# modules
from modules import (
    config_parser,
    topology_builder,
    analyzer,
    validator,
    optimizer,
    recommender,
    autofix,
    bandwidth_checker,
    simulator,
    visualizer,
    logger,
    utils
)

log = logger.get_logger("main")


def print_msg(msg):
    if use_rich:
        console.print(msg)
    else:
        print(msg)


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
    print_msg("\n=== NetSimPro CLI ===")
    while True:
        print_msg("\nOptions:\n1) Run full pipeline (configs/)\n2) Parse configs only\n3) Build topology only\n4) Validate topology\n5) Analyze topology\n6) Generate auto-fixes\n7) Visualize topology\n8) Simulate Day-1\n9) Simulate link failure\n0) Exit")
        choice = input("Choice> ").strip()
        if choice == "1":
            config_dir = input("Config directory [./configs]: ").strip() or "./configs"
            main_pipeline(config_dir)
        elif choice == "2":
            config_dir = input("Config directory [./configs]: ").strip() or "./configs"
            parsed = config_parser.parse_all_configs(config_dir)
            print_msg(f"Parsed {len(parsed)} configs.")
        elif choice == "3":
            config_dir = input("Config directory [./configs]: ").strip() or "./configs"
            parsed = config_parser.parse_all_configs(config_dir)
            G = topology_builder.build_topology(parsed)
            print_msg(f"Built topology: nodes={G.number_of_nodes()}, edges={G.number_of_edges()}")
        elif choice == "4":
            config_dir = input("Config directory [./configs]: ").strip() or "./configs"
            parsed = config_parser.parse_all_configs(config_dir)
            G = topology_builder.build_topology(parsed)
            issues = validator.validate_topology(G)
            print_msg(f"Issues found: {len(issues)}")
            for it in issues:
                print_msg(f"- {it}")
        elif choice == "5":
            config_dir = input("Config directory [./configs]: ").strip() or "./configs"
            parsed = config_parser.parse_all_configs(config_dir)
            G = topology_builder.build_topology(parsed)
            report = analyzer.analyze_network(G)
            print_msg(report["summary"])
        elif choice == "6":
            config_dir = input("Config directory [./configs]: ").strip() or "./configs"
            parsed = config_parser.parse_all_configs(config_dir)
            G = topology_builder.build_topology(parsed)
            autofix.generate_auto_fixes(G)
            print_msg("Auto-fixes generated.")
        elif choice == "7":
            config_dir = input("Config directory [./configs]: ").strip() or "./configs"
            parsed = config_parser.parse_all_configs(config_dir)
            G = topology_builder.build_topology(parsed)
            visualizer.draw_topology(G, path="./output/topology.png")
            print_msg("Topology drawn to ./output/topology.png")
        elif choice == "8":
            config_dir = input("Config directory [./configs]: ").strip() or "./configs"
            parsed = config_parser.parse_all_configs(config_dir)
            G = topology_builder.build_topology(parsed)
            simulator.run_day1_simulation(G)
        elif choice == "9":
            config_dir = input("Config directory [./configs]: ").strip() or "./configs"
            parsed = config_parser.parse_all_configs(config_dir)
            G = topology_builder.build_topology(parsed)
            link = input("Link to fail (NODE1-NODE2): ").strip()
            simulator.simulate_link_failure(G, link)
        elif choice == "0":
            print_msg("Exiting.")
            sys.exit(0)
        else:
            print_msg("Invalid choice.")


if __name__ == "__main__":
    try:
        interactive_menu()
    except KeyboardInterrupt:
        log.info("Interrupted by user. Exiting.")
        sys.exit(0)
