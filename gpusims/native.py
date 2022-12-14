import re
import os
import csv
from pprint import pprint  # noqa: F401
from gpusims.bench import BenchmarkConfig
from gpusims.cuda import get_devices
import gpusims.utils as utils


def convert_hw_csv(csv_file, output_csv_file):
    with open(str(csv_file.absolute()), "rU") as f:
        reader = csv.reader(f)

        # find the start of the csv dump
        csv_start_nvprof = re.compile(r"^==\d*==\s*Profiling result:\s*$")
        csv_start_nsight = re.compile(r"^==PROF== Disconnected[\S\s]*$")
        for row in reader:
            line = ", ".join(row)
            # print(line)
            if csv_start_nvprof.match(line) is not None:
                break
            if csv_start_nsight.match(line) is not None:
                break

        os.makedirs(output_csv_file.parent, exist_ok=True)
        with open(str(output_csv_file.absolute()), "w") as out:
            output_writer = csv.writer(out)

            # write the valid csv rows to new file
            for row in reader:
                output_writer.writerow(row)
        print("parsed stats:", output_csv_file.absolute())


def profile_nsight(path, inp, results_dir, r, timeout_mins=5):

    executable = path / inp.executable
    assert executable.is_file()
    utils.chmod_x(executable)

    metrics = [
        "gpc__cycles_elapsed.avg",
        "l1tex__t_sectors_pipe_lsu_mem_global_op_ld_lookup_hit.sum",
        "l1tex__t_sectors_pipe_lsu_mem_global_op_ld.sum",
        "l1tex__t_sectors_pipe_lsu_mem_global_op_st_lookup_hit.sum",
        "l1tex__t_sectors_pipe_lsu_mem_global_op_st.sum",
        "l1tex__t_sectors_pipe_lsu_mem_global_op_ld_lookup_hit.sum",
        "l1tex__t_sectors_pipe_lsu_mem_global_op_ld_lookup_miss.sum",
        "l1tex__t_sectors_pipe_lsu_mem_global_op_st_lookup_miss.sum",
        # add this as well?: "lts__t_sector_op_read_hit_rate.pct",
        "lts__t_sector_op_write_hit_rate.pct",
        "lts__t_sectors_srcunit_tex_op_read.sum",
        "lts__t_sectors_srcunit_tex_op_write.sum",
        "lts__t_sectors_srcunit_tex_op_read_lookup_hit.sum",
        "lts__t_sectors_srcunit_tex_op_write_lookup_hit.sum",
        "lts__t_sectors_srcunit_tex_op_read.sum.per_second",
        "lts__t_sectors_srcunit_tex_op_read_lookup_miss.sum",
        "lts__t_sectors_srcunit_tex_op_write_lookup_miss.sum",
        "dram__sectors_read.sum",
        "dram__sectors_write.sum",
        "dram__bytes_read.sum",
        "smsp__inst_executed.sum",
        "smsp__thread_inst_executed_per_inst_executed.ratio",
        "smsp__cycles_active.avg.pct_of_peak_sustained_elapsed",
        "idc__requests.sum,idc__requests_lookup_hit.sum",
        "sm__warps_active.avg.pct_of_peak_sustained_active",
        "sm__pipe_alu_cycles_active.sum",
        "sm__pipe_fma_cycles_active.sum",
        "sm__pipe_fp64_cycles_active.sum",
        "sm__pipe_shared_cycles_active.sum",
        "sm__pipe_tensor_cycles_active.sum",
        "sm__pipe_tensor_op_hmma_cycles_active.sum",
        "sm__cycles_elapsed.sum",
        "sm__cycles_active.sum",
        "sm__cycles_active.avg",
        "sm__cycles_elapsed.avg",
        "sm__sass_thread_inst_executed_op_integer_pred_on.sum",
        "sm__sass_thread_inst_executed_ops_dadd_dmul_dfma_pred_on.sum",
        "sm__sass_thread_inst_executed_ops_fadd_fmul_ffma_pred_on.sum",
        "sm__sass_thread_inst_executed_ops_hadd_hmul_hfma_pred_on.sum",
        "sm__inst_executed.sum",
        "sm__inst_executed_pipe_alu.sum",
        "sm__inst_executed_pipe_fma.sum",
        "sm__inst_executed_pipe_fp16.sum",
        "sm__inst_executed_pipe_fp64.sum",
        "sm__inst_executed_pipe_tensor.sum",
        "sm__inst_executed_pipe_tex.sum",
        "sm__inst_executed_pipe_xu.sum",
        "sm__inst_executed_pipe_lsu.sum",
        "sm__sass_thread_inst_executed_op_fp16_pred_on.sum",
        "sm__sass_thread_inst_executed_op_fp32_pred_on.sum",
        "sm__sass_thread_inst_executed_op_fp64_pred_on.sum",
        "sm__sass_thread_inst_executed_op_dmul_pred_on.sum",
        "sm__sass_thread_inst_executed_op_dfma_pred_on.sum",
        "sm__sass_thread_inst_executed.sum",
        "sm__sass_inst_executed_op_shared_st.sum",
        "sm__sass_inst_executed_op_shared_ld.sum",
        "sm__sass_inst_executed_op_memory_128b.sum",
        "sm__sass_inst_executed_op_memory_64b.sum",
        "sm__sass_inst_executed_op_memory_32b.sum",
        "sm__sass_inst_executed_op_memory_16b.sum",
        "sm__sass_inst_executed_op_memory_8b.sum",
    ]
    cmd = [
        "nv-nsight-cu-cli",
        "--metrics",
        ",".join(metrics),
        "--csv",
        "--page",
        "raw",
        "--target-processes",
        "all",
        str(executable.absolute()),
        inp.args,
    ]
    cmd = " ".join(cmd)

    log_file = results_dir / "{}.result.nsight.txt".format(r)
    _, stdout, stderr, _ = utils.run_cmd(
        cmd,
        cwd=path,
        timeout_sec=timeout_mins * 60,
        save_to=results_dir / "nsight",
    )
    print("stdout:")
    print(stdout)
    print("stderr:")
    print(stderr)

    with open(str(log_file.absolute()), "w") as f:
        f.write(stdout)


