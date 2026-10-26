"""Fixed command builder and bounded, persistent, one-job process manager."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shlex
import signal
import subprocess
import sys
import threading
import time
import uuid

from .records import load, require

SAFE_TESTS = ["tests/test_core.py", "tests/test_milestone1.py", "tests/test_gate_b.py",
    "tests/test_prototype_rl.py", "tests/test_mechanism_pilot.py", "tests/test_mechanism_cli.py",
    "tests/test_artifact_restore.py",
    "test_timing.py", "test_vpa_strategies.py", "examples/test_environment.py",
    "closeout-tests/test_independent.py", "f5-evidence/test_schema.py"]
PILOT_KEYS = ("blocks", "episodes", "contexts", "train_episodes", "validation", "calibration", "benign_test", "seed_base")


def now():
    return datetime.now(timezone.utc).isoformat()


def integer(data, key, default, low, high):
    value = data.get(key, default)
    require(type(value) is int and low <= value <= high, f"{key}: integer {low}–{high} required")
    return value


def choice(data, key, values, default):
    value = data.get(key, default)
    require(value in values, f"{key}: unsupported choice")
    return value


def build(data, repo, state, catalog):
    require(isinstance(data, dict), "Configuration must be an object")
    allowed = {"type", "name", "detector", "attacker", "seeds", "episodes", "campaigns",
               "max_steps", "blocks", "contexts", "train_episodes", "validation", "calibration",
               "benign_test", "seed_base", "mode", "reference", "repeat", "reload",
               "selection", "confirm_expensive"}
    require(not set(data)-allowed, f"Unsupported configuration fields: {sorted(set(data)-allowed)}")
    kind = choice(data, "type", ("legacy", "pilot", "tests", "verify"), "legacy")
    mode = choice(data, "mode", ("main", "repeat", "reload"), "main")
    name = data.get("name", "")
    require(isinstance(name, str) and re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,47}", name),
            "Output name: use 1–48 lowercase letters, digits, hyphens or underscores")
    state, repo = Path(state).resolve(), Path(repo).resolve()
    output = state/"runs"/name
    require(not output.exists() and not output.is_symlink(), "Output name already exists; choose a new name")
    require((state/"runs").resolve() == state/"runs", "Output root cannot be a symlink")
    args = [sys.executable, "-B", "-s", "-u"]
    result = dict(kind=kind, output=str(output), name=name, mode=mode,
                  workload=None, expensive=False, timeout=1800)
    if kind == "tests":
        selection = choice(data, "selection", ("rl", "regression", "dashboard"), "rl")
        files = ["tests/test_prototype_rl.py"] if selection == "rl" else (
            SAFE_TESTS if selection == "regression" else ["dashboard/test_dashboard.py"])
        args += ["-m", "pytest", *files, "-q", "--basetemp", str(output/"tmp"),
                 "--junitxml", str(output/"tests.xml")]
    elif kind == "verify":
        paths = [catalog.descriptor(data.get(k)) for k in ("reference", "repeat", "reload")]
        require(len({p["kind"] for p in paths}) == 1, "Cannot verify across experiment versions")
        require(len({str(p["path"]) for p in paths}) == 3,
                "Verification requires three distinct run directories, not one run reused")
        script = "verify_mechanism_pilot.py" if paths[0]["kind"] == "pilot" else "verify_prototype_outputs.py"
        args += [script]
        for key, path in zip(("reference", "repeat", "reload"), paths):
            args += ["--"+key, str(path["path"])]
        args += ["--output", str(output/"verification.json")]
    else:
        config = dict(data)
        reference = None
        if mode != "main":
            reference = catalog.descriptor(data.get("reference"))
            require(reference["kind"] == kind, "Reference experiment version does not match")
            config = catalog.dataset(reference["id"])["config"]
        if kind == "legacy":
            require(not any(k in data for k in ("blocks", "contexts", "train_episodes",
                    "validation", "calibration", "benign_test", "seed_base")),
                    "Legacy CLI does not support pilot configuration")
            detector = choice(config, "detector", ("both", "xgboost", "random_forest"), "both")
            attacker = choice(config, "attacker", ("all", "static", "adaptive", "rl", "untrained_rl"), "all")
            seeds = config.get("seeds", [101])
            require(isinstance(seeds, list) and 1 <= len(seeds) <= 9 and
                    all(type(s) is int and 0 <= s <= 2**31-1 for s in seeds) and
                    len(set(seeds)) == len(seeds), "seeds: 1–9 distinct nonnegative 31-bit integers required")
            episodes = integer(config, "episodes", 60, 1, 300)
            campaigns = integer(config, "campaigns", 6, 1, 40)
            steps = integer(config, "max_steps", 30, 1, 30)
            args += ["run_prototype.py", "--output", str(output),
                "--detector", detector, "--attacker", attacker, "--seeds", *map(str, seeds),
                "--episodes", str(episodes), "--campaigns", str(campaigns), "--max-steps", str(steps)]
            if mode == "reload":
                args += ["--policy-dir", str(reference["path"])]
            # Preserve reference thresholds rather than substitute browser defaults.
            for key in ("flag_threshold", "block_threshold"):
                if key in config:
                    args += ["--"+key.replace("_", "-"), str(config[key])]
            evaluations = 2*campaigns*len(seeds)*(2 if detector == "both" else 1)*(4 if attacker == "all" else 1)
            training = 0 if mode == "reload" or attacker in ("static", "adaptive", "untrained_rl") else episodes*len(seeds)*(2 if detector == "both" else 1)
        else:
            require(not any(k in data for k in ("detector", "attacker", "seeds", "campaigns", "max_steps")),
                    "Pilot CLI fixes both detectors, five arms, two mechanisms and 30 steps")
            limits = dict(blocks=(1,9,1), episodes=(1,300,10), contexts=(1,40,3),
                train_episodes=(4,1000,1000), validation=(1,400,400),
                calibration=(2,1000,1000), benign_test=(1,400,400),
                seed_base=(0,2**31-1,51000))
            checked = {k: integer(config, k, default, lo, hi) for k, (lo, hi, default) in limits.items()}
            args += ["-m", "src.experiments.mechanism_pilot", "--output", str(output)]
            for key, value in checked.items():
                args += ["--"+key.replace("_", "-"), str(value)]
            if mode == "reload":
                args += ["--reload-from", str(reference["path"])]
            evaluations = 20*checked["blocks"]*checked["contexts"]
            training = 0 if mode == "reload" else 4*checked["blocks"]*checked["episodes"]
        result["workload"] = dict(evaluation_campaigns=evaluations, training_episodes=training,
            note="Derived episode counts, not a runtime estimate; repeat is not independent replication.")
        result["expensive"] = training > 600 or evaluations > 1000
        result["timeout"] = 7200 if result["expensive"] else 1800
    result.update(argv=args, command=shlex.join(args), cwd=str(repo))
    return result


def redact(line):
    return re.sub(r"(?i)((?:api[_-]?key|authorization|password|secret|access[_-]?token)\s*[:=]\s*)\S+",
                  r"\1[REDACTED]", line)


class Jobs:
    def __init__(self, repo, state, catalog):
        self.repo, self.state, self.catalog = Path(repo), Path(state), catalog
        self.lock, self.active, self.process = threading.RLock(), None, None
        self.jobs, self.events = {}, []
        for sub in ("runs", "jobs", "home", "tmp", "cache"):
            (self.state/sub).mkdir(parents=True, exist_ok=True)
        if (self.state/"activity.jsonl").exists():
            self.events = [json.loads(x) for x in (self.state/"activity.jsonl").read_text().splitlines()]
        for path in (self.state/"jobs").glob("*.json"):
            job = load(path)
            if job["status"] in ("running", "starting", "cancelling"):
                job.update(status="interrupted", end=now(), note="Server restarted; no job was resumed")
                self.persist(job)
            self.jobs[job["id"]] = job

    def event(self, action, **details):
        record = dict(timestamp=now(), action=action, **details)
        self.events.append(record)
        with (self.state/"activity.jsonl").open("a") as f:
            f.write(json.dumps(record)+"\n")

    def persist(self, job):
        path = self.state/"jobs"/(job["id"]+".json")
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(job, indent=2))
        temp.replace(path)

    def list(self):
        with self.lock:
            return sorted(self.jobs.values(), key=lambda j: j["start"], reverse=True)

    def submit(self, data):
        with self.lock:
            require(self.active is None, "A job is already active; stop it or wait for completion")
            plan = build(data, self.repo, self.state, self.catalog)
            require(not plan["expensive"] or data.get("confirm_expensive") is True,
                    "Expensive run requires explicit confirmation")
            output = Path(plan["output"])
            # Experiment CLIs require nonexistent output directories.
            if plan["kind"] in ("tests", "verify"):
                output.mkdir()
            job = dict(id=uuid.uuid4().hex, **plan, start=now(), end=None,
                       status="starting", exit_code=None, elapsed=0, counts=None)
            self.jobs[job["id"]] = job
            self.active = job["id"]
            self.persist(job)
            self.event("job_started", job=job["id"], name=job["name"], kind=job["kind"])
            threading.Thread(target=self._run, args=(job,), daemon=True).start()
            return job

    def _run(self, job):
        started, cancelled = time.monotonic(), False
        env = dict(PATH=os.defpath, HOME=str(self.state/"home"), TMPDIR=str(self.state/"tmp"),
            PYTHONHASHSEED="17", PYTHONDONTWRITEBYTECODE="1", PYTHONUNBUFFERED="1", TZ="UTC",
            OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
            PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", GIT_OPTIONAL_LOCKS="0",
            PYTEST_ADDOPTS=f"-o cache_dir={self.state/'cache'}")
        log = self.state/"jobs"/(job["id"]+".jsonl")
        log_lock, written = threading.Lock(), [0]

        def emit(channel, text):
            with log_lock:
                if written[0] > 10_000_000:
                    if not job.get("log_truncated"):
                        job["log_truncated"] = True
                        with log.open("a") as f:
                            f.write(json.dumps(dict(timestamp=now(), channel="system",
                                text="Log retention limit reached (10 MB); subsequent output omitted."))+"\n")
                    return
                row = dict(timestamp=now(), channel=channel, text=redact(text.rstrip())[:16384])
                value = json.dumps(row)+"\n"
                with log.open("a") as f:
                    f.write(value)
                written[0] += len(value)

        def read(stream, channel):
            for line in iter(lambda: stream.readline(16384), ""):
                emit(channel, line)
            stream.close()
        try:
            with self.lock:
                if job["status"] == "cancelling":
                    cancelled = True
                else:
                    self.process = subprocess.Popen(job["argv"], cwd=self.repo, env=env,
                        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        text=True, encoding="utf-8", errors="replace", start_new_session=True)
                    job["pid"], job["status"] = self.process.pid, "running"
                    self.persist(job)
            if not cancelled:
                process = self.process
                readers = [threading.Thread(target=read, args=(stream, name), daemon=True)
                           for stream, name in ((process.stdout, "stdout"), (process.stderr, "stderr"))]
                for reader in readers:
                    reader.start()
                while process.poll() is None:
                    if time.monotonic()-started > job["timeout"]:
                        job["status"] = "timed_out"
                        self._terminate(process)
                        emit("system", "Execution deadline reached; process group terminated")
                        break
                    time.sleep(.1)
                process.wait()
                for reader in readers:
                    reader.join(3)
                job["exit_code"] = process.returncode
            if job["status"] == "cancelling" or cancelled:
                job["status"] = "cancelled"
            elif job["status"] != "timed_out":
                job["status"] = "completed" if job["exit_code"] == 0 else "failed"
        except Exception as exc:
            job["status"] = "failed"
            emit("system", f"Launch failure: {type(exc).__name__}: {exc}")
        finally:
            job.update(end=now(), elapsed=round(time.monotonic()-started, 3))
            if job["kind"] == "verify" and (Path(job["output"])/"verification.json").exists():
                try:
                    job["verification"] = load(Path(job["output"])/"verification.json")
                except (ValueError, OSError):
                    job["note"] = "Verification result malformed; inspect the preserved log"
            xml = Path(job["output"])/"tests.xml"
            if xml.exists():
                import xml.etree.ElementTree as ET
                try:
                    suites = list(ET.parse(xml).getroot().iter("testsuite"))
                    job["counts"] = {k: sum(int(s.get(k, 0)) for s in suites)
                                     for k in ("tests", "failures", "errors", "skipped")}
                    lines = "".join(r["text"] for r in self.logs(job["id"], 0)["lines"])
                    match = re.search(r"(\d+) deselected", lines)
                    job["counts"]["deselected"] = int(match[1]) if match else 0
                    job["counts"]["passed"] = (job["counts"]["tests"]-job["counts"]["failures"]
                                              -job["counts"]["errors"]-job["counts"]["skipped"])
                except (ET.ParseError, ValueError):
                    job["counts"] = None
                    job["note"] = "Incomplete or malformed JUnit; counts unavailable"
                    emit("system", job["note"])
            with self.lock:
                self.persist(job)
                self.active, self.process = None, None
                self.event("job_"+job["status"], job=job["id"], name=job["name"],
                           exit_code=job["exit_code"])

    @staticmethod
    def _terminate(process):
        if process.poll() is not None:
            return
        try:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                pass
            # A parent may exit while a descendant ignores TERM. Kill any
            # remaining member of this isolated group, not just the parent.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        except ProcessLookupError:
            pass

    def cancel(self, identifier):
        with self.lock:
            require(identifier == self.active, "This job is not active")
            job = self.jobs[identifier]
            job["status"] = "cancelling"
            self.persist(job)
            process = self.process
        if process:
            self._terminate(process)
        return dict(status="cancelling")

    def logs(self, identifier, cursor):
        require(identifier in self.jobs, "Unknown job")
        path = self.state/"jobs"/(identifier+".jsonl")
        lines = path.read_text().splitlines() if path.exists() else []
        return dict(lines=[json.loads(x) for x in lines[cursor:cursor+1000]],
                    cursor=min(len(lines), cursor+1000), total=len(lines))
