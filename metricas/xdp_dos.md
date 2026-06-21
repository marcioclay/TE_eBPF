
##  Passos para simulação de ataque e mitigação 

![Tcpdump](https://img.shields.io/badge/Tcpdump-network%20analysis-orange?style=flat-square&logo=wireshark)
![Hping3](https://img.shields.io/badge/Hping3-packet%20crafting-red?style=flat-square&logo=linux)
![DDoS](https://img.shields.io/badge/DDoS%20-attack%20simulation-darkred?style=flat-square&logo=apache)
![Cybersecurity](https://img.shields.io/badge/Cybersecurity-lab%20focus-blue?style=flat-square&logo=security)
![IoT](https://img.shields.io/badge/IoT-connected%20devices-lightblue?style=flat-square&logo=internetofthings)


# Guia de Validação e Execução de Testes

Este guia orienta o passo a passo para a validação do protótipo. O experimento consiste em estabelecer um tráfego legítimo (baseline de QoS), simular um ataque volumétrico de inundação (DDoS UDP Flood com IP Spoofing) e extrair métricas de mitigação e consumo de hardware em três cenários distintos.

### Métricas avaliadas 

As métricas em análise no laboratório dividem-se em duas categorias principais, focando tanto no desempenho do plano de dados do gateway quanto no impacto direto na comunicação do sensor IoT:

1. Métricas de Tráfego e Consumo de Hardware (Plano de Dados)

- Tráfego Recebido (PPS - Pacotes por Segundo)
- Pacotes Bloqueados (PPS)
- Taxa de Mitigação (%)
- Uso da CPU (Núcleo Afetado): 

2. Métricas de Qualidade de Serviço (QoS) e Disponibilidade

- Disponibilidade (Status)
- Perda de Pacotes Legítimos (%)
- Latência Média (RTT - Round-Trip Time)
- Jitter (Variação de Atraso)


---
## 🧮 Cenários de Avaliação
* **Cenário A (Baseline):** Simulação de ataque sem qualquer proteção ativa.
* **Cenário B (Iptables):** Simulação de ataque com mitigação tradicional via regras de firewall (Netfilter).
* **Cenário C (eBPF/XDP):** Simulação de ataque com mitigação em hardware/kernel via eBPF.

---

## 🖥️ Preparação do Ambiente 

Para uma observação adequada, é necessário abrir **três terminais** no servidor Host. O monitoramento (Dashboard e Htop) deve permanecer em execução durante toda a transição dos cenários.

Será utilizado o hping3 com parametros para simular ataque  - dispara a partir do contêiner atacante um ataque DDoS massivo de inundação UDP com ips de origem falsificados contra a porta MQTT do alvo para saturar a rede.

### Terminal 1: Monitoramento de QoS e Rede (Dashboard)
Neste terminal o dashboard executa um ping em background (Sensor -> Gateway) para medir a latência (RTT) e a perda de pacotes, além de extrair os pacotes bloqueados diretamente dos mapas eBPF e Iptables.

```
# Na raiz do projeto TE_eBPF
sudo python3 dashboard.py
```

### Terminal 2: Monitoramento de Hardware (Host)

Monitora o impacto dos ataques no hardware (SoftIRQ - CPU). 

```
htop
```

### Observe as barras de CPU, devido o ataque haverá alteração(barras vermelhas/verde-escuras).

### Terminal 3: Controle de Defesas e Ataque

Este terminal será utilizado para alternar os mecanismos de defesa e disparar a ferramenta de stress (hping3).

😧 Cenário A: Sem Defesa 

Objetivo: Sem mecanismo de defesa o gateway e sensor legítimo ficam comprometidos em suas funções.

1. Filtro xdp e iptables desativados.
   ```
   ./scripts/load_xdp.sh off
   ```
2. Iniciar ataque: atacante > gateway.
   ```
   sudo docker exec -it clab-lab-ebpf-atacante hping3 --flood --rand-source --udp -d 120 -p 1883 10.0.0.1
   ```
Observação: Terminal 1 (QoS offline/timeout) e Terminal 2 (CPU do Host saturada).

--- 
👽 Cenário B: Mitigação Tradicional (Iptables)
Objetivo: Avaliar o custo computacional do firewall tradicional sob ataque volumétrico.

1. Será aplicada regra no firewall de descarte (DROP) na camada de rede a porta MQTT.
   ```
   ./scripts/load_xdp.sh iptables
   ```

2. Lançar o ataque:
   ```
   sudo docker exec -it clab-lab-ebpf-atacante hping3 --flood --rand-source --udp -d 120 -p 1883 10.0.0.1
   ```

3. Observação: Terminal 1 - pacotes bloqueados - latência (RTT) e o Jitter oscilam. O Terminal 2 - alto uso de CPU. Pare o ataque.
--- 

👏 Cenário C: Mitigação com eBPF/XDP
Objetivo: Provar a eficiência do descarte antecipado (hook do driver) na preservação da QoS e redução do impacto em hardware.

1. Ativar filtro eBPF: Anexa o programa XDP à interface de rede.
   
   ```
   ./scripts/load_xdp.sh xdp
   ```

2. Lançar o ataque:
   
   ```
   sudo docker exec -it clab-lab-ebpf-atacante hping3 --flood --rand-source --udp -d 120 -p 1883 10.0.0.1
   ```
3. Observação: Terminal 1 -Taxa de Mitigação deverá permance alta e o sensor online com latência estável. Terminal 2 - a cpu deverá ficar perto do estado de repouso.

   

