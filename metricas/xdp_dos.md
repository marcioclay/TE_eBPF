
##  📊 Guia de Execução de Testes: (DoS Volumétrico)

![Tcpdump](https://img.shields.io/badge/Tcpdump-network%20analysis-orange?style=flat-square&logo=wireshark)
![Hping3](https://img.shields.io/badge/Hping3-packet%20crafting-red?style=flat-square&logo=linux)
![DDoS](https://img.shields.io/badge/DDoS%20%26%20Slow-attack%20simulation-darkred?style=flat-square&logo=apache)
![Cybersecurity](https://img.shields.io/badge/Cybersecurity-lab%20focus-blue?style=flat-square&logo=security)
![IoT](https://img.shields.io/badge/IoT-connected%20devices-lightblue?style=flat-square&logo=internetofthings)


Este guia orienta a validação do protótipo através do estabelecimento de tráfego legítimo, simulação de ataque de inundação e extração de metricas diretamente do plano de dados.

Benchmark Comparativo

- Cenário A (Baseline - Sem Proteção) ataque com ./load_xdp.sh sem argumentos. Anote o uso de CPU (top ou htop no gateway).

- Cenário B (Netfilter): Rode ./load_xdp.sh iptables. Lance o ataque, verifique o PPS no Dashboard e a CPU%.

- Cenário C (Proposta - XDP): Rode ./load_xdp.sh xdp. Lance o ataque, verifique o PPS no Dashboard e a CPU%.


--- 
## Cenário A (Baseline - Sem Proteção)

0. Desativar o xdp para não detectar ou mitigar:

```
# Dentro da pasta do projeto TE_eBPF
# 1. Certifique-se que não há XDP rodando
./scripts/load_xdp.sh
```

1. Monitorar a carga de CPU no Gateway

```
sudo docker exec -it clab-lab-ebpf-gateway top
```

2. Lançar ataque - DDoS com spoofing

```
# Executar ataque no contêiner 'atacante'
sudo docker exec -it clab-lab-ebpf-atacante hping3 --flood --rand-source --udp -d 120 -p 1883 10.0.0.1
```

3. Observação

   - CPU Load (%Cpu(s))
   - Processos: O processo ksoftirqd
   - Estabilidade: Note se o terminal do Gateway fica lento ou se o ping a partir de outros nós começa a falhar (latência alta).
  ver: si e top
Exemplo de nota: "Sem mitigação, o Gateway atingiu 98% de carga de SoftIRQ, impossibilitando a entrega de mensagens legítimas do sensor."
--- 

## Mitigação com Iptables 

1. Ativar regras iptables

Script de carga com o parâmetro iptables. Isso fará com que o Gateway aplique uma regra de descarte (DROP) na camada de rede.:

```
# Ativa a regra de bloqueio via iptables
./scripts/load_xdp.sh iptables
```

2. Monitorar a CPU

```
sudo docker exec -it clab-lab-ebpf-gateway top
```

3. Ataque(mesmo metodo) atacante > gateway

```
sudo docker exec -it clab-lab-ebpf-atacante hping3 --flood --rand-source --udp -d 120 -p 1883 10.0.0.1
```
4. Observação

   CPU Load: Você notará que o valor de si (SoftIRQ) provavelmente ainda estará elevado, mas talvez um pouco menor que no Cenário A. A grande diferença é que o iptables introduz uma latência de processamento maior para cada pacote que ele avalia nas suas tabelas de regras.

Dashboard: No seu dashboard.py (caso esteja rodando), compare os valores.

Comportamento do Kernel: O iptables opera na camada stateful (ou stateless dependendo da regra), mas ele precisa "trazer" o pacote para dentro da pilha TCP/IP do kernel, o que consome mais ciclos de processamento do que a solução XDP que testaremos a seguir.

Anotação para sua dissertação:

Exemplo de nota: "Com a mitigação via iptables, o Gateway apresentou uma redução marginal na carga de CPU, mantendo-se, contudo, próximo ao ponto de saturação devido ao overhead de processamento de pacotes na pilha de rede do Kernel."

--- 

## Mitigação via XDP (eBPF)

1. Mitigação XDP
   
```
./scripts/load_xdp.sh xdp
```

2. Monitorar CPU

```
sudo docker exec -it clab-lab-ebpf-gateway top
```

3. Ataque com uso do xdp

```
sudo docker exec -it clab-lab-ebpf-atacante hping3 --flood --rand-source --udp -d 120 -p 1883 10.0.0.1
```

O que observar no Cenário C (Resultados Esperados):
CPU Load: Você verá que o valor de si (SoftIRQ) será significativamente menor do que nos cenários A e B. Em muitos casos, o sistema mal "sente" o ataque, pois o XDP descarta os pacotes antes mesmo de eles ocuparem recursos do kernel.

Dashboard: No seu dashboard.py, observe o campo "IPs Distintos" subir rapidamente. Isso prova que o seu sistema está a filtrar um ataque distribuído (spoofed) em tempo real com precisão.

Performance Legítima: Enquanto o ataque ocorre, tente rodar um comando simples de rede (como um ping do sensor para o gateway). Ele deve continuar a responder quase normalmente, provando que o seu filtro é "cirúrgico" e não impacta o tráfego legítimo.

---

Tire os prints (ou anote os valores de si do top e o PPS do Dashboard) para cada um dos 3 cenários.

Insira esses valores na sua tabela de resultados do xdp_dos.md.

