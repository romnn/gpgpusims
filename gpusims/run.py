import itertools
from pprint import pprint
from pathlib import Path
from invoke import task
import datetime

import gpusims
import gpusims.cuda as cuda
import gpusims.utils as utils
from gpusims.bench import parse_benchmarks


ROOT_DIR = Path(__file__).parent.parent


@task(
    help={
        "benchmark-dir": "Benchmark dir",
        "run-dir": "Run dir",
        "simulator": "simulator to run",
        "benchmark": "list of benchmarks to run",
        "config": "list of configurations to run",
        "repetitions": "number of repetitions (only applies to native execution)",
        "timeout-mins": "timeout in minutes per simulation run",
        "slurm": "submit jobs using slurm (only for native and accelsim-sass)",
        "slurm-node": "the slurm node to use",
        "trace-only": "only generate traces, but do not simulate",
        "parse-only": "only parse results",
    },
    iterable=["benchmark", "config"],
)
def run(
    c,
    run_dir,
    benchmark,
    config,
    simulator,
    repetitions=3,
    benchmark_dir=None,
    timeout_mins=20,
    slurm=False,
    slurm_node=None,
    trace_only=False,
    parse_only=False,
):
    """Run benchmarks"""
    simulator = simulator.lower()
    benchmark = [b.lower() for b in benchmark]

    if benchmark_dir is not None:
        benchmark_dir = Path(benchmark_dir)
    else:
        benchmark_dir = Path(__file__).parent.parent / "benchmarks"

    print("running benchmarks ...")
    assert benchmark_dir.is_dir()
    if simulator not in gpusims.SIMULATORS:
        raise ValueError("unknown simulator: {}".format(simulator))

    configs = gpusims.config.parse_configs(benchmark_dir / "configs" / "configs.yml")
    benchmarks = parse_benchmarks(benchmark_dir / "benchmarks.yml")
    assert len(configs) > 0
    assert len(benchmarks) > 0

    run_dir = Path(run_dir)
    sim_run_dir = run_dir / simulator.lower()

    if len(config) < 1:
        if simulator == gpusims.NATIVE:
            # find current hardware
            devices = cuda.get_devices()
            config = [devices[0].name]
        else:
            # run all configs
            config = list(configs.keys())

    if len(benchmark) < 1:
        benchmark = list(benchmarks.keys())

    pending = []
    for c, b in list(itertools.product(config, benchmark)):
        conf = configs.get(c.lower())
        if simulator == gpusims.NATIVE:
            if conf is None:
                # create a mock config
                conf = gpusims.config.Config(
                    key=c.lower(), name=c.lower(), path=None, spec={}
                )
            else:
                # do not inject any config files into the run dir
                conf = gpusims.config.Config(
                    key=conf.key, name=conf.name, path=None, spec=conf.spec
                )

        if conf is None:
            have = ",".join(configs.keys())
            raise KeyError("no such config: {} (have: {})".format(c, have))

        bench = benchmarks.get(b)
        if bench is None:
            have = ",".join(benchmarks.keys())
            raise KeyError("no such benchmark: {} (have: {})".format(b, have))

        # check if the benchmark is enabled
        if not bench.enabled(simulator):
            print("skipping {} {} ...".format(c, b))
            continue

        print("adding {} {} ...".format(c, b))
        bench_cls = gpusims.SIMULATORS[simulator.lower()]
        bench_config = bench_cls(
            run_dir=sim_run_dir,
            benchmark=bench,
            config=conf,
        )

        pending.append(bench_config)

    for b in pending:
        pprint(b)
        if slurm:
            cmd = [
                "inv",
                "run",
                "--benchmark-dir",
                str(benchmark_dir.absolute()),
                "--run-dir",
                str(run_dir.absolute()),
                "--simulator",
                simulator,
                "--config",
                b.config.key,
                "--repetitions",
                str(repetitions),
                "--timeout-mins",
                str(timeout_mins),
            ]
            if trace_only:
                cmd += ["--trace-only"]
            if parse_only:
                cmd += ["--parse-only"]
            # pprint(cmd)

            # slurm_job = []
            slurm_job = [
                "#!/bin/sh",
                # 00:15:00"
                "#SBATCH --time={}".format(
                    utils.duration_to_slurm(datetime.timedelta(minutes=timeout_mins))
                ),
                "#SBATCH -N 1",
                "#SBATCH -C {}".format("A6000" if slurm_node is None else slurm_node),
                "#SBATCH --gres=gpu:1",
                " ".join(cmd),
            ]
            # slurm_job += [
            print("\n".join(slurm_job))

            slurm_job_file = (
                ROOT_DIR
                / ".slurm"
                / "-".join(
                    [
                        simulator,
                        b.benchmark.sanitized_name(),
                        utils.slugify(b.config.key.lower()),
                    ]
                )
            )
            slurm_job_file = slurm_job_file.with_suffix(".slurm")
            print(slurm_job_file)

            # module load cuda11.2/toolkit

            # !/bin/bash
            # SBATCH --time=00:15:00
            # SBATCH -N 2
            # SBATCH --ntasks-per-node=16

            # . /etc/bashrc
            # DAS-5:
            # . /etc/profile.d/modules.sh
            # DAS-6:
            # . /etc/profile.d/lmod.sh
            # module load openmpi/gcc/64

        else:
            for inp in b.benchmark.inputs:
                if inp.enabled(simulator):
                    b.run(
                        inp,
                        repetitions=repetitions,
                        # force=force,
                        timeout_mins=timeout_mins,
                        trace_ony=trace_only,
                        parse_only=parse_only,
                        # slurm=slurm,
                    )
