
export CUDA_VERSION="10.1"; export CUDA_VISIBLE_DEVICES="0" ; timeout 5m nvprof --unified-memory-profiling off --concurrent-kernels off --print-gpu-trace -u us --demangling off --csv --log-file /work/util/hw_stats/../../hw_run/device-0/10.1/heartwall-rodinia-2.0-ft/__data_test_avi_1___data_result_1_txt/22.11.29-Tuesday--22:53:41.csv.cycle.0 /apps/src/..//bin/10.1/release/heartwall-rodinia-2.0-ft ./data/test.avi 1 ./data/result-1.txt
export CUDA_VERSION="10.1"; export CUDA_VISIBLE_DEVICES="0" ; timeout 5m nvprof --concurrent-kernels off --print-gpu-trace --events elapsed_cycles_sm --demangling off --csv --log-file /work/util/hw_stats/../../hw_run/device-0/10.1/heartwall-rodinia-2.0-ft/__data_test_avi_1___data_result_1_txt/22.11.29-Tuesday--22:53:41.csv.elapsed_cycles_sm.0 /apps/src/..//bin/10.1/release/heartwall-rodinia-2.0-ft ./data/test.avi 1 ./data/result-1.txt 