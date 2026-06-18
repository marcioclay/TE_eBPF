#!/bin/bash
# load_xdp.sh - Script único de gerenciamento de defesa

IFACE="eth1"
GATEWAY="clab-lab-ebpf-gateway"
# Caminho real do arquivo compilado dentro do container
PROG_PATH="/lab/scripts/xdp_monitor.o"
PIN_PATH="/sys/fs/bpf/xdp_monitor"

# Função de limpeza (usada antes de qualquer mudança de estado)
limpar_defesa() {
    echo "[*] Limpando ambiente de defesa anterior..."
    docker exec $GATEWAY iptables -F 2>/dev/null
    docker exec $GATEWAY ip link set dev $IFACE xdp off 2>/dev/null
    docker exec $GATEWAY rm -f $PIN_PATH 2>/dev/null
}

if [ "$1" == "xdp" ]; then
    limpar_defesa
    echo "[*] 2. Carregando e pinando o programa XDP..."
    docker exec $GATEWAY bpftool prog load $PROG_PATH $PIN_PATH type xdp
    
    echo "[*] 3. Anexando o filtro XDP à interface $IFACE..."
    docker exec $GATEWAY ip link set dev $IFACE xdpgeneric pinned $PIN_PATH
    echo "--- XDP ATIVADO ---"

elif [ "$1" == "iptables" ]; then
    limpar_defesa
    echo "[*] Ativando Mitigação via Iptables (DROP UDP 1883)..."
    docker exec $GATEWAY iptables -A INPUT -p udp --dport 1883 -j DROP
    echo "--- IPTABLES ATIVADO ---"

elif [ "$1" == "off" ]; then
    limpar_defesa
    echo "--- DEFESA DESATIVADA ---"
else
    echo "Uso: ./load_xdp.sh [xdp|iptables|off]"
fi
