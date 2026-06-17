#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <bpf/bpf_endian.h>

// contadores de tráfego
struct metricas_host {
    __u64 total_pacotes;
    __u64 total_bytes;
};

// Mapa 1: Estatísticas globais por protocolo
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 2); 
    __type(key, __u32);
    __type(value, struct metricas_host);
} estatisticas_protocolo SEC(".maps");

// Mapa 2: Rastreamento de IPs únicos 
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 8192); 
    __type(key, __u32);        
    __type(value, __u64);      
} ips_detectados SEC(".maps");

SEC("xdp")
int programa_monitor_xdp(struct xdp_md *ctx) {
    void *data_end = (void *)(long)ctx->data_end;
    void *data = (void *)(long)ctx->data;

    //confirmação da camada ethernet
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end) return XDP_PASS;
    if (eth->h_proto != bpf_htons(ETH_P_IP)) return XDP_PASS;

    // confirmação camada de rede
    struct iphdr *iph = data + sizeof(struct ethhdr);
    if ((void *)(iph + 1) > data_end) return XDP_PASS;

    __u32 ip_origem = iph->saddr;
    __u64 tamanho_pacote = data_end - data;
    __u32 chave_estatistica;

    //  verifique o cabeçalho do IP
    if (iph->protocol == 17) { 
        
        // pacotes bloqueados
        chave_estatistica = 0;
        struct metricas_host *metricas = bpf_map_lookup_elem(&estatisticas_protocolo, &chave_estatistica);
        if (metricas) {
            __sync_fetch_and_add(&metricas->total_pacotes, 1);
            __sync_fetch_and_add(&metricas->total_bytes, tamanho_pacote);
        }

        // atualiza IP de origem 
        __u64 valor_dummy = 1;
        bpf_map_update_elem(&ips_detectados, &ip_origem, &valor_dummy, BPF_NOEXIST);

        
        return XDP_DROP;
    }

    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";
