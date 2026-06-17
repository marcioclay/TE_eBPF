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
    except: pass
    return None

def get_proto_metrics(map_id):
    # Índice 0 = UDP (Ataque), Índice 1 = TCP (Legítimo)
    try:
        out = subprocess.check_output(["bpftool", "map", "dump", "id", str(map_id), "-j"], stderr=subprocess.DEVNULL)
        data = json.loads(out)
        metrics = {0: {"pkts": 0, "bytes": 0}, 1: {"pkts": 0, "bytes": 0}}
        for entry in data:
            key = struct.unpack("<I", bytes.fromhex(entry['key']))[0]
            pkts, bts = struct.unpack("<QQ", bytes.fromhex(entry['value']))
            if key in metrics:
                metrics[key] = {"pkts": pkts, "bytes": bts}
        return metrics
    except: return None

def tela_ddos(id_proto):
    print("\033c--- MONITORAMENTO DE ATAQUE DDoS (UDP FLOOD) ---")
    while True:
        m = get_proto_metrics(id_proto)
        if m:
            pps = m[0]["pkts"] # Aqui você pode adicionar um delta de tempo para PPS real
            mbps = (m[0]["bytes"] * 8) / (1024 * 1024)
            print(f"-> Taxa de Bloqueio (UDP): {m[0]['pkts']} pacotes")
            print(f"-> Banda Descartada     : {mbps:.2f} Mbps")
            print(f"-> Tráfego Legítimo (TCP): {m[1]['pkts']} pacotes")
        print("\nPressione Ctrl+C para voltar ao menu.")
        time.sleep(1)

def main():
    id_proto = get_map_id(MAP_PROTO)
    if id_proto is None:
        print("Erro: Mapa proto_stats não encontrado.")
        sys.exit(1)

    while True:
        print("\033c" + "="*50)
        print("   DASHBOARD DE DEFESA IoT (Foco em DDoS)")
        print("="*50)
        print(" 1. Monitorar Ataque DDoS em Tempo Real")
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
