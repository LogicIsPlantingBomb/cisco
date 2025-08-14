# Network Topology Simulation and Analysis Tool

## Overview

This **Network Topology Simulation and Analysis Tool** is a lightweight, modular, and interactive CLI-based Python application designed for quickly creating, analyzing, and simulating various network topologies.

It supports both predefined and custom topologies, provides built-in network analysis metrics, and allows users to simulate node failures, compare designs, and visualize networks in a simple text-based format without requiring heavy graphics libraries.

---

## Features

* **Quick Topology Creation:** Predefined sizes (small / medium / large) for fast setup.
* **Multiple Topology Types:**

  * Star Topology (Hub-and-spoke)
  * Ring Topology (Circular)
  * Full / Partial Mesh (All-to-all or selective)
  * Tree Topology (Hierarchical)
  * Spine-Leaf (Modern data center)
  * Bus Topology (Linear)
  * Hybrid Topology (Combination of multiple types)
* **Network Analysis:** Connectivity, network diameter, clustering coefficient.
* **Text-Based Visualization:** Works without graphics libraries.
* **Export Summaries:** Save topology details and metrics to a file.
* **Node Failure Simulation:** Test network robustness and resilience.
* **Topology Comparison Tool:** Compare performance and structure of different designs.
* **Custom Topology Builder:** Define your own nodes and connections.

---

## Getting Started

### Prerequisites

* Python 3.8 or higher
* Recommended: Virtual environment (`venv` or `conda`)
* **Required Package:**

  ```bash
  pip install networkx
  ```

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/network-topology-tool.git
cd network-topology-tool
```

2. Set up and activate a virtual environment:

```bash
python -m venv venv
# Windows
denv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Usage

Run the main CLI program:

```bash
python main.py
```

Follow the interactive menu to:

* Create a topology (predefined or custom)
* Select topology type and size
* Analyze network metrics
* Visualize the topology in text form
* Simulate node failure and check resilience
* Compare different topology designs
* Export summaries for documentation

**Example:**

* Create a spine-leaf topology: `Option 1 → 6 → medium`
* Analyze network resilience: `Create topology → Option 5 → Enter node name`
* Compare designs: `Option 6`

---

## Project Structure

```
network-topology-tool/
├── configs/                 # Sample or saved topology configurations
├── modules/                 # Core Python modules for functionality
│   ├── topology_builder.py  # Predefined + custom topology creation
│   ├── analyzer.py          # Network metrics calculation
│   ├── simulator.py         # Node failure simulation
│   ├── visualizer.py        # Text-based visualization
│   ├── exporter.py          # Export summaries
│   ├── comparator.py        # Compare topology designs
│   ├── logger.py            # Logging utility
│   └── utils.py             # Helper functions
├── output/                  # Exported summaries and reports
├── main.py                  # CLI menu system
├── README.md
├── requirements.txt
└── .gitignore
```

---

## Future Enhancements

* Add minimal GUI support for basic visualization
* Include real-time topology editing
* Introduce cost and latency analysis for links
* Extend failure simulation to multiple nodes/links

---

**Built By Dhruv Bhardwaj**

---

## Acknowledgments

* Inspired by network topology design principles and practical engineering use cases.
* Built using the NetworkX Python library for graph-based network modeling.
