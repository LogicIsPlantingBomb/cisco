import os
from modules.config_parser import parse_all_configs

def read_links(links_file):
    """
    Reads links.txt file and returns list of endpoint tuples.
    Each endpoint is a string like 'R1:Gig0/0'.
    """
    links = []
    if not os.path.isfile(links_file):
        print(f"Links file not found: {links_file}")
        return links

    with open(links_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if '-' not in line:
                print(f"Skipping invalid link line (missing '-'): {line}")
                continue
            left, right = line.split('-', 1)
            left = left.strip()
            right = right.strip()
            links.append((left, right))
    return links


def check_links_vs_configs(parsed_configs, links):
    """
    Checks if devices and interfaces in links exist in parsed_configs.
    Prints missing devices and interfaces.
    """
    missing_devices = set()
    missing_interfaces = []

    for ep1, ep2 in links:
        for ep in [ep1, ep2]:
            if ":" not in ep:
                print(f"Invalid endpoint format (missing ':'): {ep}")
                continue
            dev, iface = ep.split(":", 1)
            dev = dev.strip()
            iface = iface.strip().lower()

            if dev not in parsed_configs:
                missing_devices.add(dev)
            else:
                interfaces = parsed_configs[dev].get("interfaces", {})
                normalized_ifaces = {k.lower() for k in interfaces.keys()}
                if iface not in normalized_ifaces:
                    missing_interfaces.append(f"{dev}:{iface}")

    if missing_devices:
        print("Missing devices in parsed configs:")
        for d in sorted(missing_devices):
            print(f" - {d}")
    else:
        print("No missing devices found.")

    if missing_interfaces:
        print("\nMissing interfaces in parsed configs:")
        for iface in sorted(missing_interfaces):
            print(f" - {iface}")
    else:
        print("No missing interfaces found.")


# Example usage:
if __name__ == "__main__":
    # parsed_configs should be imported or generated from your existing parser code
    # For example:
    # from your_project.config_parser import parse_all_configs
    # parsed_configs = parse_all_configs("path/to/configs")

    parsed_configs = {}  # <-- Replace this with actual parsed configs dict
    config_dir = "configs" 
    links_file_path = "configs/links.txt" # <-- Replace with your actual links.txt path
# Yeh wahi folder jahan aapke device config files hain
    parsed_configs = parse_all_configs(config_dir)
    links = read_links(links_file_path)
    check_links_vs_configs(parsed_configs, links)
    print("sorted first parsed_configs.keys() ",sorted(parsed_configs.keys()))
    print("second thing r4 interfaces",parsed_configs.get("R4", {}).get("interfaces", {}).keys())
    devices_from_links = set()
    for ep1, ep2 in links:
        dev1 = ep1.split(":", 1)[0].strip()
        dev2 = ep2.split(":", 1)[0].strip()
        devices_from_links.add(dev1)
        devices_from_links.add(dev2)
    for device in set(devices_from_links):
        print(device, sorted(k.lower() for k in parsed_configs[device]["interfaces"].keys()))

