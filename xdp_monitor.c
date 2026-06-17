#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <bpf/bpf_endian.h>

// Mapa otimizado: Apenas contagem de pacotes e bytes por protocolo
struct host_metrics {
    __u64 packet_count;
    __u64 byte_count;
};

struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 2); // 0: UDP (Ataque), 1: TCP (Legítimo)
    __type(key, __u32);
    __type(value, struct host_metrics);
} proto_stats SEC(".maps");

SEC("xdp")
int xdp_monitor_prog(struct xdp_md *ctx) {
    void *data_end = (void *)(long)ctx->data_end;
    void *data = (void *)(long)ctx->data;

    // 1. Parsing Ethernet
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end) return XDP_PASS;
    if (eth->h_proto != bpf_htons(ETH_P_IP)) return XDP_PASS;

    // 2. Parsing IP
    struct iphdr *iph = data + sizeof(struct ethhdr);
    if ((void *)(iph + 1) > data_end) return XDP_PASS;

    __u64 pkt_len = data_end - data;
    __u32 stat_key;

    // --- MITIGAÇÃO DE DDoS VOLUMÉTRICO (UDP) ---
    if (iph->protocol == 17) { // Protocolo UDP
        stat_key = 0;
        struct host_metrics *stats = bpf_map_lookup_elem(&proto_stats, &stat_key);
        if (stats) {
            __sync_fetch_and_add(&stats->packet_count, 1);
            __sync_fetch_and_add(&stats->byte_count, pkt_len);
        }
        // Bloqueio agressivo de tráfego UDP (Assumindo que seu sensor não usa UDP)
        // Se usar, você pode adicionar um check de porta aqui antes do DROP
        return XDP_DROP;
    }

    // --- TRÁFEGO LEGÍTIMO (TCP/Outros) ---
    // Apenas monitoramos o volume total para fins estatísticos
    stat_key = 1;
    struct host_metrics *stats = bpf_map_lookup_elem(&proto_stats, &stat_key);
    if (stats) {
        __sync_fetch_and_add(&stats->packet_count, 1);
        __sync_fetch_and_add(&stats->byte_count, pkt_len);
    }

    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";
