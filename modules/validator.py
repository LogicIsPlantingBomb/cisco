# validator.py
"""
validator.py
Validate topology and configs for issues:
- Duplicate IPs within same VLAN
- MTU mismatches
- Wrong gateway hints (simple check)
- Network loops detection
Return list of issue descriptions.
"""

from .logger import get_logger
from collections import defaultdict
import networkx as nx

log = get_logger("validator")


def validate_topology(G):
    """
    Walk graph G (NetworkX Graph). Uses node attribute 'parsed' (dict from config_parser).
    Returns list of issues (strings).
    """
    issues = []

    # 1) Duplicate IPs per VLAN
    vlan_ips = defaultdict(list)
    for node, data in G.nodes(data=True):
        parsed = data.get("parsed", {})
        for iface, ifd in parsed.get("interfaces", {}).items():
            vlan = ifd.get("vlan")
            ip = ifd.get("ip")
            if vlan and ip:
                vlan_ips[vlan].append((node, iface, ip))
    for vlan, lst in vlan_ips.items():
        seen = {}
        for node, iface, ip in lst:
            if ip in seen:
                issues.append(f"Duplicate IP {ip} in VLAN {vlan}: {seen[ip]} and {node}:{iface}")
            else:
                seen[ip] = f"{node}:{iface}"

    # 2) MTU mismatches on edges
    for u, v, attr in G.edges(data=True):
        mtu_u = _node_iface_mtu_to_neighbor(G, u, v)
        mtu_v = _node_iface_mtu_to_neighbor(G, v, u)
        if mtu_u and mtu_v and mtu_u != mtu_v:
            issues.append(f"MTU mismatch between {u} ({mtu_u}) and {v} ({mtu_v})")

    # 3) Wrong gateways (basic heuristic: interface IP not in neighbor's subnet)
    # We try to detect endpoints with default-gateway not in subnet - requires explicit default-gw info in parsed (rare)
    for node, data in G.nodes(data=True):
        parsed = data.get("parsed", {})
        dg = parsed.get("default_gateway")
        if dg:
            # check if any local interface belongs to gateway's subnet
            ok = False
            for iface, ifd in parsed.get("interfaces", {}).items():
                ip = ifd.get("ip")
                mask = ifd.get("mask")
                if ip and mask:
                    try:
                        import ipaddress
                        net = ipaddress.IPv4Network(f"{ip}/{mask}", strict=False)
                        if ipaddress.IPv4Address(dg) in net:
                            ok = True
                            break
                    except Exception:
                        pass
            if not ok:
                issues.append(f"Default gateway {dg} on {node} not in any local interface subnet")

    # 4) Network loops (simple cycle detection)
    try:
        cycles = list(nx.cycle_basis(G))
        if cycles:
            for c in cycles:
                issues.append(f"Network loop detected among nodes: {' -> '.join(c)}")
    except Exception as e:
        log.error("Cycle detection error: %s", e)

    log.info("Validation complete, %d issues found", len(issues))
    return issues


def _node_iface_mtu_to_neighbor(G, node, neighbor):
    """
    Try to find an interface on 'node' whose description mentions neighbor or whose ip shares subnet.
    Returns MTU int or None.
    """
    parsed = G.nodes[node].get("parsed", {})
    # try description
    for iface, ifd in parsed.get("interfaces", {}).items():
        desc = ifd.get("description", "")
        if desc and neighbor in desc:
            if "mtu" in ifd:
                return ifd.get("mtu")
    # fallback: if both have ip on same subnet, return that mtu
    for iface, ifd in parsed.get("interfaces", {}).items():
        if "ip" in ifd and "mask" in ifd:
            # check neighbor interfaces for subnet overlap
            nparsed = G.nodes[neighbor].get("parsed", {})
            for niface, nifd in nparsed.get("interfaces", {}).items():
                if "ip" in nifd and "mask" in nifd:
                    try:
                        import ipaddress
                        net1 = ipaddress.IPv4Network(f"{ifd['ip']}/{ifd['mask']}", strict=False)
                        net2 = ipaddress.IPv4Network(f"{nifd['ip']}/{nifd['mask']}", strict=False)
                        if net1.network_address == net2.network_address:
                            return ifd.get("mtu") or nifd.get("mtu")
                    except Exception:
                        pass
    return None


