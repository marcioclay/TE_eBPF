# Relatório de Experimentos e Análise de Resultados


Este documento detalha a metodologia, a caracterização de rede e a análise dos resultados obtidos durante os testes de mitigação de ataques DDoS (Distributed Denial of Service) em um ambiente de Gateway IoT. O estudo compara a eficiência de abordagens tradicionais de firewall (Iptables) contra o processamento de pacotes em nível de kernel (eBPF/XDP).


### Tecnologias usadas para os testes 

- xdp_monitor.c : Código eBPF/XDP que atua no driver da rede. Inspeciona e descarta pacotes maliciosos antes de consumirem memória, registando as estatísticas de bloqueio no Kernel.

- dashboard.py: Script Python que lê os dados do Kernel em tempo real e emite pings contínuos para calcular a Qualidade de Serviço (QoS) da rede IoT (Latência e Jitter).

- hping3 : Ferramenta geradora de tráfego, utilizada para simular o ataque de exaustão (DDoS UDP Flood) com IPs falsificados (IP Spoofing).

- htop : Monitor de sistema executado no Host. Serve como prova material do esgotamento da CPU (SoftIRQ) sem defesa e da poupança de processamento quando o XDP está ativo.
---
🗂 Mapas xdp

Mapa estatísticas

- Tipo: BPF_MAP_TYPE_ARRAY (array fixo, acesso imediato).

- Capacidade: 2 posições.

- Índice 0: carga bloqueada.

- Valor: estrutura metricas_host (total de pacotes + total de bytes).

- Papel: fornece os dados brutos para calcular PPS e taxa de mitigação no dashboard.

Mapa ips_detectados

- Tipo: BPF_MAP_TYPE_HASH (hash table para IPs não sequenciais).

- Capacidade: até 8192 IPs únicos.

- Chave: endereço IP de origem malicioso (__u32).

- Valor: contador (__u64).

- Papel: rastrear e bloquear milhares de IPs falsificados (spoofing), mostrando eficiência superior ao iptables em consumo de memória.
  
---

## 1. Caracterização e Diferenciação de Tráfego legítimo e anômalo

Um tráfego legítimo de um sensor IoT para um gateway se caracteriza por baixo volume de pacotes, endereço ip é conhecido e os dados do payload são organizados e estruturados. Nisto difere de um ataque DDoS com simulação de spoofing, pois gera alta taxa de pacotes na interface de rede e ips aleatórios enviando pacotes.

| **Aspecto**       | **Tráfego legítimo (sensor → gateway IoT)** | **Ataque ( DDoS)** |
|--------------------|---------------------------------------------|-------------------------|
| **Periodicidade**  | Intervalos regulares (ex.: a cada 5s    ) | Pacotes contínuos sem pausa |
| **Taxa de pacotes**| Baixa (bytes/kbps)                         | Alta (Mbps/Gbps) |
| **Origem**         | IP fixo do sensor                          | IPs aleatórios (spoofing) |
| **Payload**        | Dados estruturados (JSON, valores numéricos)| Conteúdo aleatório ou vazio |

Os comandos abaixo foram usados para gerar tráfego legítimo e anômalo entre sensor e gateway.

```
# comados para simular trafego legitimo e anomalo
sudo docker exec clab-lab-ebpf-sensor hping3 -S -c 10 -i 1 -p 1883 10.0.0.1
sudo docker exec -it clab-lab-ebpf-atacante hping3 --flood --rand-source --udp -d 120 -p 1883 10.0.0.1
```
```
# comandos tcdump gerando arquivo .pcap
sudo docker exec clab-lab-ebpf-gateway tcpdump -i eth1 port 1883 -n -c 200 -w - > comparativo.pcap
```

Observação: 

* Coluna source: tráfego legítimo - ip único / tráfego anômalo - múltiplos ips
* Coluna protocol: tráfego legítimo - tcp / tráfego anômalo - udp porta 1883
* Coluna Time: tráfego legítimo - cadência ritimada / tráfego anômalo - dezenas, centenas pacotes com a mesma marca
* Coluna lenght: tráfego legítimo - tamanho fixo / tráfego anômalo - udp porta 1883


#### Tráfego anômalo e legítimo
A primeira parte simula tráfego legítmo a segunda com borda vermelha tráfego anômalo.

Abaixo imagem de captura de trafego legitimo e anomalo, usando tcdump e wireshark. As imagens foram obtidas através de simulação de tráfego sensor -> gateway e atacante -> gateway.

<p align="center">
  <img src="https://github.com/user-attachments/assets/95478197-4b49-4c49-8de8-88b1874de72c" width="450" height="300" />
  <br>
  <em>Figura 1: Tráfego legítimo x anômalo</em>
</p>


---

## 2. Metodologia e Cenários de Teste

A bateria de testes foi executada sob um ataque volumétrico constante de aproximadamente **464000 PPS**, gerado pela ferramenta `hping3`. Foram avaliados três cenários distintos:

