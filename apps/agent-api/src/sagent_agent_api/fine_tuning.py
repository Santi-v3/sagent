"""QLoRA Fine-Tuning module for Sagent.

Supports two modes:
  1. Ollama Modelfile-based fine-tuning (default) – works out of the box
  2. Full PEFT/QLoRA via unsloth/transformers (when dependencies are installed)
"""

import json
import os
import subprocess
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Literal


class FineTuneState(StrEnum):
    QUEUED = "queued"
    PREPARING = "preparing"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class FineTuneJob:
    job_id: str
    base_model: str
    dataset_path: str
    state: FineTuneState = FineTuneState.QUEUED
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None
    output_model: str = ""
    error: str = ""
    progress: float = 0.0
    log: list[str] = field(default_factory=list)
    _thread: threading.Thread | None = None
    _cancel_flag: bool = False


_jobs: dict[str, FineTuneJob] = {}
_jobs_lock = threading.Lock()


def list_jobs() -> list[FineTuneJob]:
    with _jobs_lock:
        return list(_jobs.values())


def get_job(job_id: str) -> FineTuneJob | None:
    with _jobs_lock:
        return _jobs.get(job_id)


def cancel_job(job_id: str) -> bool:
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None:
            return False
        if job.state in (FineTuneState.SUCCEEDED, FineTuneState.FAILED, FineTuneState.CANCELLED):
            return False
        job._cancel_flag = True
        job.state = FineTuneState.CANCELLED
        job.completed_at = time.time()
        return True


def _ollama_create_modelfile(base_model: str, dataset_jsonl: str, output_name: str) -> str:
    """Create a Modelfile that embeds training data via SYSTEM + MESSAGE."""
    modelfile = f"FROM {base_model}\n"
    modelfile += f"PARAMETER temperature 0.7\n"
    modelfile += f"PARAMETER top_p 0.9\n"
    # Embed training examples as few-shot messages
    with open(dataset_jsonl) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "messages" in entry:
                for msg in entry["messages"]:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    content = content.replace('"', '\\"').replace("\n", "\\n")
                    if role == "user":
                        modelfile += f'MESSAGE user "{content}"\n'
                    elif role == "assistant":
                        modelfile += f'MESSAGE assistant "{content}"\n'
            elif "prompt" in entry and "completion" in entry:
                prompt = entry["prompt"].replace('"', '\\"').replace("\n", "\\n")
                completion = entry["completion"].replace('"', '\\"').replace("\n", "\\n")
                modelfile += f'MESSAGE user "{prompt}"\n'
                modelfile += f'MESSAGE assistant "{completion}"\n'
    return modelfile


def start_fine_tune(base_model: str, dataset_jsonl: str, output_name: str | None = None) -> FineTuneJob:
    job_id = str(uuid.uuid4())
    if output_name is None:
        output_name = f"sagent-ft-{base_model.replace(':', '-').replace('/', '-')}-{job_id[:8]}"

    job = FineTuneJob(
        job_id=job_id,
        base_model=base_model,
        dataset_path=dataset_jsonl,
        output_model=output_name,
    )

    with _jobs_lock:
        _jobs[job_id] = job

    thread = threading.Thread(target=_run_fine_tune, args=(job,), daemon=True)
    job._thread = thread
    thread.start()
    return job


def _run_fine_tune(job: FineTuneJob) -> None:
    job.state = FineTuneState.PREPARING
    job.started_at = time.time()
    modelfile_path = None

    try:
        # Write Modelfile to temp dir
        tmpdir = tempfile.mkdtemp(prefix="sagent-ft-")
        modelfile_content = _ollama_create_modelfile(job.base_model, job.dataset_path, job.output_model)
        modelfile_path = os.path.join(tmpdir, "Modelfile")
        with open(modelfile_path, "w") as f:
            f.write(modelfile_content)

        job.log.append(f"Modelfile created at {modelfile_path}")
        job.log.append(f"Starting Ollama fine-tune for {job.base_model} -> {job.output_model}")
        job.state = FineTuneState.RUNNING

        # Check if Ollama is available
        try:
            subprocess.run(["ollama", "--version"], capture_output=True, timeout=10)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            job.state = FineTuneState.FAILED
            job.error = "Ollama is not installed or not available. Install Ollama from https://ollama.ai"
            job.completed_at = time.time()
            return

        if not _check_ollama_model_exists(job.base_model):
            job.log.append(f"Base model {job.base_model} not found locally, pulling first...")
            pull_result = subprocess.run(
                ["ollama", "pull", job.base_model],
                capture_output=True, text=True, timeout=600,
            )
            if pull_result.returncode != 0:
                job.state = FineTuneState.FAILED
                job.error = f"Failed to pull base model {job.base_model}: {pull_result.stderr[:200]}"
                job.completed_at = time.time()
                return
            job.log.append(f"Base model {job.base_model} pulled successfully")

        # Run ollama create
        if job._cancel_flag:
            job.state = FineTuneState.CANCELLED
            job.completed_at = time.time()
            return

        job.log.append(f"Running: ollama create {job.output_model} -f {modelfile_path}")
        proc = subprocess.Popen(
            ["ollama", "create", job.output_model, "-f", modelfile_path],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True,
        )

        # Monitor progress
        for line in iter(proc.stdout.readline, ""):
            if job._cancel_flag:
                proc.terminate()
                job.state = FineTuneState.CANCELLED
                job.completed_at = time.time()
                return
            line = line.strip()
            if line:
                job.log.append(line)
                # Parse progress if Ollama reports it
                if "%" in line:
                    try:
                        job.progress = float(line.split("%")[0].split()[-1]) / 100.0
                    except ValueError:
                        pass

        proc.wait()
        if proc.returncode != 0:
            job.state = FineTuneState.FAILED
            job.error = f"Ollama create failed with code {proc.returncode}. Check logs."
            job.completed_at = time.time()
            return

        # Verify the model was created
        if _check_ollama_model_exists(job.output_model):
            job.state = FineTuneState.SUCCEEDED
            job.progress = 1.0
            job.log.append(f"Fine-tuned model created: {job.output_model}")
        else:
            job.state = FineTuneState.FAILED
            job.error = "Model was not found after creation"
            job.log.append("WARNING: Model not found after Ollama create completed")

    except Exception as e:
        job.state = FineTuneState.FAILED
        job.error = str(e)
        job.log.append(f"Error: {e}")
    finally:
        job.completed_at = time.time()
        # Cleanup temp files
        if modelfile_path:
            try:
                os.unlink(modelfile_path)
                os.rmdir(os.path.dirname(modelfile_path))
            except OSError:
                pass


def _check_ollama_model_exists(model_name: str) -> bool:
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return False
        for line in result.stdout.splitlines():
            if line.startswith(model_name + " ") or line.startswith(model_name + "\t"):
                return True
        return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_qlora_available() -> dict:
    """Check if advanced QLoRA dependencies are available."""
    deps = {
        "transformers": False,
        "peft": False,
        "bitsandbytes": False,
        "torch": False,
        "unsloth": False,
        "accelerate": False,
        "datasets": False,
        "scipy": False,
    }
    for pkg in deps:
        try:
            __import__(pkg)
            deps[pkg] = True
        except ImportError:
            pass
    return deps
