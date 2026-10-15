from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import traceback
from pathlib import Path

# cuBLAS requires this to be set before CUDA is initialized for reproducible
# matrix-multiplication kernels on CUDA >= 10.2. Child workers inherit it.
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from article09.audit import audit_dataset
from article09.config import load_config, sha256_file, sha256_json
from article09.data import DATASETS, prepare_raw_datasets
from article09.features import extract_dataset, prefetch_dinov2
from article09.models import benchmark_one_backend
from article09.runner import (
    completion_audit,
    evaluate_test,
    freeze_protocol,
    run_backend_benchmark,
    run_final_worker,
    run_pilot,
)
from article09.utils import (
    atomic_write_json,
    atomic_write_text,
    capture_environment,
    ensure_directories,
    mark_task,
    task_complete,
    task_context,
    utc_now,
)


def setup(config: dict, resume: bool) -> None:
    ensure_directories()
    task_id = "setup"
    if resume and task_complete(task_id, config["_config_hash"]):
        return
    with task_context(task_id, config["_config_hash"]):
        environment = capture_environment()
        atomic_write_json(ROOT / "environment" / "hardware.json", environment)
        completed = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True, check=True
        )
        atomic_write_text(ROOT / "environment" / "pip_freeze.txt", completed.stdout)
        subprocess.run(
            [
                sys.executable,
                "-m",
                "ipykernel",
                "install",
                "--user",
                "--name",
                "article09_quantum",
                "--display-name",
                "Article09 Quantum Environment",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        atomic_write_text(ROOT / "environment" / "python_executable.txt", sys.executable + "\n")
        atomic_write_text(ROOT / "environment" / "protocol_config.sha256", config["_config_hash"] + "\n")


def data_stage(config: dict, resume: bool) -> None:
    task_id = "data-download"
    if resume and task_complete(task_id, config["_config_hash"]):
        return
    with task_context(task_id, config["_config_hash"]):
        counts = prepare_raw_datasets()
        atomic_write_json(ROOT / "data" / "manifests" / "raw_counts.json", counts)


def audit_stage(config: dict, resume: bool) -> None:
    for dataset in DATASETS:
        raw_path = ROOT / "data" / "manifests" / f"{dataset}_raw.csv"
        input_hash = sha256_json(
            {"raw": sha256_file(raw_path), "audit": config["audit"], "split_seed": config["project"]["split_seed"]}
        )
        task_id = f"audit-{dataset}"
        if resume and task_complete(task_id, input_hash):
            continue
        with task_context(task_id, input_hash):
            audit_dataset(dataset, config)
    reports = {
        dataset: json.loads(
            (ROOT / "data" / "audit" / f"{dataset}_audit_report.json").read_text(encoding="utf-8")
        )
        for dataset in DATASETS
    }
    atomic_write_json(ROOT / "data" / "audit" / "audit_report.json", reports)


def embeddings_stage(config: dict, resume: bool) -> None:
    prefetch_id = "dinov2-prefetch"
    if not (resume and task_complete(prefetch_id, config["features"]["encoder"])):
        with task_context(prefetch_id, config["features"]["encoder"]):
            prefetch_dinov2()
    commands = [
        [
            sys.executable,
            str(ROOT / "run_article09.py"),
            "_extract_worker",
            "--datasets",
            "cifar10,pathmnist",
            "--device",
            "cuda:0",
        ],
        [
            sys.executable,
            str(ROOT / "run_article09.py"),
            "_extract_worker",
            "--datasets",
            "eurosat",
            "--device",
            "cuda:1",
        ],
    ]
    if resume:
        for command in commands:
            command.append("--resume")
    processes = [subprocess.Popen(command, cwd=ROOT) for command in commands]
    codes = [process.wait() for process in processes]
    if any(code != 0 for code in codes):
        raise RuntimeError(f"Embedding workers failed with exit codes {codes}")


def final_stage(config: dict, resume: bool) -> None:
    seeds = list(config["project"]["final_seeds"])
    split_at = (len(seeds) + 1) // 2
    assignments = [(seeds[:split_at], "cuda:0"), (seeds[split_at:], "cuda:1")]
    processes = []
    for worker_seeds, device in assignments:
        command = [
            sys.executable,
            str(ROOT / "run_article09.py"),
            "_final_worker",
            "--seeds",
            ",".join(map(str, worker_seeds)),
            "--device",
            device,
        ]
        if resume:
            command.append("--resume")
        env = os.environ.copy()
        env["OMP_NUM_THREADS"] = "8"
        env["MKL_NUM_THREADS"] = "8"
        processes.append(subprocess.Popen(command, cwd=ROOT, env=env))
    codes = [process.wait() for process in processes]
    if any(code != 0 for code in codes):
        raise RuntimeError(f"Final workers failed with exit codes {codes}")


def report_stage(config: dict, resume: bool) -> None:
    from article09.reporting import build_all_reports

    build_all_reports(config, resume=resume)


def notebook_stage(config: dict, resume: bool) -> None:
    from article09.notebook import build_and_execute_notebook

    build_and_execute_notebook(config, resume=resume)


def article_stage(config: dict, resume: bool) -> None:
    from article09.article import build_manuscript_and_models

    build_manuscript_and_models(config, resume=resume)


STAGES = [
    "setup",
    "data",
    "audit",
    "embeddings",
    "backend",
    "pilot",
    "freeze",
    "final",
    "test",
    "report",
    "notebook",
    "article",
]


def run_stage(stage: str, config: dict, resume: bool, args: argparse.Namespace) -> None:
    if stage == "setup":
        setup(config, resume)
    elif stage == "data":
        data_stage(config, resume)
    elif stage == "audit":
        audit_stage(config, resume)
    elif stage == "embeddings":
        embeddings_stage(config, resume)
    elif stage == "backend":
        run_backend_benchmark(config, resume)
    elif stage == "pilot":
        run_pilot(config, resume, device=args.device)
    elif stage == "freeze":
        freeze_protocol(config, resume)
    elif stage == "final":
        final_stage(config, resume)
    elif stage == "test":
        evaluate_test(config, resume)
        audit = completion_audit(config)
        if audit["incomplete"]:
            raise RuntimeError(f"Completion audit found {audit['incomplete']} incomplete runs")
    elif stage == "report":
        report_stage(config, resume)
    elif stage == "notebook":
        notebook_stage(config, resume)
    elif stage == "article":
        article_stage(config, resume)
    else:
        raise KeyError(stage)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Article 09 resumable research pipeline")
    parser.add_argument("stage", choices=STAGES + ["all", "_extract_worker", "_final_worker", "_backend_probe"])
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--config", default=str(ROOT / "configs" / "protocol.yaml"))
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--datasets", default="")
    parser.add_argument("--seeds", default="")
    parser.add_argument("--backend", default="default.qubit")
    parser.add_argument("--output", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    ensure_directories()
    if args.stage == "_backend_probe":
        result = benchmark_one_backend(config, args.backend)
        atomic_write_json(args.output, result)
        return 0
    if args.stage == "_extract_worker":
        for dataset in args.datasets.split(","):
            if dataset:
                extract_dataset(dataset, args.device, config, resume=args.resume)
        return 0
    if args.stage == "_final_worker":
        seeds = [int(value) for value in args.seeds.split(",") if value]
        run_final_worker(config, seeds, args.device, resume=args.resume)
        return 0

    marker = ROOT / "state" / ("SUCCESS" if args.stage == "all" else f"{args.stage.upper()}_SUCCESS")
    failed = ROOT / "state" / "FAILED"
    if marker.exists():
        marker.unlink()
    if failed.exists():
        failed.unlink()
    try:
        stages = STAGES if args.stage == "all" else [args.stage]
        for stage in stages:
            print(f"[{utc_now()}] START {stage}", flush=True)
            run_stage(stage, config, args.resume, args)
            print(f"[{utc_now()}] COMPLETE {stage}", flush=True)
        atomic_write_text(marker, utc_now() + "\n")
        return 0
    except Exception as exc:
        atomic_write_text(
            failed,
            json.dumps(
                {"time": utc_now(), "stage": args.stage, "error": repr(exc), "traceback": traceback.format_exc()},
                indent=2,
            ),
        )
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

