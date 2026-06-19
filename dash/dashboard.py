#!/usr/bin/env python3
import subprocess
import json
import time
import struct
import sys
import threading
import re

# ==========================================
# CONFIGURAÇÕES E CONSTANTES
# ==========================================
GATEWAY = "clab-lab-ebpf-gateway"
SENSOR = "clab-lab-ebpf-sensor"
IFACE = "eth1"
MAPA_ESTATISTICAS = "estatisticas_pr"

# Variáveis globais para partilha de dados
dados_qos = {"rtt": 0.0, "jitter": 0.0, "rtt_anterior": 0.0, "enviados": 0, "perdidos": 0}

def executar_cmd(comando, ignorar_erros=True):
    try:
        saida = subprocess.check_output(comando, shell=True, stderr=subprocess.DEVNULL)
        return saida.decode('utf-8').strip()
    except Exception:
        return "" if ignorar_erros else None

def ler_arquivo_container(container, caminho):
    return executar_cmd(f"sudo docker exec {container} cat {caminho}")

# ==========================================
# THREAD DE QOS (PING DO SENSOR)
# ==========================================
def thread_medir_qos():
    while True:
        saida = executar_cmd(f"sudo docker exec {SENSOR} ping -c 1 -W 1 10.0.0.1", ignorar_erros=True)
        dados_qos["enviados"] += 1
        
        match = re.search(r'time=([\d\.]+)\s*ms', saida)
        if match:
            rtt_atual = float(match.group(1))
            dados_qos["rtt"] = rtt_atual
            if dados_qos["rtt_anterior"] > 0:
                dados_qos["jitter"] = abs(rtt_atual - dados_qos["rtt_anterior"])
            dados_qos["rtt_anterior"] = rtt_atual
        else:
            dados_qos["perdidos"] += 1
            dados_qos["rtt"] = 0.0
            
        time.sleep(1)

# ==========================================
# DETEÇÃO DE CENÁRIO E MÉTRICAS
# ==========================================
def identificar_cenario():
    link_estado = executar_cmd(f"sudo docker exec {GATEWAY} ip link show dev {IFACE}")
    if link_estado and "xdp" in link_estado:
        return "eBPF/XDP"
    
    iptables = executar_cmd(f"sudo docker exec {GATEWAY} iptables -nvL INPUT")
    if iptables and "udp dpt:1883" in iptables and "DROP" in iptables:
        return "Iptables"
        
    return "SEM DEFESA"

def buscar_id_mapa(nome_mapa):
    saida = executar_cmd(f"sudo docker exec {GATEWAY} bpftool map show -j")
    if saida:
        try:
            for mapa in json.loads(saida):
                if nome_mapa in mapa.get("name", ""):
                    return mapa.get("id")
        except: pass
    return None

def ler_metricas_xdp(id_mapa):
    saida = executar_cmd(f"sudo docker exec {GATEWAY} bpftool map dump id {id_mapa} -j")
    if not saida: return 0
    try:
        pacotes = 0
        for entrada in json.loads(saida):
            chave = struct.unpack("<I", bytes.fromhex(entrada.get('key', '').replace(" ", "")))[0]
            if chave == 0: 
                p, _ = struct.unpack("<QQ", bytes.fromhex(entrada.get('value', '').replace(" ", "")))
                pacotes = p
        return pacotes
    except: return 0

def ler_metricas_iptables():
    saida = executar_cmd(f"sudo docker exec {GATEWAY} iptables -nvL INPUT -x")
    for linha in saida.split('\n'):
        if "udp dpt:1883" in linha and "DROP" in linha:
            return int(linha.split()[0])
    return 0

# ==========================================
# INTERFACE PRINCIPAL
# ==========================================
def iniciar_painel():
    id_estatisticas = buscar_id_mapa(MAPA_ESTATISTICAS)
    estado_anterior = {
        "rx_pkts": int(ler_arquivo_container(GATEWAY, f"/sys/class/net/{IFACE}/statistics/rx_packets") or 0),
        "drop_pkts": 0
    }
    
    print("\033c--- A INICIAR PAINEL DE REDE E QoS ---")
    time.sleep(1)
    
    try:
        while True:
            cenario = identificar_cenario()
            
            rx_pkts_atual = int(ler_arquivo_container(GATEWAY, f"/sys/class/net/{IFACE}/statistics/rx_packets") or 0)
            pps_recebido = max(0, rx_pkts_atual - estado_anterior["rx_pkts"])
            
            pkts_bloqueados_total = 0
            if cenario == "eBPF/XDP" and id_estatisticas:
                pkts_bloqueados_total = ler_metricas_xdp(id_estatisticas)
            elif cenario == "Iptables":
                pkts_bloqueados_total = ler_metricas_iptables()
                
            pps_bloqueado = max(0, pkts_bloqueados_total - estado_anterior["drop_pkts"])
            
            # Cálculo da Taxa de Mitigação (%)
            taxa_mitigacao = 0.0
            if pps_recebido > 0 and pps_bloqueado > 0:
                taxa_mitigacao = (pps_bloqueado / pps_recebido) * 100
                taxa_mitigacao = min(100.0, taxa_mitigacao) # Limita a 100% por questões de arredondamento

            taxa_perda = (dados_qos["perdidos"] / dados_qos["enviados"]) * 100 if dados_qos["enviados"] > 0 else 0.0
            estado_sensor = "ONLINE" if dados_qos["rtt"] > 0 else "OFFLINE / TIMEOUT"
            
            print("\033c" + "="*55)
            print(" PAINEL DE MITIGAÇÃO DDoS E QoS ".center(55))
            print("="*55)
            print(f" Cenário Ativo   : {cenario}")
            print("-" * 55)
            print(" [ ANÁLISE DE TRÁFEGO ]")
            print(f" Tráfego Recebido (eth1) : {pps_recebido:>8} PPS")
            print(f" Pacotes Bloqueados      : {pps_bloqueado:>8} PPS")
            print(f" Taxa de Mitigação       : {taxa_mitigacao:>8.2f} %")
            print("-" * 55)
            print(" [ QUALIDADE DE SERVIÇO (QoS) - SENSOR ]")
            print(f" Disponibilidade : {estado_sensor}")
            print(f" Latência (RTT)  : {dados_qos['rtt']:>6.2f} ms")
            print(f" Jitter          : {dados_qos['jitter']:>6.2f} ms")
            print(f" Pacotes Perdidos: {taxa_perda:>6.1f} %")
            print("="*55)
            
            estado_anterior["rx_pkts"] = rx_pkts_atual
            estado_anterior["drop_pkts"] = pkts_bloqueados_total
            time.sleep(1)
            
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    t_qos = threading.Thread(target=thread_medir_qos, daemon=True)
    t_qos.start()
    iniciar_painel()
