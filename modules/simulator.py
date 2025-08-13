"""
simulator.py
Simple multithreaded simulation:
- Each device is a thread
- A central broker (in-memory) relays metadata messages
- Simulates Day-1: ARP broadcast and OSPF hello (conceptually)
- Supports link failure toggling
- Collects and returns logs as string for UI display
"""

import threading
import time
from queue import Queue, Empty
from .logger import get_logger
import networkx as nx

log = get_logger("simulator")
BROKER_QUEUE = Queue()
STOP_EVENT = threading.Event()

# Thread-safe log collector class
class LogCollector:
    def __init__(self):
        self.lock = threading.Lock()
        self.logs = []

    def append(self, msg):
        with self.lock:
            self.logs.append(msg)

    def get_logs(self):
        with self.lock:
            return "\n".join(self.logs)

# Global log collector instance per simulation run
log_collector = None

class DeviceThread(threading.Thread):
    def __init__(self, name, graph, inbox: Queue):
        super().__init__(daemon=True)
        self.name = name
        self.graph = graph
        self.inbox = inbox
        self.running = True

    def run(self):
        global log_collector
        log_msg = f"[Sim] Device {self.name} started"
        log.info(log_msg)
        if log_collector:
            log_collector.append(log_msg)

        # initial boot: send ARP/HELLO to neighbors
        neighbors = list(self.graph.neighbors(self.name))
        for n in neighbors:
            msg = {"type": "HELLO", "src": self.name, "dst": n, "time": time.time()}
            BROKER_QUEUE.put(msg)
            log_msg = f"[{self.name}] sent HELLO to {n}"
            log.info(log_msg)
            if log_collector:
                log_collector.append(log_msg)

        # event loop
        while self.running and not STOP_EVENT.is_set():
            try:
                msg = self.inbox.get(timeout=0.5)
            except Empty:
                time.sleep(0.1)
                continue

            # process msg
            if msg["type"] == "HELLO":
                log_msg = f"[{self.name}] Received HELLO from {msg['src']}"
                log.info(log_msg)
                if log_collector:
                    log_collector.append(log_msg)
            elif msg["type"] == "ARP":
                if msg["dst"] == self.name:
                    r = {"type": "ARP_REPLY", "src": self.name, "dst": msg["src"], "time": time.time()}
                    BROKER_QUEUE.put(r)
                    log_msg = f"[{self.name}] sent ARP_REPLY to {msg['src']}"
                    log.info(log_msg)
                    if log_collector:
                        log_collector.append(log_msg)
            time.sleep(0.01)

    def stop(self):
        self.running = False
        log_msg = f"[Sim] Device {self.name} stopped"
        log.info(log_msg)
        if log_collector:
            log_collector.append(log_msg)

def broker_dispatch(graph, inbox_map):
    """Dispatch messages from BROKER_QUEUE to appropriate device inboxes."""
    global log_collector
    while not STOP_EVENT.is_set():
        try:
            msg = BROKER_QUEUE.get(timeout=0.5)
        except Empty:
            continue
        dst = msg.get("dst")
        if dst in inbox_map:
            inbox_map[dst].put(msg)
            if log_collector:
                log_collector.append(f"[Broker] Dispatched {msg['type']} from {msg['src']} to {dst}")
        else:
            # broadcast or unknown destination
            if dst is None:
                src = msg.get("src")
                for n in graph.neighbors(src):
                    inbox_map[n].put(msg)
                    if log_collector:
                        log_collector.append(f"[Broker] Broadcast {msg['type']} from {src} to {n}")
        time.sleep(0.01)

def run_day1_simulation(G, duration=5):
    """
    Runs the Day-1 simulation for given duration (seconds).
    Returns a string of the log messages.
    """
    global log_collector
    log_collector = LogCollector()

    STOP_EVENT.clear()
    inbox_map = {node: Queue() for node in G.nodes()}
    threads = {}

    for node in G.nodes():
        t = DeviceThread(node, G, inbox_map[node])
        t.start()
        threads[node] = t

    broker = threading.Thread(target=broker_dispatch, args=(G, inbox_map), daemon=True)
    broker.start()

    start_msg = "Simulation started for Day-1"
    log.info(start_msg)
    log_collector.append(start_msg)

    time.sleep(duration)

    STOP_EVENT.set()

    for t in threads.values():
        t.stop()

    end_msg = "Simulation ended"
    log.info(end_msg)
    log_collector.append(end_msg)

    # Return collected logs as string for UI display
    return log_collector.get_logs()

def _simulate_link_failure(G, link_key: str):
    global log_collector
    if log_collector is None:
        log_collector = LogCollector()

    try:
        a, b = link_key.split("-")
    except Exception:
        err_msg = "Invalid link format. Use format like 'R1-R2'."
        log.error(err_msg)
        log_collector.append(err_msg)
        return

    if G.has_edge(a, b):
        G[a][b]["up"] = False
        warn_msg = f"Link {a}-{b} brought down"
        log.warning(warn_msg)
        log_collector.append(warn_msg)

        comps = list(nx.connected_components(G))
        if len(comps) > 1:
            part_msg = "Network partition occurred:"
            log.warning(part_msg)
            log_collector.append(part_msg)
            for comp in comps:
                comp_msg = f"Component: {comp}"
                log.warning(comp_msg)
                log_collector.append(comp_msg)
    else:
        err_msg = "No such edge"
        log.error(err_msg)
        log_collector.append(err_msg)



def simulate_link_failure(G, link_key: str):
    """
    Public API function for link failure simulation.
    Returns string logs.
    """
    global log_collector
    log_collector = LogCollector()  # reset logs for each simulation run

    _simulate_link_failure(G, link_key)

    return log_collector.get_logs()

# Optional helper for Streamlit app to get logs live (if needed)
def get_sim_logs():
    global log_collector
    if log_collector:
        return log_collector.logs.copy()
    return []
