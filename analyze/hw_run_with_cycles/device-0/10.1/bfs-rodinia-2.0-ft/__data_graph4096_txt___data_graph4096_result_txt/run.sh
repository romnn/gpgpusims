
export CUDA_VERSION="10.1"; export CUDA_VISIBLE_DEVICES="0" ; timeout 5m nvprof --unified-memory-profiling off --concurrent-kernels off --print-gpu-trace -u us --demangling off --csv --log-file /work/util/hw_stats/../../hw_run/device-0/10.1/bfs-rodinia-2.0-ft/__data_graph4096_txt___data_graph4096_result_txt/22.11.30-Wednesday--22:35:34.csv.cycle.0 /apps/src/..//bin/10.1/release/bfs-rodinia-2.0-ft ./data/graph4096.txt ./data/graph4096-result.txt
export CUDA_VERSION="10.1"; export CUDA_VISIBLE_DEVICES="0" ; timeout 5m nvprof --concurrent-kernels off --print-gpu-trace --events elapsed_cycles_sm --demangling off --csv --log-file /work/util/hw_stats/../../hw_run/device-0/10.1/bfs-rodinia-2.0-ft/__data_graph4096_txt___data_graph4096_result_txt/22.11.30-Wednesday--22:35:34.csv.elapsed_cycles_sm.0 /apps/src/..//bin/10.1/release/bfs-rodinia-2.0-ft ./data/graph4096.txt ./data/graph4096-result.txt 