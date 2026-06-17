#!/usr/bin/env python3
import subprocess
import json
import time
import struct
import sys

MAP_PROTO = "proto_stats"

def get_map_id(name):
    try:
        out = subprocess.check_output(["bpftool", "map", "show", "-j"], stderr=subprocess.DEVNULL)
        for m in json.loads(out):
            if m.get("name") == name: return m.get("id")
    except: return None
    return None

def get_proto_metrics(map_id):
    try:
        out = subprocess.check_output(["bpftool", "map", "dump", "id", str(map_id), "-j"], stderr=subprocess.DEVNULL)
        data = json.loads(out)
        # Inicializa estrutura
        res = {0: {"pkts": 0, "bytes": 0}, 1: {"pkts": 0, "bytes": 0}}
        for entry in data:
            key = struct.unpack("<I", bytes.fromhex(entry['key']))[0]
            # O valor do array tem 16 bytes (dois uint64: pkts e bytes)
            v = bytes.fromhex(entry['value'])
            pkts, bts = struct.unpack("<QQ", v)
            if key in res: res[key] = {"pkts": pkts, "bytes": bts}
        return res
    except: return None

def tela_ddos(id_proto):
    print("\033c--- MONITORAMENTO DE ATAQUE DDoS (CÁLCULO DE PPS) ---")
    
    # Valores iniciais para cálculo de delta
    prev = get_proto_metrics(id_proto)
    time.sleep(1)
    
    while True:
        curr = get_proto_metrics(id_proto)
        if curr and prev:
            # Cálculo de Delta
            delta_pkts_udp = curr[0]["pkts"] - prev[0]["pkts"]
            delta_bytes_udp = curr[0]["bytes"] - prev[0]["bytes"]
            
            pps = delta_pkts_udp
            mbps = (delta_bytes_udp * 8) / (1024 * 1024)
            
            print(f"\033c--- MONITORAMENTO EM TEMPO REAL ---")
            print(f"Taxa de Bloqueio (UDP): {pps:>10} PPS")
            print(f"Banda Descartada      : {mbps:>10.2f} Mbps")
            print(f"Tráfego Legítimo (TCP): {curr[1]['pkts']:>10} Pacotes totais")
            print("\nPressione Ctrl+C para voltar ao menu.")
            
            prev = curr
        time.sleep(1)

def main():
    id_proto = get_map_id(MAP_PROTO)
    if not id_proto:
        print("Erro: Mapa não encontrado. Verifique se o XDP está carregado.")
        sys.exit(1)

    while True:
        print("\033c" + "="*50)
        print("   DASHBOARD DE DEFESA IoT (Benchmark)")
        print("="*50)
        print(" 1. Iniciar Monitoramento DDoS (Cálculo PPS)")
        print(" 2. Sair")
        print("="*50)
        
        escolha = input("\n Selecione: ").strip()
        if escolha == '1':
            try: tela_ddos(id_proto)
            except KeyboardInterrupt: continue
        elif escolha == '2':
            sys.exit(0)

if __name__ == "__main__":
    main()