1.  **Cenário 1: Sem Defesa (Baseline de Caos):** Gateway exposto ao ataque volumétrico sem qualquer mecanismo de filtragem ativo.
2.  **Cenário 2: Mitigação L3/L4 Tradicional (Iptables):** Regra de *DROP* aplicada no Netfilter (`iptables -A INPUT -p udp --dport 1883 -j DROP`).
3.  **Cenário 3: Mitigação eBPF/XDP:** Filtro injetado no driver da interface de rede para descarte antecipado.

---

## 3. Resultados e Métricas de Avaliação

A eficácia de cada cenário foi medida em tempo real através de um painel de monitoramento customizado em Python e ferramenta de análise de hardware `htop`.

### 3.1. Análise de Tráfego e Consumo de Hardware (Plano de Dados)
Nesta etapa, avaliou-se o volume do ataque injetado na interface do Gateway e o impacto computacional correspondente. O consumo de hardware foi medido através da extração do pico de utilização do núcleo afetado (Core 1) pelas interrupções de rede (SoftIRQ).

 Quadro Resumo dos Resultados

 | Métrica Avaliada | Cenário 1: Sem Defesa | Cenário 2: Iptables | Cenário 3: eBPF/XDP |
| :--- | :---: | :---: | :---: |
| **Tráfego Recebido (PPS)** | ~ 306.679 | ~ 397.727 | ~ 730.258 |
| **Pacotes Bloqueados (PPS)**| 0 | ~ 345.479 | ~ 859.922 * |
| **Taxa de Mitigação** | 0.00% | 86.86% | 100.00% |
| **Uso da CPU (Núcleo Afetado)**| 100.0% | 95.2% | 43.1% |

 |


Tráfego e Hardware: Os testes mostraram que tanto xdp, quanto o iptables conseguem mitigar ataques DDoS, porém percebeu-se que a carga do hardware como cpu foi menor do que o iptables, que em alguns momentos chegou a 95%. O xdp teve uma taxa de drop de pacotes de forma superior o que facilitou a manutenção do sistema. Ambas as tecnologias são eficientes, mas o drop a nível de kernel do xdp possibilita menor exaustão da cpu.


### 3.2. Análise de Qualidade de Serviço (QoS) e Disponibilidade
Esta etapa mede o impacto da mitigação do ponto de vista do dispositivo IoT (Sensor Legítimo), focando na viabilidade de manter comunicações de missão crítica (tempo real) ativas durante o ataque.

| Métrica de QoS | Cenário 1: Sem Defesa | Cenário 2: Iptables | Cenário 3: eBPF/XDP |
| :--- | :---: | :---: | :---: |
| **Disponibilidade (Status)** | ONLINE | ONLINE | ONLINE |
| **Perda de Pacotes Legítimos**| 0.9% | 2.2% | 0.0% |
| **Latência Média (RTT)** | 899.00 ms | 67.80 ms | 26.20 ms |
| **Jitter (Variação de Atraso)**| 764.00 ms | 40.10 ms | 5.90 ms |

**Status do Sensor (QoS)** - o status OFFLINE, é intermitente, necessitando observação temporal para sua visualização.

Achados de Qualidade de Serviço:
O impacto na QoS define de forma categórica a viabilidade técnica da defesa para ambientes IoT. Embora o Iptables evite a queda total do sensor (0% de perda), ele introduz um gargalo, sacrificando o tempo real ao gerar um Jitter severo de 831.60 ms. A abordagem com eBPF/XDP demonstra ser uma arquitetura capaz de restaurar a normalidade da rede, mantendo a latência em estado de repouso (31.50 ms) e um Jitter estável, garantindo o serviço legítimo.

--- 

As figuras apresentam os resultados dos testes do protótipo de mitigação DDoS. As duas primeiras mostram a análise de tráfego e a qualidade de serviço com XDP/eBPF, evidenciando a eficiência da filtragem no kernel. As duas últimas ilustram o mesmo cenário com iptables, destacando a diferença de desempenho e impacto sobre o tráfego legítimo.


| ![Imagem 1](https://github.com/user-attachments/assets/74cb21d8-f754-437f-868f-df7ec245b27d) | ![Imagem 2](https://github.com/user-attachments/assets/43330cb6-9592-47c0-97c8-645eaa2f1e49) |
|:--:|:--:|
| Figura 2: Análise tráfego xdp | Figura 3: QoS xdp |

| ![Imagem 3](https://github.com/user-attachments/assets/d6534712-4226-472c-8e32-1bb86e0cbd0b) | ![Imagem 4](https://github.com/user-attachments/assets/de87b5c3-5cd2-45a8-9dd6-b509067eafd9) |
|:--:|:--:|
| Figura 4:  Análise tráfego iptables | Figura 5: QoS iptables |



## 4. Conclusão Parcial

Os teste foram realizados para simular uma ataque DDoS com simulação de spoofing. Os testes demonstram uma ganho do eBPF/xdp ao iptables, a diferença se mostra no uso da cpu que foi quase a 100% no iptables. Cada teste foi realizado no periodo de 30s, e sugere-se continuar a avaliação, aumentando o numero de sensores atacantes e inserindo o broker MQTT em um container separado.
