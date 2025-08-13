import os

# Base directory for all devices
base_dir = "configs"
os.makedirs(base_dir, exist_ok=True)

# Router configs (R6 onwards)
start_router = 6
total_routers = 6  # R6 to R11
for i in range(start_router, start_router + total_routers):
    name = f"R{i}"
    folder = os.path.join(base_dir, name)
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "config.dump"), "w") as f:
        f.write(f"hostname {name}\n")
        f.write("!\n")
        f.write("interface Gig0/0\n")
        f.write(f" ip address 10.{i}.0.1 255.255.255.0\n")
        f.write(" no shutdown\n")
        f.write("!\n")
        f.write("interface Gig0/1\n")
        f.write(f" ip address 10.{i}.1.1 255.255.255.0\n")
        f.write(" no shutdown\n")

# Switch configs
switch_count = 3
for i in range(1, switch_count + 1):
    name = f"S{i}"
    folder = os.path.join(base_dir, name)
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "config.dump"), "w") as f:
        f.write(f"hostname {name}\n")
        f.write("!\n")
        for port in range(1, 5):
            f.write(f"interface Fa0/{port}\n switchport mode access\n!\n")

# Modem configs
modem_count = 1
for i in range(1, modem_count + 1):
    name = f"M{i}"
    folder = os.path.join(base_dir, name)
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "config.dump"), "w") as f:
        f.write(f"hostname {name}\n")
        f.write("!\ninterface Eth0\n ip address 192.168.{i}.1 255.255.255.0\n no shutdown\n")

# Firewall configs
firewall_count = 1
for i in range(1, firewall_count + 1):
    name = f"FW{i}"
    folder = os.path.join(base_dir, name)
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "config.dump"), "w") as f:
        f.write(f"hostname {name}\n")
        f.write("!\ninterface WAN\n ip address 192.168.{i}.2 255.255.255.0\n no shutdown\n")
        f.write("interface LAN\n ip address 10.100.{i}.1 255.255.255.0\n no shutdown\n")

# Server configs
server_count = 2
for i in range(1, server_count + 1):
    name = f"Server{i}"
    folder = os.path.join(base_dir, name)
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "config.dump"), "w") as f:
        f.write(f"hostname {name}\n")
        f.write(f"!\ninterface Eth0\n ip address 10.200.{i}.1 255.255.255.0\n no shutdown\n")

# PC configs
pc_count = 2
for i in range(1, pc_count + 1):
    name = f"PC{i}"
    folder = os.path.join(base_dir, name)
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "config.dump"), "w") as f:
        f.write(f"hostname {name}\n")
        f.write(f"!\ninterface Eth0\n ip address 10.150.{i}.2 255.255.255.0\n no shutdown\n")

print(f"✅ All device folders and configs created inside '{base_dir}'")
