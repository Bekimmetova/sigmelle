"""
"Algoritmlarni loyihalash" fanidan onlayn olimpiada sayti.
Ikki bo'lim: TEST (25 savol) va MASALALAR (8 masala). Har birining o'z vaqt chegarasi bor,
talaba bo'limlarni istalgan tartibda boshlaydi. Uch xil reyting: test, masalalar, umumiy.
Ishga tushirish (sinov uchun):  python3 app.py
"""
import csv
import difflib
import io
import json
import os
import random
import re
import secrets
import sqlite3
from datetime import datetime, timedelta
from functools import wraps

import markdown
from flask import (Flask, Response, abort, flash, g, jsonify, redirect,
                   render_template, request, session, url_for)
from markupsafe import Markup
from werkzeug.security import check_password_hash, generate_password_hash

import judge

BASE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(BASE, "data"), exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config["MAX_CONTENT_LENGTH"] = 256 * 1024

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
CONTEST_TITLE = os.environ.get("CONTEST_TITLE", "Algoritmlarni loyihalash — talabalar olimpiadasi")
SUBMIT_COOLDOWN = 10      # ikki yuborish orasidagi minimal soniya
RUN_COOLDOWN = 5          # namunada sinashlar orasidagi minimal soniya
MAX_CODE = 64 * 1024
GRACE_SEC = 10            # taymer tugagandan keyin javob saqlash uchun zaxira soniya
DT_FMT = "%Y-%m-%dT%H:%M"
SECTIONS = {"test": "Test", "problems": "Masalalar"}
EVENT_UZ = {"tab_hidden": "Boshqa oynaga/tabga o'tdi", "blur": "Brauzer oynasidan chiqdi",
            "fullscreen_exit": "To'liq ekrandan chiqdi", "paste": "Matn joylashga urindi",
            "copy": "Matn nusxalashga urindi", "auto_finish": "Qoidabuzarlik sababli yakunlandi"}

