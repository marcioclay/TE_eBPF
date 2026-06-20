# Comandos de apoio

1. Para ver se o XDP anexou na placa de rede (eth1):
   
```
sudo docker exec clab-lab-ebpf-gateway ip link show eth1
```

2. Para ver se os Mapas foram criados na memória:
   
```
sudo docker exec clab-lab-ebpf-gateway ls -la /sys/fs/bpf/
```

3. Lista mapas ativos na memória, com os seus respetivos IDs e nomes:

```
sudo docker exec clab-lab-ebpf-gateway bpftool map show
```