def profile_nvprof(path, inp, results_dir, r, timeout_mins=5):
    log_file = results_dir / "{}.result.nvprof.txt".format(r)

    executable = path / inp.executable
    assert executable.is_file()
    utils.chmod_x(executable)

    cmd = [
        "nvprof",
        "--unified-memory-profiling",
        "off",
        "--concurrent-kernels",
        "off",
        "--print-gpu-trace",
        "-u",
        "us",
        "--demangling",
        "off",
        "--csv",
        "--log-file",
        str(log_file.absolute()),
        str(executable.absolute()),
        inp.args,
    ]
    cmd = " ".join(cmd)
    try:
        _, stdout, stderr, _ = utils.run_cmd(
            cmd,
            cwd=path,
            timeout_sec=timeout_mins * 60,
            save_to=results_dir / "nvprof-kernels",
        )
        print("stdout:")
        print(stdout)
        print("stderr:")
        print(stderr)

        with open(str(log_file.absolute()), "r") as f:
            print("log file:")
            print(f.read())

    except utils.ExecError as e:
        with open(str(log_file.absolute()), "r") as f:
            print("log file:")
            print(f.read())
        raise e

    cycles_log_file = results_dir / "{}.result.nvprof.cycles.txt".format(r)
    cycles_cmd = [
        "nvprof",
        "--unified-memory-profiling",
        "off",
        "--concurrent-kernels",
        "off",
        "--print-gpu-trace",
        "--events",
        "elapsed_cycles_sm",
        "-u",
        "us",
        "--metrics",
        "all",
        "--demangling",
        "off",
        "--csv",
        "--log-file",
        str(cycles_log_file.absolute()),
        str(executable.absolute()),
        inp.args,
    ]
    cycles_cmd = " ".join(cycles_cmd)
    try:
        _, stdout, stderr, _ = utils.run_cmd(
            cycles_cmd,
            cwd=path,
            timeout_sec=timeout_mins * 60,
            save_to=results_dir / "nvprof-cycles",
        )
        print("stdout:")
        print(stdout)
        print("stderr:")
        print(stderr)

        with open(str(cycles_log_file.absolute()), "r") as f:
            print("log file:")
            print(f.read())

    except utils.ExecError as e:
        with open(str(cycles_log_file.absolute()), "r") as f:
            print("log file:")
            print(f.read())
        raise e


