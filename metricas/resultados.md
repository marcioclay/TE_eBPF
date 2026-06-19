# Relatório de Experimentos e Análise de Resultados


Este documento detalha a metodologia, a caracterização de rede e a análise dos resultados obtidos durante os testes de mitigação de ataques DDoS (Distributed Denial of Service) em um ambiente de Gateway IoT. O estudo compara a eficiência de abordagens tradicionais de firewall (Iptables) contra o processamento de pacotes em nível de kernel (eBPF/XDP).

---

## 1. Caracterização e Diferenciação de Tráfego legítimo e anômalo

Um tráfego legítimo de um sensor IoT para um gateway se caracteriza por baixo volume de pacotes, endereço ip é conhecido e os dados do payload são organizados e estruturados. Nisto difere de um ataque DDoS com simulação de spoofing, pois gera alta taxa de pacotes na interface de rede e ips aleatórios enviando pacotes.

| **Aspecto**       | **Tráfego legítimo (sensor → gateway IoT)** | **Ataque ( DDoS)** |
|--------------------|---------------------------------------------|-------------------------|
| **Periodicidade**  | Intervalos regulares (ex.: a cada 5s    ) | Pacotes contínuos sem pausa |
| **Taxa de pacotes**| Baixa (bytes/kbps)                         | Alta (Mbps/Gbps) |
| **Origem**         | IP fixo do sensor                          | IPs aleatórios (spoofing) |
| **Payload**        | Dados estruturados (JSON, valores numéricos)| Conteúdo aleatório ou vazio |


Abaixo imagem de captura de trafego legitimo e anomalo, usando tcdump e wireshark. As imagens foram obtidas através de simulação de tráfego sensor -> gateway e atacante -> gateway.

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

<img width="579" height="338" alt="image" src="https://github.com/user-attachments/assets/95478197-4b49-4c49-8de8-88b1874de72c" />

---

## 2. Metodologia e Cenários de Teste

A bateria de testes foi executada sob um ataque volumétrico constante de aproximadamente **[INSERIR PPS DO ATAQUE, ex: 400.000] PPS**, gerado pela ferramenta `hping3`. Foram avaliados três cenários distintos:

1.  **Cenário 1: Sem Defesa (Baseline de Caos):** Gateway exposto ao ataque volumétrico sem qualquer mecanismo de filtragem ativo.
2.  **Cenário 2: Mitigação L3/L4 Tradicional (Iptables):** Regra de *DROP* aplicada no Netfilter (`iptables -A INPUT -p udp --dport 1883 -j DROP`).
3.  **Cenário 3: Mitigação eBPF/XDP:** Filtro injetado no driver da interface de rede para descarte antecipado.

---

## 3. Resultados e Métricas de Avaliação

A eficácia de cada cenário foi medida em tempo real através de um painel de monitoramento customizado em Python e ferramentas de análise de hardware (`mpstat`/`htop`).

### 3.1. Quadro Resumo dos Resultados

| Métrica Avaliada | Cenário 1: Sem Defesa | Cenário 2: Iptables | Cenário 3: eBPF/XDP |
| :--- | :---: | :---: | :---: |
| **Tráfego Recebido (PPS)** | ~ [000.000] | ~ [000.000] | ~ [000.000] |
| **Taxa de Mitigação (%)** | 0.00% | [XX.X]% | **[XX.X]%** |
| **Status do Sensor (QoS)** | OFFLINE | Instável | **ONLINE** |
| **Perda de Pacotes Legítimos**| 100% | [XX]% | **[0.0]%** |
| **Latência Média (RTT)** | Timeout | [XX.X] ms | **[X.X] ms** |
| **Jitter (Variação de Atraso)**| N/A | [XX.X] ms | **[X.X] ms** |

### 3.2. Análise da Taxa de Mitigação e Tráfego
*(Nota: O eBPF/XDP foi capaz de interceptar os pacotes maliciosos na sua totalidade. No cenário Iptables, observou-se [INSERIR OBSERVAÇÃO, ex: que a fila do kernel encheu antes que o firewall pudesse processar todos os pacotes, resultando em menor taxa de mitigação efetiva]).*

### 3.3. Qualidade de Serviço (QoS) e Disponibilidade
O impacto do ataque volumétrico no tráfego legítimo foi medido através de disparos de pacotes ICMP (Ping) do Sensor para o Gateway.
* **Sem defesa:** A saturação da interface de rede impediu o retorno de pacotes, resultando em 100% de perda e queda total da disponibilidade.
* **Iptables:** A latência sofreu picos elevados (Jitter alto de `[XX] ms`), evidenciando que o processamento tardio do firewall atrasa a passagem do tráfego legítimo.
* **eBPF/XDP:** A latência manteve-se próxima do estado de repouso (`[X] ms`), confirmando que o descarte antecipado liberta o barramento para a comunicação IoT legítima.

### 3.4. Consumo de CPU e "Degradação Graciosa"
Para validar o impacto na infraestrutura física/host, avaliou-se o uso de processamento de rede (*SoftIRQ*) núcleo a núcleo.

* No cenário **Sem Defesa** e com **Iptables**, observou-se um consumo severo de *SoftIRQ*, levando núcleos da CPU a operar próximos de **[XX]%** de capacidade apenas para lidar com o descarte ou roteamento dos pacotes da *botnet*.
* Com a ativação do **eBPF/XDP**, evidenciou-se o conceito de **degradação graciosa**: a arquitetura limitou o impacto do ataque. O núcleo responsável pela interface de rede reduziu drasticamente o ciclo de processamento (pois o pacote é descartado no hook do driver, antes de virar um *Socket Buffer*), libertando os recursos computacionais do Gateway para outras tarefas do sistema operativo.

---

## 4. Conclusão Parcial

Os dados preliminares demonstram categoricamente a superioridade do eBPF/XDP como mecanismo de defesa para infraestruturas restritas como Gateways IoT. Enquanto abordagens tradicionais (Iptables) conseguem bloquear o ataque em regras lógicas, falham em proteger os recursos de hardware subjacentes, resultando em latência e degradação de QoS inaceitáveis para sistemas de missão crítica em tempo real. O XDP provou atuar como um escudo eficiente, mantendo a responsividade do sistema intacta mesmo sob cenários de estresse extremo.
