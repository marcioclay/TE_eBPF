#!/bin/bash
# load_xdp.sh - Alterna entre iptables e XDP

IFACE="eth1"
GATEWAY="clab-lab-ebpf-gateway"

echo "[1/2] Limpando regras de firewall..."
docker exec $GATEWAY iptables -F 
docker exec $GATEWAY ip link set dev $IFACE xdpgeneric off 2>/dev/null || true

if [ "$1" == "xdp" ]; then
    echo "[2/2] Ativando Mitigação eBPF/XDP..."
    docker exec $GATEWAY bpftool prog load /lab/src/xdp_monitor.o /sys/fs/bpf/xdp_monitor
    docker exec $GATEWAY ip link set dev $IFACE xdpgeneric obj /sys/fs/bpf/xdp_monitor section xdp
    echo "--- XDP ATIVADO ---"
elif [ "$1" == "iptables" ]; then
    echo "[2/2] Ativando Mitigação via Iptables..."
    docker exec $GATEWAY iptables -A INPUT -p udp --dport 1883 -j DROP
    echo "--- IPTABLES ATIVADO ---"
else
    echo "Uso: ./load_xdp.sh [xdp|iptables]"
fi
