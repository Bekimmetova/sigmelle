"""
Avtomatik tekshiruvchi (judge).
Talaba kodini kompilyatsiya qiladi, har bir testda ishga tushiradi,
vaqt/xotira limitlarini nazorat qiladi va natijani bazaga yozadi.
"""
import json
import os
import resource
import shutil
import subprocess
import sqlite3
import tempfile
import threading
import time

BASE = os.path.dirname(os.path.abspath(__file__))
PROBLEMS_DIR = os.path.join(BASE, "problems")
DB_PATH = os.environ.get("OLIMP_DB", os.path.join(BASE, "data", "olimpiada.db"))

PYTHON_TL_FACTOR = 3        # Python uchun vaqt limiti necha baravar ko'p
COMPILE_TIMEOUT = 30
MAX_OUTPUT = 32 * 1024 * 1024

LANGS = {
    "cpp": {"name": "C++17 (g++)", "file": "main.cpp",
            "compile": ["g++", "-O2", "-std=c++17", "-o", "main", "main.cpp"],
            "run": ["./main"]},
    "python": {"name": "Python 3", "file": "main.py",
               "compile": ["python3", "-m", "py_compile", "main.py"],
               "run": ["python3", "main.py"]},
}

VERDICT_UZ = {
    "AC": "To'g'ri javob",
    "WA": "Noto'g'ri javob",
    "TLE": "Vaqt limiti oshdi",
    "MLE": "Xotira limiti oshdi",
    "RE": "Dastur xatosi (Runtime Error)",
    "CE": "Kompilyatsiya xatosi",
    "PARTIAL": "Qisman to'g'ri",
}


def load_problem(pid):
    d = os.path.join(PROBLEMS_DIR, pid)
    meta = json.load(open(os.path.join(d, "meta.json"), encoding="utf-8"))
    tdir = os.path.join(d, "tests")
    tests = sorted(f[:-3] for f in os.listdir(tdir) if f.endswith(".in"))
    meta["tests"] = [(os.path.join(tdir, t + ".in"), os.path.join(tdir, t + ".out")) for t in tests]
    return meta


def _limits(cpu_sec, mem_mb, is_python):
    def setter():
        os.setsid()
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_sec + 1, cpu_sec + 2))
        mem = (mem_mb + (64 if is_python else 16)) * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
        resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_OUTPUT, MAX_OUTPUT))
        resource.setrlimit(resource.RLIMIT_NPROC, (512, 512))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    return setter


def _same(out_bytes, ans_path):
    with open(ans_path, "rb") as f:
        return out_bytes.split() == f.read().split()


RUN_SEM = threading.BoundedSemaphore(int(os.environ.get("RUN_PARALLEL", "2")))


def run_samples(code, lang, pid):
    """Talaba kodini faqat namunaviy testlarda ishga tushiradi (ball berilmaydi)."""
    prob = load_problem(pid)
    samples = [prob["tests"][k - 1] for k in prob.get("samples", [])]
    with RUN_SEM:
        return judge(code, lang, pid, tests=samples, keep_output=True)


