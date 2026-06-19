
##  📊 Guia de Execução de Testes: (DoS Volumétrico)

![Tcpdump](https://img.shields.io/badge/Tcpdump-network%20analysis-orange?style=flat-square&logo=wireshark)
![Hping3](https://img.shields.io/badge/Hping3-packet%20crafting-red?style=flat-square&logo=linux)
![DDoS](https://img.shields.io/badge/DDoS%20%26%20Slow-attack%20simulation-darkred?style=flat-square&logo=apache)
![Cybersecurity](https://img.shields.io/badge/Cybersecurity-lab%20focus-blue?style=flat-square&logo=security)
![IoT](https://img.shields.io/badge/IoT-connected%20devices-lightblue?style=flat-square&logo=internetofthings)


Este guia orienta a validação do protótipo através do estabelecimento de tráfego legítimo, simulação de ataque de inundação e extração de metricas diretamente do plano de dados.

Comparativo 

- Cenário A (Baseline - Simulação de ataque sem proteção) 

- Cenário B (Simulação de ataque com iptables).

- Cenário C (Simulação de ataque com XDP).

## Preparação do ambiente

1. Em todos os cenário inicie o dashboard
   O dashboard colherá dados dos mapas xdp e iptables
```
# medir a mitigação, RTT e pacotes perdidos
sudo python3 dashboard.py
```
2. Enquanto o dashboard estiver em execução será realizado ping automático sensor > gateway (não é necessário nenhuma ação)

3. Em todos os cenários executar o htop - fará leitura de dados do hardware, cpu, memoria e outros.
```
htop
```
   
--- 
## Cenário A (Baseline - Sem Proteção)

1. Desativar o xdp para não detectar ou mitigar:

```
# Dentro da pasta do projeto TE_eBPF
# 1. Certifique-se que não há XDP rodando
./scripts/load_xdp.sh
```

2. Monitorar a carga de CPU  

```
# inicie um terminal A
htop
```

3. Dashboard de observação
```
# medir a mitigação, RTT e pacotes perdidos
sudo python3 dashboard.py
```

4. Lançar ataque - DDoS com spoofing

```
# Executar ataque no contêiner 'atacante'
sudo docker exec -it clab-lab-ebpf-atacante hping3 --flood --rand-source --udp -d 120 -p 1883 10.0.0.1
```

---

## Mitigação com Iptables 

1. Ativar regras iptables

Script de carga com o parâmetro iptables. Isso fará com que o Gateway aplique uma regra de descarte (DROP) na camada de rede.:

```
# Ativa a regra de bloqueio via iptables
./scripts/load_xdp.sh iptables
```

2. Monitorar a carga de CPU  

```
# inicie um terminal A
htop
```

3. Dashboard de observação
```
# medir a mitigação, RTT e pacotes perdidos
sudo python3 dashboard.py
```

4. Lançar ataque - DDoS com spoofing

```
# Executar ataque no contêiner 'atacante'
sudo docker exec -it clab-lab-ebpf-atacante hping3 --flood --rand-source --udp -d 120 -p 1883 10.0.0.1
```

--- 

## Mitigação via XDP (eBPF)

1. Mitigação XDP
   
```
./scripts/load_xdp.sh xdp
```

2. Monitorar a carga de CPU  

```
# inicie um terminal A
htop
```

3. Dashboard de observação
```
# medir a mitigação, RTT e pacotes perdidos
sudo python3 dashboard.py
```

4. Lançar ataque - DDoS com spoofing

```
# Executar ataque no contêiner 'atacante'
sudo docker exec -it clab-lab-ebpf-atacante hping3 --flood --rand-source --udp -d 120 -p 1883 10.0.0.1
```

---

### Analise dos testes estão no diretório resultados.md

