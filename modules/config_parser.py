# modules/config_parser.py
"""
config_parser.py
Parses Cisco-like config dumps (.dump/.cfg/.txt) into structured dicts.

Outputs:
{ hostname: { "hostname": str, "interfaces": { ifname: {"ip":..., "mask":..., "mtu":..., "bandwidth":..., "vlan":..., "description":... }, ...},
"vlans": set(), "raw": str } }
"""

import os
import re
from typing import Dict
#sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from modules.logger import get_logger

log = get_logger("config_parser")


def parse_config_file(path: str) -> Dict:
    data = {
        "hostname": None,
        "interfaces": {},
        "vlans": set(),
        "raw": ""
    }
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        log.error("Failed to read %s: %s", path, e)
        return data
    data["raw"] = content
    # hostname
    m = re.search(r"^hostname\s+(\S+)", content, re.MULTILINE)
    if m:
        data["hostname"] = m.group(1).strip()
    else:
        data["hostname"] = os.path.splitext(os.path.basename(path))[0]
    # split interfaces
    blocks = re.split(r"(?m)^interface\s+", content)
    for block in blocks[1:]:
        lines = block.splitlines()
        if not lines:
            continue
        ifname = lines[0].strip().split()[0]
        block_text = "\n".join(lines[1:])
        entry = {}
        ipm = re.search(r"ip address\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)", block_text)
        if ipm:
            entry["ip"] = ipm.group(1)
            entry["mask"] = ipm.group(2)
        mt = re.search(r"\bmtu\s+(\d+)", block_text)
        if mt:
            entry["mtu"] = int(mt.group(1))
        bw = re.search(r"\bbandwidth\s+(\d+)", block_text)
        if bw:
            entry["bandwidth"] = int(bw.group(1))
        desc = re.search(r"description\s+(.+)", block_text)
        if desc:
            entry["description"] = desc.group(1).strip()
        vlan = re.search(r"switchport access vlan\s+(\d+)", block_text)
        if vlan:
            entry["vlan"] = int(vlan.group(1))
            data["vlans"].add(int(vlan.group(1)))
        data["interfaces"][ifname] = entry
    # vlan blocks
    for m in re.finditer(r"^vlan\s+(\d+)", content, re.MULTILINE):
        data["vlans"].add(int(m.group(1)))
    log.info("Parsed %s (%d interfaces, %d vlans)", data["hostname"], len(data["interfaces"]), len(data["vlans"]))
    return data


def parse_all_configs(dir_path: str) -> Dict[str, Dict]:
    result = {}
    if not os.path.isdir(dir_path):
        log.error("Config dir not found: %s", dir_path)
        return result
    for root, _, files in os.walk(dir_path):
        for f in files:
            if f.lower().endswith((".dump", ".cfg", ".txt")):
                path = os.path.join(root, f)
                parsed = parse_config_file(path)
                name = parsed.get("hostname") or os.path.splitext(f)[0]
                result[name] = parsed
    return result

def parse_links_file(path: str) -> list[tuple[str, str]]:
    """
    Parses a links file with format:
    device1:interface1 - device2:interface2
    Returns a sorted list of unique tuples with connected endpoints, all in lowercase.
    """
    links_set = set()
    
    if not os.path.isfile(path):
        log.error("Links file not found: %s", path)
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                
                if not line or line.startswith("#"):
                    continue
                if "-" not in line:
                    log.warning("Skipping invalid link line (missing '-'): %s", line)
                    continue
                
                left, right = line.split("-", 1)
                left = left.strip().lower()
                right = right.strip().lower()

                
                if ":" not in left or ":" not in right:
                    log.warning("Skipping invalid link line (missing ':'): %s", line)
                    continue

                links_set.add(tuple(sorted([left, right])))

    except Exception as e:
        log.error("Error reading links file %s: %s", path, e)

    links = sorted(links_set)
    log.info("Parsed %d unique links from %s", len(links), path)
    return links


import json

def parse_config(config_input):
    """
    Wrapper function that can parse:
    - JSON config file (string path or dict already loaded)
    - Old Cisco-like configs (folder path or .txt file)
    """

    # If already a dictionary → assume JSON already parsed
    if isinstance(config_input, dict):
        return config_input

    # If it's a string path
    if isinstance(config_input, str):
        if config_input.lower().endswith(".json"):
            # Parse JSON file
            try:
                with open(config_input, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                log.error("Failed to read JSON config %s: %s", config_input, e)
                return {}

        elif os.path.isdir(config_input):
            # Parse old-style configs from folder
            return parse_all_configs(config_input)

        elif os.path.isfile(config_input):
            # Single Cisco-like config file
            return {os.path.basename(config_input): parse_config_file(config_input)}

    log.error("Unsupported config input type: %s", type(config_input))
    return {}