class NativeBenchmarkConfig(BenchmarkConfig):
    @staticmethod
    def _run(path, inp, repetitions=1, timeout_mins=5, parse_only=False, **kwargs):
        print("native run")
        pprint(
            dict(
                path=path,
                inp=inp,
                repetitions=repetitions,
                timeout_mins=timeout_mins,
                kwargs=kwargs,
            )
        )

        if not parse_only:
            devices = get_devices()
            if len(devices) < 1:
                raise AssertionError("no GPU device found")
            device = devices[0]
            if len(devices) > 1:
                print(
                    "warn: multiple GPU devices found, using compute capability of",
                    device.name,
                )

            print(
                "{} has compute capability {}.{}".format(
                    device.name, device.major, device.minor
                )
            )

            use_nsight = int(device.major) >= 8

            results_dir = path / "results"
            os.makedirs(str(results_dir.absolute()), exist_ok=True)

            for r in range(repetitions):
                args = dict(
                    path=path,
                    inp=inp,
                    results_dir=results_dir,
                    r=r,
                    timeout_mins=timeout_mins,
                )

                if use_nsight:
                    profile_nsight(**args)
                else:
                    profile_nvprof(**args)

        # parse the results
        nsight_results = sorted(list(results_dir.rglob("*result.nsight.txt")))
        nvprof_cycles_results = sorted(
            list(results_dir.rglob("*result.nvprof.cycles.txt"))
        )
        nvprof_results = sorted(list(results_dir.rglob("*result.nvprof.txt")))

        for result in nvprof_results + nvprof_cycles_results + nsight_results:
            convert_hw_csv(result, result.with_suffix(".csv"))

    def load_dataframe(self, inp):
        results_dir = self.input_path(inp) / "results"
        assert results_dir.is_dir(), "{} is not a dir".format(results_dir)

        nsight_results = sorted(list(results_dir.rglob("*result.nsight.csv")))
        nvprof_cycles_results = sorted(
            list(results_dir.rglob("*result.nvprof.cycles.csv"))
        )
        nvprof_results = sorted(list(results_dir.rglob("*result.nvprof.csv")))
        # pprint(nvprof_results)
        # pprint(nvprof_cycles_results)

        if len(nsight_results) > 0:
            return build_nsight_df(nsight_results)
        else:
            return build_nvprof_df(
                cycle_csv_files=nvprof_cycles_results,
                kernel_csv_files=nvprof_results,
            )


nvprof_index_cols = ["Stream", "Context", "Device", "Kernel", "Correlation_ID"]
nsight_index_cols = [
    "Stream",
    "Context",
    "device__attribute_display_name",
    "device__attribute_device_index",
    "Kernel Name",
    "ID",
]


def normalize_device_name(name):
    # Strip off device numbers, e.g. (0), (1)
    # that some profiler versions add to the end of device name
    return re.sub(r" \(\d+\)$", "", name)


