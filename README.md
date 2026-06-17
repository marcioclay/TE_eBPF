## 🐝 Protótipo de topologia com XDP/eBPF orquestrado por Containerlab

> Protótipo de **deteção de pacotes em um Gateway** usando **eBPF/XDP** em ambiente de rede virtualizado com **Containerlab**.

[![Containerlab](https://img.shields.io/badge/Containerlab-v0.50+-blue?logo=linux)](https://containerlab.dev)
[![Docker](https://img.shields.io/badge/Docker-required-blue?logo=docker)](https://www.docker.com)
[![eBPF](https://img.shields.io/badge/eBPF-XDP-orange)](https://ebpf.io)
[![Licença](https://img.shields.io/badge/licença-GPL--2.0-green)](LICENSE)
[![Linguagem](https://img.shields.io/badge/linguagem-C-blue)](https://en.wikipedia.org/wiki/C_(programming_language))
[![OS](https://img.shields.io/badge/OS-Ubuntu-orange)](https://ubuntu.com/)


---
## 📖 Visão Geral

"Este protótipo, inicialmente concebido como atividade prática da disciplina de Redes Programáveis do Mestrado em Computação Aplicada, evoluiu para uma proposta de pesquisa voltada à mitigação de ataques DDoS em dispositivos IoT. O sistema propõe uma Sonda de Monitoramento de Segurança de alto desempenho que utiliza eBPF e XDP para realizar a mitigação de ataques volumétricos (DDoS) com técnica de IP Spoofing. O objetivo é demonstrar que a filtragem em nível de driver, aliada ao processamento em line-rate, supera as limitações de escalabilidade dos firewalls tradicionais, consolidando-se como uma solução robusta para cenários de exaustão de recursos em Gateways IoT."

## O que este protótipo demonstra:

- Mitigação em Nível de Driver: Implementação de um filtro XDP em C capaz de descartar tráfego malicioso (XDP_DROP) no estágio mais precoce possível da pilha de rede, antes da alocação de memória no kernel.
- Eficiência Computacional: Processamento de tráfego em line-rate com uso mínimo de CPU, validando a superioridade da arquitetura eBPF em relação a firewalls tradicionais baseados em Netfilter (iptables).
- Análise Comparativa de Desempenho: Orquestração de cenários de teste para avaliar a resiliência do Gateway sob condições de rede instáveis (latência/perda simuladas via tc qdisc).
- Monitoramento Estatístico via eBPF Maps: Uso de mapas do tipo ARRAY para contagem determinística ($O(1)$) de pacotes e banda, garantindo escalabilidade e mínima latência de observabilidade.
- Seletividade de Filtro: Implementação de regras baseadas em protocolos e portas (UDP/1883) para garantir a proteção contra ataques sem comprometer o tráfego MQTT legítimo.


---

Hipótese: "A mitigação de ataques DDoS baseada em XDP (Stateless) é superior à mitigação baseada em Netfilter (Stateful) em cenários de IP Spoofing, uma vez que a abordagem stateless mantém o desempenho constante ($O(1)$) independentemente da cardinalidade de IPs falsificados, enquanto a abordagem stateful sofre degradação exponencial devido à exaustão da tabela de estados do kernel."

---

## Topologia


## 🌐 Topologia da Rede


```
┌────────────────────────────────────────────────────────┐
│                      MÁQUINA HOST                      │
│                                                        │
│  ┌────────────────────────┐    ┌────────────────────┐  │
│  │    clab-sensor    │    │    │    clab-atacante   │  │
│  │     (10.0.0.20/24)     │    │   (10.0.0.10/24)   │  │
│  └───────────┬────────────┘    └──────────┬─────────┘  │
│              │ eth1                       │ eth1       │
│              └──────────────┬─────────────┘            │
│                             ▼                          │
│                  ┌────────────────────┐                │
│                  │  clab-bridge       │                │
│                  │  (Switch Virtual)  │                │
│                  └──────────┬─────────┘                │
│                             │ eth1                     │
│                             ▼                          │
│                  ┌────────────────────┐                │
│                  │ clab- gateway      │                │
│                  │   (10.0.0.1/24)    │                │
│                  │ [Filtro eBPF/XDP]  │                │
│                  └────────────────────┘                │
└────────────────────────────────────────────────────────┘

```


| Nó     | Endereço IP  | Função                                      |
|--------|-------------|---------------------------------------------|
| atacante | `10.0.0.10`  | Emissor de pacotes - ilegítimo        |
| sensor | `10.0.0.20`  | Sensor — emissor pacotes legítimo      |
| gateway | `10.0.0.1`  | Filtro XDP - GATEWAY          |


---

## 🔧 Pré-requisitos


### 0. Requisitos do Sistema

Os seguintes requisitos devem ser atendidos para que a ferramenta containerlab seja executada com sucesso (https://containerlab.dev/install/):

- Um usuário com privilégios de sudo para executar o containerlab.

- Um servidor Linux, pode ser WSL2 (https://learn.microsoft.com/pt-br/windows/wsl/install).

### 1. Instalar o Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

> Saia e entre novamente na sessão após adicionar seu usuário ao grupo `docker`.

### 2. Instalar o Containerlab

```bash
bash -c "$(curl -sL https://get.containerlab.dev)"
```

Verifique a instalação:

```bash
containerlab version
```

---

### 3. Obtendo o Laboratório

Clone o repositório e acesse o diretório do laboratório:

```bash
git clone https://github.com/marcioclay/gateway-ebpf.git

```
Instalação de imagem ubuntu com ebpf
```
# A. Entre na pasta ebpf-host dentro do seu repositório local
cd gateway-ebpf/ebpf-host/

# B. Construa a imagem localmente
sudo docker build -t ebpf-host:latest .

---

### 4. Instalar na raiz - para iniciar o MQTT

```
cat <<EOF > mosquitto.conf
listener 1883 0.0.0.0
allow_anonymous true
EOF
```


### 5. Compilar o Programa eBPF

O script `compile.sh` usa um **container nicolaka/netshoot como ambiente de build**, dispensando a instalação de ferramentas de compilação no host.Isso evita que você precise instalar localmente todas as dependências de eBPF (que podem ser pesadas ou conflitar) diretamente no seu sistema host.

```bash
# Se não estiver no diretório do lab:
# cd ~/redes/gateway-ebpf
chmod +x compile.sh
./compile.sh
```

<details>
<summary>O que o compile.sh faz?</summary>

Ele sobe um container Docker temporário que:
1. Instala `clang`, `llvm`, `libbpf-dev` e `gcc-multilib`.
2. Compila `xdp_monitor.c` gerando bytecode para a **máquina virtual BPF** (`-target bpf`).
3. Gera o arquivo objeto `xdp_monitor.o` no diretório atual.
4. Remove o container de build automaticamente (`--rm`).

</details>

**Saída esperada:**
```
Success! xdp_monitor.o created. 😱😱😱
```

---

### 6. Deploy da Topologia

```bash
sudo containerlab deploy -t topologia.yml --reconfigure
```

Isso irá:
- Criar três containers Linux (`gateway` , `atacante` e `sensor`).
- Configurar os IPs nas interfaces `eth1` de cada nó.
- Montar o `xdp_monitor.o` dentro do `gateway` em `/xdp_monitor.o`.
- Criar um barramento virtual através de uma bridge conectando as interfaces eth1 dos nós atacante, sensor e gateway.

Verifique se o lab está rodando:

```bash
docker ps --filter "label=containerlab=gateway-ebpf"
```
```
docker ps --format "table {{.Names}}\t{{.Status}}" | grep clab
```

---


### 6. Verificar Conectividade Inicial

Antes de ativar o filtro XDP, confirme que os nós se comunicam normalmente:

```bash
docker exec clab-gateway-ebpf-sensor ping -c 3 10.0.0.1
```

**Resultado esperado:** `0% packet loss`  

---

### 7. Executar script 

- instala python
- instala MQTT

  ```
  chmod +x setup.sh
  ./setup.sh
  ```

### 8. Ativar o Filtro XDP

8.1 Carregar e pinar o programa XDP

#### Remover pin anterior (se existir) para evitar erros

```
sudo docker exec -it clab-lab-ebpf-gateway rm -f /sys/fs/bpf/xdp_monitor_test
```

#### Carregar e pinar o programa no filesystem BPF

```
sudo docker exec -it clab-lab-ebpf-gateway bpftool prog load /lab/xdp_monitor.o /sys/fs/bpf/xdp_monitor_test type xdp
```

#### Anexar à interface eth1

```
sudo docker exec -it clab-lab-ebpf-gateway ip link set dev eth1 xdpgeneric pinned /sys/fs/bpf/xdp_monitor_test
```

Por que pinar? Pinar o programa em /sys/fs/bpf/ mantém o BPF Map ativo na memória, permitindo ler o contador de drops mesmo após o comando de carregamento encerrar.

--- 

📊 Mapas - atalho

Como o programa foi pinado, o bpftool cria um "atalho" para os seus mapas dentro do diretório /sys/fs/bpf/. Para ver as estatísticas dos ataques em tempo real:

```
# Para ver a volumetria global (DDoS e total da porta 1883):
sudo docker exec -it clab-lab-ebpf-gateway bpftool map dump name proto_stats
```

```
# Para ver a análise comportamental por IP (Slow DoS):
sudo docker exec -it clab-lab-ebpf-gateway bpftool map dump name tcp_sessions
```



### 🧹 Limpeza

Para destruir o laboratório e remover todos os containers:

```
sudo containerlab destroy -t topologia.yml
```



### 📂 Estrutura do Projeto 

```
TE_eBPF/
├── topology.yaml       # Configuração do laboratório (Containerlab)
├── src/
│   └── xdp_monitor.c   # Código eBPF otimizado (DDoS + IP Spoofing)
├── scripts/
│   ├── compile.sh      # Compila o xdp_monitor.c
│   ├── setup.sh        # Configura rede (tc qdisc)
│   ├── load_xdp.sh     # Ativa o XDP no Gateway
│   └── start_broker.sh # Inicia o Mosquitto (MQTT)
├── dash/
│   └── dashboard.py    # Dashboard com PPS e IPs Únicos
└── metricas/
    └── xdp_dos.md      # Roteiro de testes (Passo a passo)

```

---

### 📚 Referências 

- [Documentação Oficial do eBPF](https://ebpf.io/what-is-ebpf/)
- [Documentação do Containerlab](https://containerlab.dev/quickstart/)
- [Tutorial XDP (kernel.org)](https://github.com/xdp-project/xdp-tutorial)
- [libbpf GitHub](https://github.com/libbpf/libbpf)
- [nicolaka/netshoot — Container de diagnóstico de rede](https://github.com/nicolaka/netshoot)
- [Tutorial de artigo ataque slow](https://github.com/gianluca2414/MQTT_SlowITe )




