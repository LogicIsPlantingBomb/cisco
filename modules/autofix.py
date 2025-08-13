# autofix.py
"""
autofix.py
Generate CLI-friendly config snippets that fix validation problems.
Writes suggestive files into ./auto_fixes/
"""

import os
from .logger import get_logger
from . import validator

log = get_logger("autofix")
AUTO_DIR = os.path.join(os.getcwd(), "auto_fixes")
os.makedirs(AUTO_DIR, exist_ok=True)


def generate_auto_fixes(G):
    issues = validator.validate_topology(G)
    fixes = []
    for i, issue in enumerate(issues, 1):
        # simple heuristics for generating fixes
        if "Duplicate IP" in issue:
            # suggest to change IP of second occurrence to .2 higher (very naive)
            fixes.append(f"! FIX {i}: {issue}\n! Suggestion: change IP on second interface to another unused address in subnet\n")
        elif "MTU mismatch" in issue:
            # extract nodes
            parts = issue.split()
            a = parts[2]
            b = parts[5]
            fixes.append(f"! FIX {i}: {issue}\ninterface <iface-on-{a}>\n mtu <match-value>\n")
        elif "Network loop" in issue:
            fixes.append(f"! FIX {i}: {issue}\n! Suggestion: enable STP on switches or remove redundant physical link\n")
        else:
            fixes.append(f"! FIX {i}: {issue}\n! Manual review required\n")

    # write fixes to file
    path = os.path.join(AUTO_DIR, "auto_fixes.txt")
    with open(path, "w") as f:
        for fix in fixes:
            f.write(fix + "\n")
    log.info(f"Wrote {len(fixes)} fixes to {path}")
    return fixes
