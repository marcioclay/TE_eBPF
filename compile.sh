#!/bin/bash
set -e

echo "Compiling eBPF program using Docker..."

# Use Ubuntu as builder to ensure we have clang and libbpf headers
# We mount the current directory to /code
sudo docker run --rm -v $(pwd):/code -w /code ubuntu:22.04 /bin/bash -c "
    apt-get update && \
    apt-get install -y clang llvm libbpf-dev gcc-multilib && \
    clang -O2 -g -target bpf -c xdp_monitor.c -o xdp_monitor.o
"

if [ -f xdp_monitor.o ]; then
    echo "Success! xdp_monitor.o created.😱😱😱"
else
    echo "Compilation failed.❌"
    exit 1
fi