def build_nsight_df(csv_files):
    import pandas as pd
    import numpy as np

    # pprint(csv_files)
    nsight_df_runs = []
    for csv_file in csv_files:
        nsight_df_run = pd.read_csv(csv_file)
        # add units to column names
        units = nsight_df_run.iloc[0].copy()
        units[~units.isnull()] = "_" + units[~units.isnull()]
        units = units.fillna("")
        # print("units")
        # print(units)
        nsight_df_run.columns = nsight_df_run.columns + units
        nsight_df_run = nsight_df_run.drop(nsight_df_run.index[0])
        nsight_df_runs.append(nsight_df_run)

    nsight_df = pd.concat(nsight_df_runs, ignore_index=False)
    # we have removed the units, so no nan values
    assert nsight_df["ID"].isnull().sum() == 0

    nsight_df = nsight_df.set_index(nsight_index_cols)
    # for debugging
    # return nsight_df

    non_numeric = [
        c
        for c in [
            "Process ID",
            "Process Name",
            "Host Name",
            "Kernel Time",
            "launch__func_cache_config",
            "nvlink__uuidDev0",
            "nvlink__uuidDev1",
        ]
        if c in nsight_df.columns
    ]
    # drop non numeric columns
    nsight_df = nsight_df.drop(columns=non_numeric)

    # convert to numeric
    def to_numeric_single(value, integer=False):
        if value in ["no data", "nan"]:
            return np.nan
        # ".avg", ".sum"
        # if nseconds unit then . is decimal point
        # value = value.replace(",", "")
        # 16.626,67
        # 15,935.33

        # if value.count(",") > 0 and value.count(".") > 0:
        #     # find returns lowest index (first occurence)
        #     sep = "." if value.find(".") < value.find(",") else ","
        #     value = value.replace(sep, "")

        #     # we can leave dots that will be left
        #     value = value.replace(",", ".")

        if value.count(",") > 1:
            # interpret as thousands instead of decimal point
            value = value.replace(",", "")

        if value.count(".") > 1:
            # interpret as thousands instead of decimal point
            value = value.replace(".", "")

        if integer:
            value = value.replace(".", "")
            value = value.replace(",", "")

        value = value.replace(",", ".")
        return value

    def to_numeric(series, integer=False):
        # find separator for the entire series
        series = series.astype(str)
        # sep = "."
        sep = ","
        for value in series:
            if value.count(",") > 0 and value.count(".") > 0:
                # find returns lowest index (first occurence)
                sep = "." if value.find(".") < value.find(",") else ","
                break
        series = series.apply(lambda v: v.replace(sep, ""))

        return pd.to_numeric(series.apply(to_numeric_single, integer=integer))

    integer_cols = []
    integer_cols += nsight_df.columns[
        nsight_df.columns.str.contains(pat="_nsecond$")
    ].tolist()
    integer_cols += nsight_df.columns[
        nsight_df.columns.str.contains(pat=r"\.sum_inst$")
    ].tolist()
    integer_cols += nsight_df.columns[
        nsight_df.columns.str.contains(pat=r"\.sum_sector$")
    ].tolist()
    # integer_cols += ["dram__sectors_read.sum_sector", "dram__sectors_write.sum_sector"]
    integer_cols = [c for c in integer_cols if c in nsight_df.columns]
    # print(integer_cols)
    nsight_df[integer_cols] = nsight_df[integer_cols].apply(
        to_numeric,
        integer=True,
    )
    nsight_df = nsight_df.apply(to_numeric)
    # return nsight_df

    # compute min, max, mean, stddev
    grouped_repetitions = nsight_df.groupby(level=nsight_index_cols)
    nsight_df = grouped_repetitions.mean()
    nsight_df_max = grouped_repetitions.max()
    nsight_df_max = nsight_df_max.rename(
        columns={c: c + "_max" for c in nsight_df_max.columns}
    )
    nsight_df_min = grouped_repetitions.min()
    nsight_df_min = nsight_df_min.rename(
        columns={c: c + "_min" for c in nsight_df_min.columns}
    )
    nsight_df_std = grouped_repetitions.std(ddof=0)
    nsight_df_std = nsight_df_std.rename(
        columns={c: c + "_std" for c in nsight_df_std.columns}
    )

    nsight_df = pd.concat(
        [nsight_df, nsight_df_max, nsight_df_min, nsight_df_std], axis=1
    )
    nsight_df = nsight_df.sort_index(axis=1)
    return nsight_df


