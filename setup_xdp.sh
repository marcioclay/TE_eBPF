#!/bin/bash

# Interrompe a execução caso algum comando falhe
set -e

echo "=================================================="
echo "🛡️ CONFIGURANDO O ESCUDO XDP (eBPF) NO GATEWAY"
echo "=================================================="

echo "[*] 1. Limpando o diretório de pins antigo..."
sudo docker exec -it clab-lab-ebpf-gateway rm -f /sys/fs/bpf/xdp_monitor_test

echo "[*] 2. Carregando e pinando o novo programa eBPF no Kernel..."
sudo docker exec -it clab-lab-ebpf-gateway bpftool prog load /lab/xdp_monitor.o /sys/fs/bpf/xdp_monitor_test type xdp

echo "[*] 3. Anexando o filtro XDP à placa de rede (eth1)..."
sudo docker exec -it clab-lab-ebpf-gateway ip link set dev eth1 xdpgeneric pinned /sys/fs/bpf/xdp_monitor_test

echo "[+] Concluído! O XDP está ativo e a intercetar os pacotes na placa de rede."
echo "=================================================="