# ---------------- Ma'lumotlar bazasi ----------------
SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, full_name TEXT NOT NULL,
  group_name TEXT NOT NULL, pw_hash TEXT NOT NULL, is_admin INTEGER DEFAULT 0, created TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS submissions(
  id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, problem TEXT NOT NULL,
  lang TEXT NOT NULL, code TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'queue',
  verdict TEXT, score INTEGER DEFAULT 0, passed INTEGER DEFAULT 0, total INTEGER DEFAULT 0,
  time_ms INTEGER DEFAULT 0, details TEXT, compile_log TEXT, created TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_sub_user ON submissions(user_id);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS attempts(
  user_id INTEGER NOT NULL, section TEXT NOT NULL, started_at TEXT NOT NULL,
  finished_at TEXT, extra_minutes INTEGER DEFAULT 0, PRIMARY KEY(user_id, section));
CREATE TABLE IF NOT EXISTS quiz_answers(
  user_id INTEGER NOT NULL, qid INTEGER NOT NULL, answer TEXT NOT NULL, updated TEXT NOT NULL,
  PRIMARY KEY(user_id, qid));
CREATE TABLE IF NOT EXISTS events(
  id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, section TEXT, kind TEXT NOT NULL,
  ip TEXT, at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_ev_user ON events(user_id);
"""

DEFAULTS = {
    "registration": "1", "freeze_minutes": "0",
    "test_minutes": "30", "problems_minutes": "120",
    "weight_test": "40", "weight_problems": "60",
    "guard_test": "1",          # testda tab/oyna/to'liq ekran nazorati
    "guard_problems": "0",      # masalalarda tab/oyna nazorati
    "block_paste_problems": "0",
    "max_violations": "0",      # 0 = faqat qayd etiladi; N>0 bo'lsa N-qoidabuzarlikda bo'lim yakunlanadi
}


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(judge.DB_PATH, timeout=30)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_):
    db = g.pop("db", None)
    if db:
        db.close()


def init_db():
    con = sqlite3.connect(judge.DB_PATH)
    con.executescript(SCHEMA)
    con.execute("PRAGMA journal_mode=WAL")
    now = datetime.now()
    defaults = dict(DEFAULTS, start=now.strftime(DT_FMT), end=(now + timedelta(hours=4)).strftime(DT_FMT))
    for k, v in defaults.items():
        con.execute("INSERT OR IGNORE INTO settings VALUES(?,?)", (k, v))
    if not con.execute("SELECT 1 FROM users WHERE username=?", (ADMIN_USER,)).fetchone():
        con.execute("INSERT INTO users(username,full_name,group_name,pw_hash,is_admin,created) VALUES(?,?,?,?,1,?)",
                    (ADMIN_USER, "Administrator", "-", generate_password_hash(ADMIN_PASSWORD), now.isoformat()))
    con.commit()
    con.close()


def setting(key):
    if "settings" not in g:
        g.settings = {r["key"]: r["value"] for r in get_db().execute("SELECT * FROM settings")}
    return g.settings.get(key, DEFAULTS.get(key))


def isetting(key):
    try:
        return int(setting(key))
    except (TypeError, ValueError):
        return int(DEFAULTS.get(key, 0))


def contest_times():
    return datetime.strptime(setting("start"), DT_FMT), datetime.strptime(setting("end"), DT_FMT)


def contest_state():
    s, e = contest_times()
    now = datetime.now()
    return "before" if now < s else ("running" if now < e else "finished")


def client_ip():
    return (request.headers.get("CF-Connecting-IP") or
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or request.remote_addr)


# ---------------- Bo'limlar (shaxsiy taymer) ----------------
def section_info(uid, sec, db=None):
    """state: none | active | done ; deadline = boshlanish + davomiylik (lekin olimpiada tugashidan oshmaydi)."""
    db = db or get_db()
    r = db.execute("SELECT * FROM attempts WHERE user_id=? AND section=?", (uid, sec)).fetchone()
    if not r:
        return {"state": "none", "start": None, "deadline": None, "end": None}
    start = datetime.fromisoformat(r["started_at"])
    _, c_end = contest_times()
    # admin qo'shgan qo'shimcha daqiqalar olimpiada tugash vaqtidan keyin ham amal qiladi
    deadline = min(start + timedelta(minutes=isetting(f"{sec}_minutes")), c_end) + \
        timedelta(minutes=r["extra_minutes"] or 0)
    fin = datetime.fromisoformat(r["finished_at"]) if r["finished_at"] else None
    now = datetime.now()
    done = fin is not None or now >= deadline
    end = fin or deadline
    return {"state": "done" if done else "active", "start": start, "deadline": deadline,
            "end": min(end, deadline), "finished_at": fin}


def active_section(uid):
    for s in SECTIONS:
        if section_info(uid, s)["state"] == "active":
            return s
    return None


def finish_section(uid, sec, reason=None):
    db = get_db()
    db.execute("UPDATE attempts SET finished_at=? WHERE user_id=? AND section=? AND finished_at IS NULL",
               (datetime.now().isoformat(), uid, sec))
    if reason:
        db.execute("INSERT INTO events(user_id,section,kind,ip,at) VALUES(?,?,?,?,?)",
                   (uid, sec, reason, client_ip(), datetime.now().isoformat()))
    db.commit()


# ---------------- Masalalar ----------------
_PROBLEMS = None


def problems():
    global _PROBLEMS
    if _PROBLEMS is None:
        res = []
        for pid in sorted(os.listdir(judge.PROBLEMS_DIR)):
            d = os.path.join(judge.PROBLEMS_DIR, pid)
            if not os.path.isfile(os.path.join(d, "meta.json")):
                continue
            meta = judge.load_problem(pid)
            md = open(os.path.join(d, "statement.md"), encoding="utf-8").read()
            samples = []
            for k in meta.get("samples", []):
                tin, tout = meta["tests"][k - 1]
                samples.append((open(tin).read().rstrip(), open(tout).read().rstrip()))
            res.append({"id": pid, "title": meta["title"], "points": meta["points"],
                        "time_limit": meta["time_limit"], "memory_limit": meta["memory_limit"],
                        "statement": markdown.markdown(md, extensions=["tables", "fenced_code"]),
                        "samples": samples, "ntests": len(meta["tests"])})
        _PROBLEMS = res
    return _PROBLEMS


def problems_max():
    return sum(p["points"] for p in problems())


def problem_by_id(pid):
    for p in problems():
        if p["id"] == pid:
            return p
    abort(404)


# ---------------- Test savollari ----------------
_QUIZ = None


def quiz():
    global _QUIZ
    if _QUIZ is None:
        qs = json.load(open(os.path.join(BASE, "quiz", "questions.json"), encoding="utf-8"))
        for q in qs:
            q["html"] = Markup(markdown.markdown(q["text"]))
        _QUIZ = qs
    return _QUIZ


def quiz_max():
    return sum(q["points"] for q in quiz())


def quiz_for_user(uid):
    """Har bir talaba uchun savollar va variantlar tartibi aralashtiriladi (lekin doimiy)."""
    rng = random.Random(f"quiz-{uid}")
    qs = [dict(q) for q in quiz()]
    rng.shuffle(qs)
    for q in qs:
        if q["type"] in ("single", "multi"):
            idx = list(range(len(q["options"])))
            rng.shuffle(idx)
            q["view_options"] = [(i, q["options"][i]) for i in idx]
        elif q["type"] == "order":
            idx = list(range(len(q["items"])))
            while idx == sorted(idx):
                rng.shuffle(idx)
            q["view_items"] = [(i, q["items"][i]) for i in idx]
        elif q["type"] == "match":
            idx = list(range(len(q["right"])))
            rng.shuffle(idx)
            q["view_right"] = [(i, q["right"][i]) for i in idx]
    return qs


def _norm(s):
    s = str(s).lower().replace("ё", "е")
    s = re.sub(r"[,;\[\]\(\)\.]", " ", s)
    return " ".join(s.split())


def grade_question(q, ans):
    if ans is None:
        return False
    try:
        t = q["type"]
        if t == "single":
            return int(ans) == q["answer"]
        if t == "multi":
            return sorted(int(x) for x in ans) == sorted(q["answer"])
        if t == "text":
            return _norm(ans) in {_norm(a) for a in q["answer"]}
        if t == "order":
            return [int(x) for x in ans] == list(range(len(q["items"])))
        if t == "match":
            return [int(x) if x not in (None, "") else -1 for x in ans] == q["answer"]
    except (TypeError, ValueError):
        return False
    return False


def user_answers(uid, db=None):
    db = db or get_db()
    return {r["qid"]: json.loads(r["answer"]) for r in
            db.execute("SELECT qid, answer FROM quiz_answers WHERE user_id=?", (uid,))}


def quiz_score(uid, db=None):
    ans = user_answers(uid, db)
    return sum(q["points"] for q in quiz() if grade_question(q, ans.get(q["id"])))


# ---------------- Yordamchilar ----------------
def current_user():
    if "me" not in g:
        uid = session.get("uid")
        g.me = get_db().execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone() if uid else None
    return g.me


def login_required(f):
    @wraps(f)
    def w(*a, **k):
        if not current_user():
            return redirect(url_for("login", next=request.path))
        return f(*a, **k)
    return w


def admin_required(f):
    @wraps(f)
    def w(*a, **k):
        u = current_user()
        if not u or not u["is_admin"]:
            abort(403)
        return f(*a, **k)
    return w


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return session["csrf"]


@app.before_request
def check_csrf():
    if request.method == "POST":
        tok = request.form.get("csrf") or request.headers.get("X-CSRF")
        if not tok or tok != session.get("csrf"):
            abort(400, "CSRF token xato. Sahifani yangilab, qayta urinib ko'ring.")


@app.context_processor
def inject():
    s, e = contest_times()
    me = current_user()
    act = None
    if me and not me["is_admin"]:
        a = active_section(me["id"])
        if a:
            act = {"section": a, "name": SECTIONS[a], "deadline": section_info(me["id"], a)["deadline"]}
    guard_on = bool(act and setting(f"guard_{act['section']}") == "1")
    return {"me": me, "csrf_token": csrf_token, "contest_title": CONTEST_TITLE, "guard_on": guard_on,
            "state": contest_state(), "c_start": s, "c_end": e, "VERDICT_UZ": judge.VERDICT_UZ,
            "LANGS": judge.LANGS, "active": act, "setting": setting, "SECTIONS": SECTIONS}


# ---------------- Ro'yxatdan o'tish / kirish ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if setting("registration") != "1":
        flash("Ro'yxatdan o'tish yopilgan. O'qituvchiga murojaat qiling.", "err")
        return redirect(url_for("login"))
    if request.method == "POST":
        un = request.form.get("username", "").strip().lower()
        fn = " ".join(request.form.get("full_name", "").split())
        gr = request.form.get("group_name", "").strip()
        pw = request.form.get("password", "")
        err = None
        if not (3 <= len(un) <= 30) or not re.fullmatch(r"[a-z0-9_]+", un):
            err = "Login 3–30 belgi, faqat lotin harflari, raqamlar va _ bo'lishi kerak."
        elif len(fn) < 5 or len(gr) < 2:
            err = "F.I.Sh. va guruhni to'liq kiriting."
        elif len(pw) < 6:
            err = "Parol kamida 6 belgidan iborat bo'lsin."
        elif get_db().execute("SELECT 1 FROM users WHERE username=?", (un,)).fetchone():
            err = "Bu login band."
        if err:
            flash(err, "err")
        else:
            db = get_db()
            cur = db.execute("INSERT INTO users(username,full_name,group_name,pw_hash,created) VALUES(?,?,?,?,?)",
                             (un, fn, gr, generate_password_hash(pw), datetime.now().isoformat()))
            db.execute("INSERT INTO events(user_id,kind,ip,at) VALUES(?,?,?,?)",
                       (cur.lastrowid, "register", client_ip(), datetime.now().isoformat()))
            db.commit()
            session.clear()
            session["uid"] = cur.lastrowid
            flash("Muvaffaqiyatli ro'yxatdan o'tdingiz!", "ok")
            return redirect(url_for("index"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        un = request.form.get("username", "").strip().lower()
        u = get_db().execute("SELECT * FROM users WHERE username=?", (un,)).fetchone()
        if u and check_password_hash(u["pw_hash"], request.form.get("password", "")):
            session.clear()
            session["uid"] = u["id"]
            db = get_db()
            db.execute("INSERT INTO events(user_id,kind,ip,at) VALUES(?,?,?,?)",
                       (u["id"], "login", client_ip(), datetime.now().isoformat()))
            db.commit()
            nxt = request.args.get("next", "")
            return redirect(nxt if nxt.startswith("/") and not nxt.startswith("//") else url_for("index"))
        flash("Login yoki parol noto'g'ri.", "err")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ---------------- Bosh sahifa va bo'limlarni boshlash ----------------
@app.route("/")
def index():
    me = current_user()
    info = {}
    if me and not me["is_admin"]:
        info = {s: section_info(me["id"], s) for s in SECTIONS}
    return render_template("index.html", info=info, nq=len(quiz()), qmax=quiz_max(),
                           np=len(problems()), pmax=problems_max())


@app.route("/start/<sec>", methods=["POST"])
@login_required
def start_section(sec):
    me = current_user()
    if sec not in SECTIONS or me["is_admin"]:
        abort(404)
    if contest_state() != "running":
        flash("Olimpiada hozir davom etmayapti.", "err")
    elif section_info(me["id"], sec)["state"] != "none":
        flash("Bu bo'lim allaqachon boshlangan.", "err")
    elif active_section(me["id"]):
        flash("Avval boshlangan bo'limni yakunlang.", "err")
    else:
        db = get_db()
        db.execute("INSERT INTO attempts(user_id,section,started_at) VALUES(?,?,?)",
                   (me["id"], sec, datetime.now().isoformat()))
        db.execute("INSERT INTO events(user_id,section,kind,ip,at) VALUES(?,?,?,?,?)",
                   (me["id"], sec, "start", client_ip(), datetime.now().isoformat()))
        db.commit()
        return redirect(url_for("test_page" if sec == "test" else "problem_list"))
    return redirect(url_for("index"))


@app.route("/finish/<sec>", methods=["POST"])
@login_required
def finish(sec):
    me = current_user()
    if sec in SECTIONS and section_info(me["id"], sec)["state"] == "active":
        finish_section(me["id"], sec, "finish")
        flash(f"\"{SECTIONS[sec]}\" bo'limi yakunlandi.", "ok")
    return redirect(url_for("index"))


# ---------------- TEST ----------------
@app.route("/test")
@login_required
def test_page():
    me = current_user()
    if me["is_admin"]:
        return redirect(url_for("admin_quiz_key"))
    info = section_info(me["id"], "test")
    if info["state"] == "none":
        flash("Testni bosh sahifadan boshlang.", "err")
        return redirect(url_for("index"))
    answers = user_answers(me["id"])
    qs = quiz_for_user(me["id"])
    if info["state"] == "done":
        reveal = contest_state() == "finished"
        results = {q["id"]: grade_question(q, answers.get(q["id"])) for q in qs}
        return render_template("test_result.html", qs=qs, answers=answers, results=results, reveal=reveal,
                               score=quiz_score(me["id"]), qmax=quiz_max(), info=info)
    return render_template("test.html", qs=qs, answers=answers, info=info, guard=setting("guard_test") == "1")


@app.route("/api/quiz/save", methods=["POST"])
@login_required
def api_quiz_save():
    me = current_user()
    info = section_info(me["id"], "test")
    now = datetime.now()
    if info["state"] == "none" or info.get("finished_at") or now > info["deadline"] + timedelta(seconds=GRACE_SEC):
        return jsonify({"ok": False, "error": "Test vaqti tugagan"}), 403
    data = request.get_json(silent=True) or {}
    qid = data.get("qid")
    if not any(q["id"] == qid for q in quiz()):
        return jsonify({"ok": False}), 400
    db = get_db()
    db.execute("INSERT OR REPLACE INTO quiz_answers VALUES(?,?,?,?)",
               (me["id"], qid, json.dumps(data.get("answer"), ensure_ascii=False)[:2000], now.isoformat()))
    db.commit()
    return jsonify({"ok": True})


# ---------------- Qoidabuzarlik qaydlari ----------------
@app.route("/api/event", methods=["POST"])
@login_required
def api_event():
    me = current_user()
    data = request.get_json(silent=True) or {}
    sec, kind = data.get("section"), data.get("kind")
    if sec not in SECTIONS or kind not in EVENT_UZ or section_info(me["id"], sec)["state"] != "active":
        return jsonify({"ok": False})
    db = get_db()
    last = db.execute("SELECT at FROM events WHERE user_id=? AND kind NOT IN ('login','start','register') "
                      "ORDER BY id DESC LIMIT 1", (me["id"],)).fetchone()
    now = datetime.now()
    if not (last and (now - datetime.fromisoformat(last["at"])).total_seconds() < 1.5):
        db.execute("INSERT INTO events(user_id,section,kind,ip,at) VALUES(?,?,?,?,?)",
                   (me["id"], sec, kind, client_ip(), now.isoformat()))
        db.commit()
    cnt = violation_count(me["id"], sec)
    mx = isetting("max_violations")
    finished = False
    if mx and cnt >= mx:
        finish_section(me["id"], sec, "auto_finish")
        finished = True
    return jsonify({"ok": True, "count": cnt, "max": mx, "finished": finished})


def violation_count(uid, sec=None, db=None):
    db = db or get_db()
    kinds = "('tab_hidden','blur','fullscreen_exit','paste','copy')"
    if sec:
        return db.execute(f"SELECT COUNT(*) c FROM events WHERE user_id=? AND section=? AND kind IN {kinds}",
                          (uid, sec)).fetchone()["c"]
    return db.execute(f"SELECT COUNT(*) c FROM events WHERE user_id=? AND kind IN {kinds}", (uid,)).fetchone()["c"]


# ---------------- MASALALAR ----------------
def problems_visible(me):
    return me["is_admin"] or section_info(me["id"], "problems")["state"] != "none"


@app.route("/problems")
@login_required
def problem_list():
    me = current_user()
    if not problems_visible(me):
        flash("Masalalar bo'limini bosh sahifadan boshlang.", "err")
        return redirect(url_for("index"))
    best = {r["problem"]: r["s"] for r in get_db().execute(
        "SELECT problem, MAX(score) s FROM submissions WHERE user_id=? AND status='done' GROUP BY problem",
        (me["id"],))}
    return render_template("problems.html", problems=problems(), best=best,
                           info=section_info(me["id"], "problems"),
                           guard=setting("guard_problems") == "1" and not me["is_admin"])


def can_submit(me):
    return me["is_admin"] or section_info(me["id"], "problems")["state"] == "active"


@app.route("/problem/<pid>", methods=["GET", "POST"])
@login_required
def problem(pid):
    me = current_user()
    if not problems_visible(me):
        flash("Masalalar bo'limini bosh sahifadan boshlang.", "err")
        return redirect(url_for("index"))
    p = problem_by_id(pid)
    db = get_db()
    if request.method == "POST":
        if not can_submit(me):
            flash("Masalalar bo'limi vaqti tugagan — yechim qabul qilinmaydi.", "err")
            return redirect(url_for("problem", pid=pid))
        lang = request.form.get("lang")
        code = request.form.get("code", "")
        f = request.files.get("file")
        if f and f.filename and setting("block_paste_problems") != "1":
            code = f.read().decode("utf-8", "replace")
        last = db.execute("SELECT created FROM submissions WHERE user_id=? ORDER BY id DESC LIMIT 1",
                          (me["id"],)).fetchone()
        if lang not in judge.LANGS:
            flash("Dasturlash tilini tanlang.", "err")
        elif not code.strip():
            flash("Kod bo'sh.", "err")
        elif len(code.encode()) > MAX_CODE:
            flash("Kod hajmi 64 KB dan oshmasligi kerak.", "err")
        elif last and not me["is_admin"] and \
                (datetime.now() - datetime.fromisoformat(last["created"])).total_seconds() < SUBMIT_COOLDOWN:
            flash(f"Yechimlar orasida kamida {SUBMIT_COOLDOWN} soniya kuting.", "err")
            session[f"draft_{pid}"] = code[:MAX_CODE]
        else:
            cur = db.execute("INSERT INTO submissions(user_id,problem,lang,code,created) VALUES(?,?,?,?,?)",
                             (me["id"], pid, lang, code, datetime.now().isoformat()))
            db.commit()
            session["last_lang"] = lang
            session.pop(f"draft_{pid}", None)
            flash("Yechim tekshiruvga yuborildi.", "ok")
            return redirect(url_for("submission", sid=cur.lastrowid))
        return redirect(url_for("problem", pid=pid))
    best = db.execute("SELECT MAX(score) s FROM submissions WHERE user_id=? AND problem=? AND status='done'",
                      (me["id"], pid)).fetchone()["s"]
    last_code = db.execute("SELECT code, lang FROM submissions WHERE user_id=? AND problem=? ORDER BY id DESC LIMIT 1",
                           (me["id"], pid)).fetchone()
    return render_template("problem.html", p=p, best=best, last_lang=session.get("last_lang", "cpp"),
                           can_submit=can_submit(me), last_code=last_code,
                           info=None if me["is_admin"] else section_info(me["id"], "problems"),
                           guard=setting("guard_problems") == "1" and not me["is_admin"],
                           block_paste=setting("block_paste_problems") == "1" and not me["is_admin"])


@app.route("/api/run/<pid>", methods=["POST"])
@login_required
def api_run(pid):
    """Namunaviy testlarda sinab ko'rish — ball berilmaydi, reytingga ta'sir qilmaydi."""
    me = current_user()
    problem_by_id(pid)
    if not can_submit(me):
        return jsonify({"error": "Masalalar bo'limi faol emas."}), 403
    last = session.get("last_run", 0)
    now = datetime.now().timestamp()
    if now - last < RUN_COOLDOWN and not me["is_admin"]:
        return jsonify({"error": f"Sinashlar orasida {RUN_COOLDOWN} soniya kuting."}), 429
    session["last_run"] = now
    data = request.get_json(silent=True) or {}
    code, lang = data.get("code", ""), data.get("lang")
    if lang not in judge.LANGS or not code.strip() or len(code.encode()) > MAX_CODE:
        return jsonify({"error": "Kod yoki til noto'g'ri."}), 400
    res = judge.run_samples(code, lang, pid)
    return jsonify({"verdict": res["verdict"], "compile_log": res["compile_log"], "details": res["details"]})


@app.route("/submissions")
@login_required
def my_submissions():
    me = current_user()
    rows = get_db().execute("SELECT * FROM submissions WHERE user_id=? ORDER BY id DESC", (me["id"],)).fetchall()
    return render_template("submissions.html", rows=rows, titles={p["id"]: p["title"] for p in problems()},
                           all_users=False)


@app.route("/submission/<int:sid>")
@login_required
def submission(sid):
    me = current_user()
    s = get_db().execute("""SELECT s.*, u.username, u.full_name FROM submissions s
                            JOIN users u ON u.id=s.user_id WHERE s.id=?""", (sid,)).fetchone()
    if not s or (s["user_id"] != me["id"] and not me["is_admin"]):
        abort(404)
    details = json.loads(s["details"]) if s["details"] else []
    return render_template("submission.html", s=s, details=details, p=problem_by_id(s["problem"]))


@app.route("/api/status/<int:sid>")
@login_required
def api_status(sid):
    me = current_user()
    s = get_db().execute("SELECT user_id,status,verdict FROM submissions WHERE id=?", (sid,)).fetchone()
    if not s or (s["user_id"] != me["id"] and not me["is_admin"]):
        abort(404)
    return {"status": s["status"], "verdict": s["verdict"]}


# ---------------- REYTINGLAR ----------------
def fmt_dur(td):
    if td is None:
        return ""
    t = int(td.total_seconds())
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}"


def build_rankings(for_admin=False):
    db = get_db()
    _, c_end = contest_times()
    freeze = isetting("freeze_minutes")
    cutoff = c_end - timedelta(minutes=freeze) if freeze and not for_admin else None
    users = db.execute("SELECT id, username, full_name, group_name FROM users WHERE is_admin=0").fetchall()
    subs = db.execute("SELECT user_id, problem, score, created FROM submissions WHERE status='done' ORDER BY id").fetchall()
    by_user = {}
    for s in subs:
        by_user.setdefault(s["user_id"], []).append(s)
    qmax, pmax = quiz_max(), problems_max()
    wt, wp = isetting("weight_test"), isetting("weight_problems")
    rows = []
    for u in users:
        ti = section_info(u["id"], "test", db)
        pi = section_info(u["id"], "problems", db)
        r = {"u": u, "test": None, "test_time": None, "prob": None, "prob_time": None, "cells": {},
             "violations": violation_count(u["id"], db=db)}
        # Test natijasi faqat bo'lim yakunlangandan keyin ko'rinadi
        if ti["state"] == "done":
            r["test"] = quiz_score(u["id"], db)
            r["test_time"] = ti["end"] - ti["start"]
        if pi["state"] != "none":
            best = {}
            for s in by_user.get(u["id"], []):
                t = datetime.fromisoformat(s["created"])
                if t < pi["start"] or t > pi["end"] or (cutoff and t > cutoff):
                    continue
                if s["problem"] not in best or s["score"] > best[s["problem"]][0]:
                    best[s["problem"]] = (s["score"], t - pi["start"])
            r["cells"] = {p: (v[0], int(v[1].total_seconds() // 60)) for p, v in best.items()}
            r["prob"] = sum(v[0] for v in best.values())
            pos = [v[1] for v in best.values() if v[0] > 0]
            r["prob_time"] = max(pos) if pos else timedelta(0)
        tp = (r["test"] or 0) / qmax if qmax else 0
        pp = (r["prob"] or 0) / pmax if pmax else 0
        r["overall"] = round(tp * wt + pp * wp, 2)
        r["overall_time"] = (r["test_time"] or timedelta(0)) + (r["prob_time"] or timedelta(0))
        rows.append(r)

    def ranked(key_rows, key):
        key_rows = sorted(key_rows, key=key)
        place, prev = 0, None
        out = []
        for i, r in enumerate(key_rows):
            k = key(r)
            if k != prev:
                place = i + 1
            prev = k
            out.append(dict(r, place=place))
        return out

    test_rows = ranked([r for r in rows if r["test"] is not None],
                       lambda r: (-r["test"], r["test_time"]))
    prob_rows = ranked([r for r in rows if r["prob"] is not None],
                       lambda r: (-r["prob"], r["prob_time"]))
    overall_rows = ranked([r for r in rows if r["test"] is not None or r["prob"] is not None],
                          lambda r: (-r["overall"], r["overall_time"]))
    frozen = bool(cutoff and datetime.now() > cutoff)
    return {"test": test_rows, "problems": prob_rows, "overall": overall_rows, "frozen": frozen,
            "qmax": qmax, "pmax": pmax, "wt": wt, "wp": wp}


@app.route("/scoreboard")
def scoreboard():
    me = current_user()
    tab = request.args.get("tab", "overall")
    if tab not in ("overall", "test", "problems"):
        tab = "overall"
    R = build_rankings(for_admin=bool(me and me["is_admin"]))
    return render_template("scoreboard.html", R=R, tab=tab, problems=problems(), fmt_dur=fmt_dur)


# ---------------- ADMIN ----------------
@app.route("/admin", methods=["GET", "POST"])
@admin_required
def admin():
    db = get_db()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "settings":
            try:
                for k in ("start", "end"):
                    datetime.strptime(request.form[k], DT_FMT)
                    db.execute("UPDATE settings SET value=? WHERE key=?", (request.form[k], k))
                for k in ("test_minutes", "problems_minutes", "weight_test", "weight_problems",
                          "freeze_minutes", "max_violations"):
                    db.execute("INSERT OR REPLACE INTO settings VALUES(?,?)",
                               (k, str(max(0, int(request.form.get(k) or 0)))))
                for k in ("registration", "guard_test", "guard_problems", "block_paste_problems"):
                    db.execute("INSERT OR REPLACE INTO settings VALUES(?,?)", (k, "1" if request.form.get(k) else "0"))
                db.commit()
                flash("Sozlamalar saqlandi.", "ok")
            except (ValueError, KeyError):
                flash("Kiritilgan qiymatlar formati noto'g'ri.", "err")
        elif action == "rejudge":
            sid = request.form.get("sid")
            q = "UPDATE submissions SET status='queue' WHERE status='done'" + (" AND id=?" if sid else "")
            db.execute(q, (sid,) if sid else ())
            db.commit()
            flash("Qayta tekshiruvga qo'yildi.", "ok")
        elif action == "reset_pw":
            uid, pw = request.form.get("uid"), request.form.get("new_password", "")
            if len(pw) >= 6:
                db.execute("UPDATE users SET pw_hash=? WHERE id=?", (generate_password_hash(pw), uid))
                db.commit()
                flash("Parol yangilandi.", "ok")
            else:
                flash("Parol kamida 6 belgi.", "err")
        elif action == "extend":
            uid, sec = request.form.get("uid"), request.form.get("section")
            mins = int(request.form.get("minutes") or 0)
            db.execute("UPDATE attempts SET extra_minutes=extra_minutes+?, finished_at=NULL WHERE user_id=? AND section=?",
                       (mins, uid, sec))
            db.commit()
            flash(f"{mins} daqiqa qo'shildi.", "ok")
        elif action == "reset_attempt":
            uid, sec = request.form.get("uid"), request.form.get("section")
            db.execute("DELETE FROM attempts WHERE user_id=? AND section=?", (uid, sec))
            if sec == "test":
                db.execute("DELETE FROM quiz_answers WHERE user_id=?", (uid,))
            db.commit()
            flash("Urinish bekor qilindi — talaba bo'limni qaytadan boshlashi mumkin.", "ok")
        elif action == "delete_user":
            uid = request.form.get("uid")
            for t in ("submissions", "attempts", "quiz_answers", "events"):
                db.execute(f"DELETE FROM {t} WHERE user_id=?", (uid,))
            db.execute("DELETE FROM users WHERE id=? AND is_admin=0", (uid,))
            db.commit()
            flash("Foydalanuvchi o'chirildi.", "ok")
        return redirect(url_for("admin"))
    users = db.execute("""SELECT u.*, (SELECT COUNT(*) FROM submissions s WHERE s.user_id=u.id) n
                          FROM users u WHERE u.is_admin=0 ORDER BY u.group_name, u.full_name""").fetchall()
    urows = []
    for u in users:
        urows.append({"u": u, "test": section_info(u["id"], "test", db),
                      "prob": section_info(u["id"], "problems", db),
                      "vt": violation_count(u["id"], "test", db), "vp": violation_count(u["id"], "problems", db)})
    queue = db.execute("SELECT COUNT(*) c FROM submissions WHERE status!='done'").fetchone()["c"]
    keys = list(DEFAULTS) + ["start", "end"]
    return render_template("admin.html", urows=urows, queue=queue, s={k: setting(k) for k in keys})


@app.route("/admin/events/<int:uid>")
@admin_required
def admin_events(uid):
    db = get_db()
    u = db.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone() or abort(404)
    ev = db.execute("SELECT * FROM events WHERE user_id=? ORDER BY id", (uid,)).fetchall()
    return render_template("admin_events.html", u=u, ev=ev, EVENT_UZ=EVENT_UZ)


@app.route("/admin/submissions")
@admin_required
def admin_submissions():
    rows = get_db().execute("""SELECT s.*, u.username, u.full_name FROM submissions s
                               JOIN users u ON u.id=s.user_id ORDER BY s.id DESC LIMIT 2000""").fetchall()
    return render_template("submissions.html", rows=rows, titles={p["id"]: p["title"] for p in problems()},
                           all_users=True)


def _code_fingerprint(code):
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.S)
    code = re.sub(r"//[^\n]*|#(?!include|define)[^\n]*", "", code)
    return re.sub(r"\s+", "", code)


@app.route("/admin/similar")
@admin_required
def admin_similar():
    """Har bir masala bo'yicha talabalarning eng yaxshi yechimlarini juft-juft solishtiradi."""
    db = get_db()
    threshold = float(request.args.get("t", 0.85))
    rows = db.execute("""SELECT s.id, s.user_id, s.problem, s.score, s.code, u.full_name FROM submissions s
                         JOIN users u ON u.id=s.user_id WHERE s.status='done' AND s.score>0 AND u.is_admin=0
                         ORDER BY s.score DESC, s.id DESC""").fetchall()
    best = {}
    for r in rows:
        best.setdefault((r["problem"], r["user_id"]), r)
    by_prob = {}
    for (pid, _), r in best.items():
        by_prob.setdefault(pid, []).append((r, _code_fingerprint(r["code"])))
    pairs = []
    for pid, lst in by_prob.items():
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)):
                a, b = lst[i][1], lst[j][1]
                sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
                if sm.real_quick_ratio() < threshold or sm.quick_ratio() < threshold:
                    continue
                ratio = sm.ratio()
                if ratio >= threshold:
                    pairs.append((ratio, pid, lst[i][0], lst[j][0]))
    pairs.sort(key=lambda x: -x[0])
    return render_template("admin_similar.html", pairs=pairs, threshold=threshold)


