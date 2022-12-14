import os
import csv
from gpusims.bench import BenchmarkConfig
import gpusims.utils as utils


class Multi2SimBenchmarkConfig(BenchmarkConfig):
    @staticmethod
    def _run(path, inp, force=False, timeout_mins=5, **kwargs):
        print("multi2sim run:", inp)

        executable = path / inp.executable
        assert executable.is_file()
        utils.chmod_x(executable)

        results_dir = path / "results"
        os.makedirs(str(results_dir.absolute()), exist_ok=True)
        log_file = results_dir / "log.txt"
        kpl_stats_file = results_dir / "kpl-stats.txt"
        mem_stats_file = results_dir / "mem-stats.txt"

        cmd = [
            "m2s",
            "--mem-report",
            str(mem_stats_file.absolute()),
            "--kpl-report",
            str(kpl_stats_file.absolute()),
            "--kpl-config",
            str((path / "m2s.config.ini").absolute()),
            "--kpl-sim",
            "detailed",
            str(executable.absolute()),
            inp.args,
        ]
        cmd = " ".join(cmd)
        _, stdout, stderr, duration = utils.run_cmd(
            cmd,
            cwd=path,
            timeout_sec=timeout_mins * 60,
            save_to=results_dir / "m2s",
        )
        print("stdout:")
        print(stdout)
        print("stderr:")
        print(stderr)

        with open(str((results_dir / "sim_wall_time.csv").absolute()), "w") as f:
            output_writer = csv.writer(f)
            output_writer.writerow(["exec_time_sec"])
            output_writer.writerow([duration])

        with open(str(log_file.absolute()), "w") as f:
            f.write(stderr)

        # parse the stats file
        for stat_file in [kpl_stats_file, mem_stats_file]:
            csv_file = stat_file.with_suffix(".csv")
            _, stdout, stderr, _ = utils.run_cmd(
                [
                    "m2s-parse",
                    "--input",
                    str(stat_file.absolute()),
                    "--output",
                    str(csv_file.absolute()),
                ],
                cwd=path,
                timeout_sec=timeout_mins * 60,
                save_to=results_dir / "m2s-parse",
            )
            print("stdout:")
            print(stdout)
            print("stderr:")
            print(stderr)

    def load_dataframe(self, inp):
        results_dir = self.input_path(inp) / "results"
        assert results_dir.is_dir(), "{} is not a dir".format(results_dir)
        return build_multi2sim_df(
            kpl_stats_csv=results_dir / "kpl-stats.csv",
            mem_stats_csv=results_dir / "mem-stats.csv",
            sim_dur_csv=results_dir / "sim_wall_time.csv",
        )


def build_multi2sim_df(kpl_stats_csv, mem_stats_csv, sim_dur_csv=None):
    import pandas as pd

    mem_df = pd.read_csv(mem_stats_csv)
    mem_df["Stat"] = mem_df["Section"] + "." + mem_df["Stat"]
    del mem_df["Section"]

    mem_df = mem_df.set_index("Stat")
    mem_df = mem_df.T
    # return mem_df

    # df = pd.concat([pd.read_csv(csv_file) for csv_file in csv_files])
    kpl_df = pd.read_csv(kpl_stats_csv)
    per_sm_metrics = kpl_df[kpl_df["Section"].str.match(r"SM \d+")]
    per_sm_total = per_sm_metrics.groupby("Stat")
    per_sm_total = per_sm_total.sum(numeric_only=True).reset_index()
    per_sm_total["Section"] = "Total"
    # print(len(per_sm_total))
    # print(len(per_sm_metrics["Stat"].unique()))

    assert len(per_sm_total) == len(per_sm_metrics["Stat"].unique())

    kpl_df = pd.concat([kpl_df, per_sm_total])

    kpl_df["Stat"] = kpl_df["Section"] + "." + kpl_df["Stat"]
    del kpl_df["Section"]

    kpl_df = kpl_df.set_index("Stat")
    kpl_df = kpl_df.T

    # Total instruction count
    # SPU Instructions
    # SFU Instructions
    # LDS Instructions
    # IMU Instructions
    # DPU Instructions
    # BRU Instructions
    units = ["SPU", "SFU", "LDS", "IMU", "DPU", "BRU"]
    kpl_df["Total.Instructions"] = kpl_df[
        ["Total.{} Instructions".format(unit) for unit in units]
    ].sum(axis=1)

    df = pd.concat([kpl_df, mem_df], axis=1)
    if sim_dur_csv is not None:
        df["sim_wall_time"] = pd.read_csv(sim_dur_csv)["exec_time_sec"][0]

    return df
