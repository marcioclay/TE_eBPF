#!/bin/bash
set -e

echo "=================================================="
echo "1. PREPARANDO GATEWAY (Configuração de Rede e Dependências)"
echo "=================================================="
docker exec clab-lab-ebpf-gateway apt-get update
# Mantemos o iptables para o seu comparativo de benchmark
docker exec clab-lab-ebpf-gateway apt-get install -y iptables iproute2

echo "=================================================="
echo "2. PREPARANDO AMBIENTE DE SIMULAÇÃO (Atacante & Sensor)"
echo "=================================================="
for node in clab-lab-ebpf-atacante clab-lab-ebpf-sensor; do
    docker exec $node apt-get update
    docker exec $node apt-get install -y python3 python3-pip iproute2
    docker exec $node pip3 install paho-mqtt
done

echo "=================================================="
echo "3. EMULANDO CONDIÇÕES DE REDE (Wi-Fi/Edge Computing)"
echo "=================================================="
# Limpeza de regras anteriores
docker exec clab-lab-ebpf-sensor tc qdisc del dev eth1 root 2>/dev/null || true
docker exec clab-lab-ebpf-atacante tc qdisc del dev eth1 root 2>/dev/null || true

# Aplica latência e perda ao sensor (simulando um ambiente real de IoT)
docker exec clab-lab-ebpf-sensor tc qdisc add dev eth1 root netem delay 30ms 5ms loss 1%

echo "=================================================="
echo "🎉 INFRAESTRUTURA LIMPA E PRONTA PARA TESTES DE DDoS!"
echo "=================================================="
