
##  📊 Guia de Execução de Testes: (DoS Volumétrico)

![Tcpdump](https://img.shields.io/badge/Tcpdump-network%20analysis-orange?style=flat-square&logo=wireshark)
![Hping3](https://img.shields.io/badge/Hping3-packet%20crafting-red?style=flat-square&logo=linux)
![DDoS](https://img.shields.io/badge/DDoS%20%26%20Slow-attack%20simulation-darkred?style=flat-square&logo=apache)
![Cybersecurity](https://img.shields.io/badge/Cybersecurity-lab%20focus-blue?style=flat-square&logo=security)
![IoT](https://img.shields.io/badge/IoT-connected%20devices-lightblue?style=flat-square&logo=internetofthings)


# 🧪 Guia de Validação e Execução de Testes

Este guia orienta o passo a passo para a validação do protótipo. O experimento consiste em estabelecer um tráfego legítimo (baseline de QoS), simular um ataque volumétrico de inundação (DDoS UDP Flood com IP Spoofing) e extrair métricas de mitigação e consumo de hardware em três cenários distintos.

## 📋 Cenários de Avaliação
* **Cenário A (Baseline):** Simulação de ataque sem qualquer proteção ativa.
* **Cenário B (Iptables):** Simulação de ataque com mitigação tradicional via regras de firewall (Netfilter).
* **Cenário C (eBPF/XDP):** Simulação de ataque com mitigação em hardware/kernel via eBPF.

---

## 🖥️ Preparação do Ambiente (Setup de Monitoramento)

Para uma observação adequada, é necessário abrir **três terminais** no servidor Host. O monitoramento (Dashboard e Htop) deve permanecer em execução durante toda a transição dos cenários.

### Terminal 1: Monitoramento de QoS e Rede (Dashboard)
Este painel executa um ping automático em segundo plano (Sensor -> Gateway) para medir a latência (RTT) e a perda de pacotes, além de extrair os pacotes bloqueados diretamente dos mapas eBPF e Iptables.
```
# Na raiz do projeto TE_eBPF
sudo python3 dashboard.py
```

### Terminal 2: Monitoramento de Hardware (Host)

Responsável por exibir o impacto do processamento de rede (SoftIRQ) nos núcleos da CPU. 

```
htop
```

# Dica: Observe as barras de CPU. O processamento de rede maliciosa elevará o uso de núcleos específicos (barras vermelhas/verde-escuras).

### Terminal 3: Controle de Defesas e Ataque

Este terminal será utilizado para alternar os mecanismos de defesa e disparar a ferramenta de stress (hping3).

🚀 Execução dos Cenários

A partir do Terminal 3, siga o fluxo abaixo para registrar os resultados de cada arquitetura de mitigação.

🔴 Cenário A: Sem Defesa (Baseline do Caos)

Objetivo: Provar a vulnerabilidade do Gateway e a saturação da rede.

1. Desativar proteções: Certifique-se de que não há filtros XDP ou regras de iptables ativas.
   ```
   ./scripts/load_xdp.sh off
   ```
2. Lançar o ataque: Execute o tráfego forjado a partir do contêiner atacante.
   ```
   sudo docker exec -it clab-lab-ebpf-atacante hping3 --flood --rand-source --udp -d 120 -p 1883 10.0.0.1
   ```
Observação: Olhe para o Terminal 1 (QoS offline/timeout) e Terminal 2 (CPU do Host saturada). Pare o ataque (Ctrl+C) após coletar os dados.

--- 
🟡 Cenário B: Mitigação Tradicional (Iptables)
Objetivo: Avaliar o custo computacional do firewall tradicional sob ataque volumétrico.

1. Ativar regras de firewall: Aplica uma regra de descarte (DROP) na camada de rede para a porta MQTT.
   ```
   ./scripts/load_xdp.sh iptables
   ```

2. Lançar o ataque:
   ```
   sudo docker exec -it clab-lab-ebpf-atacante hping3 --flood --rand-source --udp -d 120 -p 1883 10.0.0.1
   ```

3. Observação: O Terminal 1 mostrará os pacotes bloqueados, mas a latência (RTT) e o Jitter sofrerão oscilações severas devido à lentidão do Netfilter. O Terminal 2 continuará a mostrar alto uso de CPU. Pare o ataque.
--- 

🟢 Cenário C: Mitigação Alta Performance (eBPF/XDP)
Objetivo: Provar a eficiência do descarte antecipado (hook do driver) na preservação da QoS e redução do impacto em hardware.

1. Ativar filtro eBPF: Anexa o programa XDP à interface de rede.
   
   ```
   ./scripts/load_xdp.sh xdp
   ```

2. Lançar o ataque:
   
   ```
   sudo docker exec -it clab-lab-ebpf-atacante hping3 --flood --rand-source --udp -d 120 -p 1883 10.0.0.1
   ```
3. Observação: No Terminal 1, a Taxa de Mitigação subirá para ~100% e o Sensor permanecerá ONLINE com latência estável. No Terminal 2, a CPU retornará ao estado de repouso (degradação graciosa), comprovando a eficácia do eBPF.

   

