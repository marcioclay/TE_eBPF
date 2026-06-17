#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <bpf/bpf_endian.h>

struct host_metrics {
    __u64 packet_count;
    __u64 byte_count;
};

// Mapa 1: Estatísticas globais (Array - Rápido)
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 2);
    __type(key, __u32);
    __type(value, struct host_metrics);
} proto_stats SEC(".maps");

// Mapa 2: Rastreamento de IPs Únicos (Hash - Permite contar cardinalidade)
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 8192); // Capacidade de monitorar 8k IPs simultâneos
    __type(key, __u32);        // IP de origem
    __type(value, __u64);      // Dummy value apenas para contar ocorrências
} unique_ips SEC(".maps");

SEC("xdp")
int xdp_monitor_prog(struct xdp_md *ctx) {
    void *data_end = (void *)(long)ctx->data_end;
    void *data = (void *)(long)ctx->data;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end) return XDP_PASS;
    if (eth->h_proto != bpf_htons(ETH_P_IP)) return XDP_PASS;

    struct iphdr *iph = data + sizeof(struct ethhdr);
    if ((void *)(iph + 1) > data_end) return XDP_PASS;

    __u32 src_ip = iph->saddr;
    __u64 pkt_len = data_end - data;
    __u32 stat_key;

    // --- MITIGAÇÃO DE DDoS (UDP) ---
    if (iph->protocol == 17) {
        // 1. Contador global
        stat_key = 0;
        struct host_metrics *stats = bpf_map_lookup_elem(&proto_stats, &stat_key);
        if (stats) {
            __sync_fetch_and_add(&stats->packet_count, 1);
            __sync_fetch_and_add(&stats->byte_count, pkt_len);
        }

        // 2. Registro de IP Único (Cardinalidade)
        __u64 one = 1;
        bpf_map_update_elem(&unique_ips, &src_ip, &one, BPF_NOEXIST);

        return XDP_DROP;
    }

    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";
