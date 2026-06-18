#!/usr/bin/env python3
import subprocess
import json
import time
import struct
import sys

# Nomes dos mapas no kernel (podem estar abreviados pelo eBPF)
MAPA_ESTATISTICAS = "estatisticas_pr"
MAPA_IPS = "ips_detectados"
CONTAINER_GATEWAY = "clab-lab-ebpf-gateway"

def executar_bpftool(*argumentos):
    """Executa o comando bpftool dentro do container do gateway IoT."""
    comando = ["sudo", "docker", "exec", CONTAINER_GATEWAY, "bpftool"] + list(argumentos)
    try:
        saida = subprocess.check_output(comando, stderr=subprocess.DEVNULL)
        return saida.decode('utf-8')
    except Exception:
        return None

def buscar_id_mapa(nome_mapa):
    """Busca o ID numérico do mapa pelo nome."""
    saida = executar_bpftool("map", "show", "-j")
    if not saida:
        return None
        
    try:
        mapas = json.loads(saida)
        for mapa in mapas:
            # Verifica se o nome desejado faz parte do nome registrado no kernel
            if nome_mapa in mapa.get("name", ""):
                return mapa.get("id")
    except json.JSONDecodeError:
        pass
    return None

def ler_metricas_protocolo(id_mapa):
    """Lê pacotes e bytes do mapa de estatísticas (UDP vs TCP)."""
    saida = executar_bpftool("map", "dump", "id", str(id_mapa), "-j")
    if not saida:
        return None

    # Estrutura base: chave 0 = UDP (Bloqueado), chave 1 = TCP (Legítimo)
    metricas = {
        0: {"pacotes": 0, "bytes": 0}, 
        1: {"pacotes": 0, "bytes": 0}
    }
    
    try:
        dados = json.loads(saida)
        for entrada in dados:
            # O bpftool retorna hexadecimal com espaços, precisamos removê-los
            hex_chave = entrada.get('key', '').replace(" ", "")
            hex_valor = entrada.get('value', '').replace(" ", "")
            
            if not hex_chave or not hex_valor:
                continue

            # Decodifica a chave (inteiro de 4 bytes) e os valores (dois inteiros de 8 bytes)
            chave = struct.unpack("<I", bytes.fromhex(hex_chave))[0]
            pacotes, total_bytes = struct.unpack("<QQ", bytes.fromhex(hex_valor))
            
            if chave in metricas:
                metricas[chave] = {"pacotes": pacotes, "bytes": total_bytes}
                
        return metricas
    except Exception:
        return None

def contar_ips_unicos(id_mapa_ips):
    """Retorna a quantidade de IPs de origem distintos registrados."""
    if not id_mapa_ips:
        return 0
        
    saida = executar_bpftool("map", "dump", "id", str(id_mapa_ips), "-j")
    if not saida:
        return 0
        
    try:
        dados = json.loads(saida)
        # Cada entrada no JSON representa um IP diferente que enviou tráfego
        return len(dados)
    except json.JSONDecodeError:
        return 0

def monitorar_ataque(id_estatisticas, id_ips):
    """Loop principal de exibição em tempo real do ataque."""
    print("\033c--- INICIANDO MONITORAMENTO DE DEFESA IoT ---")
    print("Aguardando a coleta dos primeiros pacotes...\n")
    
    estado_anterior = ler_metricas_protocolo(id_estatisticas)
    time.sleep(1)
    
    while True:
        try:
            estado_atual = ler_metricas_protocolo(id_estatisticas)
            
            if estado_atual and estado_anterior:
                # Calcula a taxa instantânea subtraindo a leitura anterior da atual
                pacotes_udp = estado_atual[0]["pacotes"] - estado_anterior[0]["pacotes"]
                bytes_udp = estado_atual[0]["bytes"] - estado_anterior[0]["bytes"]
                
                # Converte os bytes bloqueados para Megabits por segundo (Mbps)
                mbps = (bytes_udp * 8) / (1024 * 1024)
                
                total_ips = contar_ips_unicos(id_ips)
                pacotes_tcp = estado_atual[1]["pacotes"]
                
                # Atualiza a interface gráfica no terminal
                print("\033c" + "="*55)
                print(" MONITORAMENTO DE ATAQUE DDoS (IP Spoofing)".center(55))
                print("="*55)
                print(f" Mitigação XDP (UDP)   : {pacotes_udp:>8} pps (descartados)")
                print(f" Banda Poupada         : {mbps:>8.2f} Mbps")
                print(f" Dispositivos Atacantes: {total_ips:>8} IPs falsos")
                print("-" * 55)
                print(f" Tráfego Legítimo (TCP): {pacotes_tcp:>8} pacotes acumulados")
                print("="*55)
                print("\n[ Pressione Ctrl+C para encerrar o monitoramento ]")
                
                estado_anterior = estado_atual
                
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\nMonitoramento encerrado pelo usuário.")
            break
        except Exception as erro:
            print(f"\nOcorreu um erro de leitura: {erro}")
            time.sleep(1)

def menu_principal():
    """Ponto de entrada do painel."""
    id_estatisticas = buscar_id_mapa(MAPA_ESTATISTICAS)
    id_ips = buscar_id_mapa(MAPA_IPS)
    
    if not id_estatisticas:
        print(f"Aviso: Não consegui localizar o mapa '{MAPA_ESTATISTICAS}'.")
        print("O filtro XDP está ativo no gateway? Tente rodar o load_xdp.sh novamente.")
        sys.exit(1)

    while True:
        print("\033c" + "="*50)
        print(" PAINEL DE CONTROLE DE DEFESA IoT ".center(50))
        print("="*50)
        print(" [1] Monitorar tráfego e mitigação em tempo real")
        print(" [2] Sair do sistema")
        print("="*50)
        
        opcao = input("\n Selecione uma opção: ").strip()
        
        if opcao == '1':
            monitorar_ataque(id_estatisticas, id_ips)
        elif opcao == '2':
            print("Saindo...")
            sys.exit(0)

if __name__ == "__main__":
    # Garante que scripts que precisem ser parados via Ctrl+C não mostrem erros complexos
    try:
        menu_principal()
    except KeyboardInterrupt:
        sys.exit(0)
