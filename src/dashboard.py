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
        res = {0: {"pkts": 0, "bytes": 0}, 1: {"pkts": 0, "bytes": 0}}
        for entry in data:
            key = struct.unpack("<I", bytes.fromhex(entry['key']))[0]
            v = bytes.fromhex(entry['value'])
            pkts, bts = struct.unpack("<QQ", v)
            if key in res: res[key] = {"pkts": pkts, "bytes": bts}
        return res
    except: return None

def tela_ddos(id_proto):
    print("\033c--- MONITORAMENTO EM TEMPO REAL: DDoS com IP Spoofing ---")
    
    prev = get_proto_metrics(id_proto)
    time.sleep(1)
    
    while True:
        try:
            curr = get_proto_metrics(id_proto)
            if curr and prev:
                # Delta para taxa instantânea
                delta_pkts = curr[0]["pkts"] - prev[0]["pkts"]
                delta_bytes = curr[0]["bytes"] - prev[0]["bytes"]
                
                mbps = (delta_bytes * 8) / (1024 * 1024)
                
                print(f"\033c--- MONITORAMENTO DDoS (IP Spoofing) ---")
                print(f"Taxa de Bloqueio (UDP): {delta_pkts:>10} PPS")
                print(f"Banda Descartada      : {mbps:>10.2f} Mbps")
                print(f"Tráfego Legítimo (TCP): {curr[1]['pkts']:>10} Pacotes acumulados")
                print("\n[Nota]: O PPS reflete o bloqueio de tráfego spoofed em tempo real.")
                print("\n(Pressione Ctrl+C para voltar ao menu)")
                
                prev = curr
            time.sleep(1)
        except KeyboardInterrupt:
            break

def main():
    id_proto = get_map_id(MAP_PROTO)
    if not id_proto:
        print("Erro: Mapa proto_stats não encontrado.")
        sys.exit(1)

    while True:
        print("\033c" + "="*50)
        print("   DASHBOARD DE DEFESA IoT (Dissertação)")
        print("="*50)
        print(" 1. Iniciar Monitoramento de Ataque (PPS)")
        print(" 2. Sair")
        print("="*50)
        
        escolha = input("\n Selecione: ").strip()
        if escolha == '1': tela_ddos(id_proto)
        elif escolha == '2': sys.exit(0)

if __name__ == "__main__":
    main()
