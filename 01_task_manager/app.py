"""
Flask Task Manager
==================
Run:
    pip install flask
    python app.py
Then open: http://127.0.0.1:5000
"""

from flask import Flask, render_template, request, redirect, url_for
import json
import os
from datetime import datetime

app = Flask(__name__)
TASKS_FILE = "tasks.json"


# ── Storage helpers ───────────────────────────────────────────────

def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_tasks(tasks):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2)

def next_id(tasks):
    return max((t["id"] for t in tasks), default=0) + 1


# ── Routes ────────────────────────────────────────────────────────

@app.route("/")
def index():
    tasks    = load_tasks()
    priority = request.args.get("priority", "all")
    status   = request.args.get("status", "all")

    filtered = tasks
    if priority != "all":
        filtered = [t for t in filtered if t["priority"] == priority]
    if status == "pending":
        filtered = [t for t in filtered if not t["done"]]
    elif status == "done":
        filtered = [t for t in filtered if t["done"]]

    # sort: high first, done last
    order = {"high": 0, "medium": 1, "low": 2}
    filtered.sort(key=lambda t: (t["done"], order.get(t["priority"], 1)))

    total     = len(tasks)
    done_count = sum(1 for t in tasks if t["done"])
    from datetime import date
    return render_template("index.html",
                           tasks=filtered,
                           total=total,
                           done_count=done_count,
                           priority=priority,
                           status=status,
                           today=str(date.today()))


@app.route("/add", methods=["POST"])
def add():
    title    = request.form.get("title", "").strip()
    priority = request.form.get("priority", "medium")
    due_date = request.form.get("due_date", "").strip() or None
    if title:
        tasks = load_tasks()
        tasks.append({
            "id":         next_id(tasks),
            "title":      title,
            "done":       False,
            "priority":   priority,
            "due_date":   due_date,
            "created_at": datetime.now().isoformat(),
        })
        save_tasks(tasks)
    return redirect(url_for("index"))


@app.route("/done/<int:task_id>")
def mark_done(task_id):
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t["done"] = True
            break
    save_tasks(tasks)
    return redirect(url_for("index"))


@app.route("/delete/<int:task_id>")
def delete(task_id):
    tasks = load_tasks()
    tasks = [t for t in tasks if t["id"] != task_id]
    save_tasks(tasks)
    return redirect(url_for("index"))


@app.route("/clear-done")
def clear_done():
    tasks = load_tasks()
    tasks = [t for t in tasks if not t["done"]]
    save_tasks(tasks)
    return redirect(url_for("index"))


# ── Run ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)