@app.route("/admin/quiz-key")
@admin_required
def admin_quiz_key():
    db = get_db()
    done_users = [r["user_id"] for r in db.execute("SELECT user_id FROM attempts WHERE section='test'")]
    stats = {}
    for uid in done_users:
        ans = user_answers(uid, db)
        for q in quiz():
            stats.setdefault(q["id"], [0, 0])
            stats[q["id"]][1] += 1
            stats[q["id"]][0] += grade_question(q, ans.get(q["id"]))
    return render_template("quiz_key.html", qs=quiz(), stats=stats)


@app.route("/admin/print")
@admin_required
def admin_print():
    return render_template("print.html", problems=problems())


@app.route("/admin/export.csv")
@admin_required
def export_csv():
    R = build_rankings(for_admin=True)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["O'rin", "F.I.Sh.", "Guruh", "Login", f"Test (/{R['qmax']})", "Test vaqti",
                f"Masalalar (/{R['pmax']})"] + [p["id"] for p in problems()] +
               ["Masalalar vaqti", "Umumiy ball (/100)", "Qoidabuzarliklar"])
    for r in R["overall"]:
        w.writerow([r["place"], r["u"]["full_name"], r["u"]["group_name"], r["u"]["username"],
                    "" if r["test"] is None else r["test"], fmt_dur(r["test_time"]),
                    "" if r["prob"] is None else r["prob"]] +
                   [(r["cells"].get(p["id"]) or ("",))[0] for p in problems()] +
                   [fmt_dur(r["prob_time"]), r["overall"], r["violations"]])
    return Response("﻿" + buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=olimpiada_natijalar.csv"})


init_db()
if os.environ.get("JUDGE_IN_PROCESS", "1") == "1":
    judge.start_workers(int(os.environ.get("JUDGE_WORKERS", "2")))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