def build_nvprof_kernel_df(csv_files):
    import pandas as pd

    hw_kernel_df = pd.concat(
        [pd.read_csv(csv) for csv in csv_files], ignore_index=False
    )
    # remove the units
    hw_kernel_df = hw_kernel_df[~hw_kernel_df["Correlation_ID"].isnull()]
    # remove memcopies
    hw_kernel_df = hw_kernel_df[
        ~hw_kernel_df["Name"].str.contains(r"\[CUDA memcpy .*\]")
    ]
    # name refers to kernels now
    hw_kernel_df = hw_kernel_df.rename(columns={"Name": "Kernel"})
    # remove columns that are only relevant for memcopies
    # df = df.loc[:,df.notna().any(axis=0)]
    hw_kernel_df = hw_kernel_df.drop(
        columns=["Size", "Throughput", "SrcMemType", "DstMemType"]
    )
    # set the correct dtypes
    hw_kernel_df = hw_kernel_df.astype(
        {
            "Start": "float64",
            "Duration": "float64",
            "Static SMem": "float64",
            "Dynamic SMem": "float64",
            "Device": "string",
            "Kernel": "string",
        }
    )

    hw_kernel_df["Device"] = hw_kernel_df["Device"].apply(normalize_device_name)

    hw_kernel_df = hw_kernel_df.set_index(nvprof_index_cols)

    # compute min, max, mean, stddev
    grouped_repetitions = hw_kernel_df.groupby(level=nvprof_index_cols)
    hw_kernel_df = grouped_repetitions.mean()
    hw_kernel_df_max = grouped_repetitions.max()
    hw_kernel_df_max = hw_kernel_df_max.rename(
        columns={c: c + "_max" for c in hw_kernel_df_max.columns}
    )
    hw_kernel_df_min = grouped_repetitions.min()
    hw_kernel_df_min = hw_kernel_df_min.rename(
        columns={c: c + "_min" for c in hw_kernel_df_min.columns}
    )
    hw_kernel_df_std = grouped_repetitions.std(ddof=0)
    hw_kernel_df_std = hw_kernel_df_std.rename(
        columns={c: c + "_std" for c in hw_kernel_df_std.columns}
    )
    return hw_kernel_df


def build_nvprof_cycles_df(csv_files):
    import pandas as pd

    # ref: https://docs.nvidia.com/cuda/profiler-users-guide/index.html#metrics-reference # noqa: E501
    hw_cycle_df = pd.concat([pd.read_csv(csv) for csv in csv_files], ignore_index=False)
    # remove the units
    hw_cycle_df = hw_cycle_df[~hw_cycle_df["Correlation_ID"].isnull()]
    # remove textual utilization metrics (high, low, ...)
    hw_cycle_df = hw_cycle_df[
        hw_cycle_df.columns[~hw_cycle_df.columns.str.contains(r".*_utilization")]
    ]
    hw_cycle_df["Device"] = hw_cycle_df["Device"].apply(normalize_device_name)
    hw_cycle_df = hw_cycle_df.set_index(nvprof_index_cols)
    # convert to numeric values
    hw_cycle_df = hw_cycle_df.convert_dtypes()
    hw_cycle_df = hw_cycle_df.apply(pd.to_numeric)

    # compute min, max, mean, stddev
    grouped_repetitions = hw_cycle_df.groupby(level=nvprof_index_cols)
    hw_cycle_df = grouped_repetitions.mean()
    hw_cycle_df_max = grouped_repetitions.max()
    hw_cycle_df_max = hw_cycle_df_max.rename(
        columns={c: c + "_max" for c in hw_cycle_df_max.columns}
    )
    hw_cycle_df_min = grouped_repetitions.min()
    hw_cycle_df_min = hw_cycle_df_min.rename(
        columns={c: c + "_min" for c in hw_cycle_df_min.columns}
    )
    hw_cycle_df_std = grouped_repetitions.std(ddof=0)
    hw_cycle_df_std = hw_cycle_df_std.rename(
        columns={c: c + "_std" for c in hw_cycle_df_std.columns}
    )

    hw_cycle_df = pd.concat(
        [hw_cycle_df, hw_cycle_df_max, hw_cycle_df_min, hw_cycle_df_std], axis=1
    )
    return hw_cycle_df


def build_nvprof_df(kernel_csv_files, cycle_csv_files):
    # pprint(kernel_csv_files)
    # pprint(cycle_csv_files)
    kernel_df = build_nvprof_kernel_df(kernel_csv_files)
    # return kernel_df
    # print("kernels shape", kernel_df.shape)
    cycle_df = build_nvprof_cycles_df(cycle_csv_files)
    # return cycle_df
    # print("cycles shape", cycle_df.shape)

    # same number of repetitions
    assert kernel_df.shape[0] == cycle_df.shape[0]

    inner_hw_df = kernel_df.join(cycle_df, how="inner")

    # sort columns
    inner_hw_df = inner_hw_df.sort_index(axis=1)
    # print("inner join shape", inner_hw_df.shape)

    # assert no nan values
    assert inner_hw_df.isna().any().sum() == 0
    return inner_hw_df
