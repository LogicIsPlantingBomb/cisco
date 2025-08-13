import streamlit as st
import json
from pathlib import Path
from modules import (
    config_parser,
    topology_builder,
    validator,
    analyzer,
    autofix,
    visualizer,
    simulator
)

st.set_page_config(page_title="NetSimPro Dashboard", layout="wide")
st.title("NetSimPro Network Simulator Dashboard")

# Sidebar menu
option = st.sidebar.selectbox(
    "Choose an action",
    [
        "Upload Configs",
        "Run Full Pipeline",
        "Parse Configs Only",
        "Build Topology Only",
        "Validate Topology",
        "Analyze Network",
        "Generate Auto-Fixes",
        "Visualize Topology",
        "Simulate Day-1",
        "Simulate Link Failure",
        "Clear Uploaded Configs"
    ]
)

def load_sample_configs():
    sample_dir = "./configs"
    if Path(sample_dir).exists():
        sample_configs = config_parser.parse_all_configs(sample_dir)
        st.session_state['configs_data'] = sample_configs
        st.success(f"Loaded {len(sample_configs)} sample config files from '{sample_dir}'.")
        return sample_configs
    else:
        st.error(f"Sample config directory '{sample_dir}' not found. Please upload configs.")
        return None

# Clear uploaded configs
if option == "Clear Uploaded Configs":
    if 'configs_data' in st.session_state:
        del st.session_state['configs_data']
    st.success("Cleared uploaded configs. You can now upload new configs or use sample configs.")
    st.stop()

# Upload configs UI
if option == "Upload Configs":
    st.header("Upload your router config files (or choose to use sample configs)")
    uploaded_files = st.file_uploader(
        "Upload one or more .cfg or .txt config files",
        type=["cfg", "txt","json"],
        accept_multiple_files=True
    )
    use_sample = st.checkbox("Don't have files? Use sample configs to continue")

    if uploaded_files:
        configs_data = {}
        for file in uploaded_files:
            try:
                content = file.getvalue().decode("utf-8")
                if file.name.lower().endswith(".json"):
                    try:
                        content = json.loads(content)
                    except json.JSONDecodeError:
                        st.error(f"Invalid JSON format in {file.name}")
                        continue
            except UnicodeDecodeError:
                st.error(f"Could not decode {file.name}. Please upload UTF-8 encoded files.")
                continue
            configs_data[file.name] = content
        if configs_data:
            st.success(f"Successfully uploaded {len(configs_data)} config files.")
            st.session_state['configs_data'] = configs_data
    elif use_sample:
        configs_data = load_sample_configs()
    else:
        st.info("Please upload config files or select 'Use sample configs' to proceed.")

# For all other options, ensure configs_data is loaded
if option != "Upload Configs" and option != "Clear Uploaded Configs":
    if 'configs_data' not in st.session_state:
        st.info("No configs uploaded yet. Loading sample configs by default...")
        configs_data = load_sample_configs()
    else:
        configs_data = st.session_state['configs_data']
    if not configs_data:
        st.stop()


def run_topology_pipeline(configs):
    # Accepts dict of filename -> content or directory path string
    # For compatibility with your modules, adapt as needed
    if isinstance(configs, dict):
        # If configs is dict, parse each file content into structured config
        parsed_configs = {}
        for fname, content in configs.items():
            try:
                parsed_configs[fname] = config_parser.parse_config(content)
            except Exception as e:
                st.error(f"Error parsing {fname}: {e}")
                return None
        G = topology_builder.build_topology(parsed_configs)
    elif isinstance(configs, str):
        # If configs is a path, pass directly
        G = topology_builder.build_topology(configs)
    else:
        st.error("Invalid config format.")
        return None

    return G


if option == "Run Full Pipeline":
    st.header("Running Full Pipeline...")
    G = run_topology_pipeline(configs_data)
    if G.number_of_nodes() == 0:
        st.error("No topology nodes found. Check configs.")
        st.stop()
    
    st.success(f"Topology built: Nodes={G.number_of_nodes()}, Edges={G.number_of_edges()}")

    # Validation
    issues = validator.validate_topology(G)
    if issues:
        st.warning(f"Validation found {len(issues)} issue(s):")
        for issue in issues:
            st.write(f"- {issue}")
    else:
        st.success("No validation issues found.")

    # Analysis
    analysis = analyzer.analyze_network(G)
    st.info(f"Analysis Summary: {analysis['summary']}")

    # Auto-fixes
    fixes = autofix.generate_auto_fixes(G)
    st.success("Auto-fix suggestions generated.")

    # Visualization
    out_path = Path("output/topology.png")
    visualizer.draw_topology(G, path=str(out_path))
    st.image(str(out_path), caption="Network Topology")

elif option == "Parse Configs Only":
    st.header("Parsing Configs Only")
    if isinstance(configs_data, dict):
        st.write(f"Parsed {len(configs_data)} config files uploaded.")
    else:
        parsed = config_parser.parse_all_configs(configs_data)
        st.write(f"Parsed {len(parsed)} configs from sample directory.")

elif option == "Build Topology Only":
    st.header("Building Topology Only")
    G = run_topology_pipeline(configs_data)
    st.write(f"Built topology: nodes={G.number_of_nodes()}, edges={G.number_of_edges()}")

elif option == "Validate Topology":
    st.header("Validate Topology")
    G = run_topology_pipeline(configs_data)
    issues = validator.validate_topology(G)
    st.write(f"Issues found: {len(issues)}")
    for issue in issues:
        st.write(f"- {issue}")

elif option == "Analyze Network":
    st.header("Analyze Network")
    G = run_topology_pipeline(configs_data)
    analysis = analyzer.analyze_network(G)
    st.write(analysis['summary'])

elif option == "Generate Auto-Fixes":
    st.header("Generate Auto-Fixes")
    G = run_topology_pipeline(configs_data)
    autofix.generate_auto_fixes(G)
    st.success("Auto-fixes generated.")

elif option == "Visualize Topology":
    st.header("Visualize Topology")
    G = run_topology_pipeline(configs_data)
    out_path = Path("output/topology.png")
    visualizer.draw_topology(G, path=str(out_path))
    st.image(str(out_path), caption="Network Topology")

elif option == "Simulate Day-1":
    st.header("Simulate Day-1")
    G = run_topology_pipeline(configs_data)
    simulator.run_day1_simulation(G)
    st.success("Day-1 simulation complete.")

elif option == "Simulate Link Failure":
    st.header("Simulate Link Failure")
    G = run_topology_pipeline(configs_data)
    link = st.text_input("Enter link to fail (format: NODE1-NODE2)")
    if st.button("Simulate Failure"):
        if "-" not in link:
            st.error("Invalid link format. Use format like 'R1-R2'.")
        else:
            simulator.simulate_link_failure(G, link)
            st.success(f"Simulated failure for link: {link}")

