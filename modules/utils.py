# modules/utils.py
"""
utils.py
Common helper utilities used across modules.
"""

import ipaddress
from typing import Tuple


def ip_and_network(ip_str: str, mask_str: str) -> Tuple[str, str]:
    try:
        ip = ipaddress.IPv4Address(ip_str)
        net = ipaddress.IPv4Network(f"{ip_str}/{mask_str}", strict=False)
        return str(ip), str(net)
    except Exception:
        return ip_str, "0.0.0.0/0"


def is_same_subnet(ip1: str, mask1: str, ip2: str, mask2: str) -> bool:
    try:
        n1 = ipaddress.IPv4Network(f"{ip1}/{mask1}", strict=False)
        n2 = ipaddress.IPv4Network(f"{ip2}/{mask2}", strict=False)
        result = n1.network_address == n2.network_address and n1.prefixlen == n2.prefixlen
        log.debug(f"is_same_subnet: {ip1}/{mask1} vs {ip2}/{mask2} -> {result}")
        return result
    except Exception as e:
        log.warning(f"is_same_subnet failed for {ip1}/{mask1} vs {ip2}/{mask2}: {e}")
        return False



def ensure_dir(path: str):
    import os
    os.makedirs(path, exist_ok=True)