def judge(code, lang, pid, tests=None, keep_output=False):
    """Natija: dict(verdict, score, passed, total, time_ms, details, compile_log)."""
    prob = load_problem(pid)
    if tests is not None:
        prob["tests"] = tests
    cfg = LANGS[lang]
    total = len(prob["tests"])
    work = tempfile.mkdtemp(prefix="olimp_")
    try:
        with open(os.path.join(work, cfg["file"]), "w", encoding="utf-8") as f:
            f.write(code)
        try:
            c = subprocess.run(cfg["compile"], cwd=work, capture_output=True, timeout=COMPILE_TIMEOUT)
            ok, log = c.returncode == 0, (c.stderr or c.stdout).decode("utf-8", "replace")
        except subprocess.TimeoutExpired:
            ok, log = False, "Kompilyatsiya vaqti tugadi"
        if not ok:
            return {"verdict": "CE", "score": 0, "passed": 0, "total": total,
                    "time_ms": 0, "details": [], "compile_log": log[-4000:]}

        is_py = lang == "python"
        tl = prob["time_limit"] * (PYTHON_TL_FACTOR if is_py else 1)
        details, passed, max_t, first_bad = [], 0, 0, None
        for i, (tin, tout) in enumerate(prob["tests"], 1):
            start = time.monotonic()
            with open(tin, "rb") as fin:
                try:
                    p = subprocess.Popen(cfg["run"], cwd=work, stdin=fin, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         preexec_fn=_limits(int(tl) + 1, prob["memory_limit"], is_py))
                    out, err = p.communicate(timeout=tl * 1.5 + 0.5)
                    rc = p.returncode
                    timed_out = False
                except subprocess.TimeoutExpired:
                    os.killpg(p.pid, 9)
                    out, err = p.communicate()
                    rc, timed_out = -9, True
            el = time.monotonic() - start
            ms = min(int(el * 1000), int(tl * 1000) + 1)
            max_t = max(max_t, ms)
            errtxt = err.decode("utf-8", "replace")
            if timed_out or el > tl or rc == -24:   # -24 = SIGXCPU (CPU limiti)
                v = "TLE"
            elif rc != 0:
                v = "MLE" if ("MemoryError" in errtxt or "bad_alloc" in errtxt) else "RE"
            elif _same(out, tout):
                v = "AC"
            else:
                v = "WA"
            if v == "AC":
                passed += 1
            elif first_bad is None:
                first_bad = v
            item = {"test": i, "verdict": v, "time_ms": ms}
            if keep_output:
                item["input"] = open(tin).read()[:2000]
                item["expected"] = open(tout).read()[:2000]
                item["output"] = out.decode("utf-8", "replace")[:2000]
                item["stderr"] = errtxt[-1000:]
            details.append(item)

        score = round(prob["points"] * passed / total) if total else 0
        if passed == total:
            verdict = "AC"
        elif passed > 0:
            verdict = "PARTIAL"
        else:
            verdict = first_bad or "WA"
        return {"verdict": verdict, "score": score, "passed": passed, "total": total,
                "time_ms": max_t, "details": details, "compile_log": ""}
    finally:
        shutil.rmtree(work, ignore_errors=True)


# ---------------- Navbat (queue) ishchisi ----------------
def _db():
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.row_factory = sqlite3.Row
    return con


def worker_loop(stop_event=None):
    while not (stop_event and stop_event.is_set()):
        con = _db()
        row = con.execute("SELECT * FROM submissions WHERE status='queue' ORDER BY id LIMIT 1").fetchone()
        if not row:
            con.close(); time.sleep(1); continue
        cur = con.execute("UPDATE submissions SET status='running' WHERE id=? AND status='queue'", (row["id"],))
        con.commit()
        if cur.rowcount == 0:
            con.close(); continue
        try:
            res = judge(row["code"], row["lang"], row["problem"])
        except Exception as e:  # tizim xatosi
            res = {"verdict": "RE", "score": 0, "passed": 0, "total": 0, "time_ms": 0,
                   "details": [], "compile_log": f"Tizim xatosi: {e}"}
        con.execute("""UPDATE submissions SET status='done', verdict=?, score=?, passed=?, total=?,
                       time_ms=?, details=?, compile_log=? WHERE id=?""",
                    (res["verdict"], res["score"], res["passed"], res["total"], res["time_ms"],
                     json.dumps(res["details"]), res["compile_log"], row["id"]))
        con.commit(); con.close()


def start_workers(n=1):
    con = _db()
    con.execute("UPDATE submissions SET status='queue' WHERE status='running'")
    con.commit(); con.close()
    for _ in range(n):
        threading.Thread(target=worker_loop, daemon=True).start()


if __name__ == "__main__":
    # Alohida jarayon sifatida ishga tushirish:  python3 judge.py
    start_workers(int(os.environ.get("JUDGE_WORKERS", "2")))
    print("Judge ishlamoqda... (Ctrl+C — to'xtatish)")
    while True:
        time.sleep(3600)
