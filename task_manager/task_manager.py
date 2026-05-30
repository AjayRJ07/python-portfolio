import argparse
import json
import os
import sys
from datetime import datetime, date
from enum import Enum
from dataclasses import dataclass, field, asdict


# ── Enums ─────────────────────────────────────────────────────────

class Priority(str, Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"

PRIORITY_ORDER = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
PRIORITY_LABEL = {Priority.HIGH: "[HIGH]", Priority.MEDIUM: "[MED] ", Priority.LOW: "[LOW] "}


# ── Data Model ────────────────────────────────────────────────────

@dataclass
class Task:
    id:         int
    title:      str
    done:       bool          = False
    priority:   str           = Priority.MEDIUM.value
    due_date:   str | None    = None          # ISO format: YYYY-MM-DD
    created_at: str           = field(default_factory=lambda: datetime.now().isoformat())

    # ── Convenience properties ──

    @property
    def priority_enum(self) -> Priority:
        return Priority(self.priority)

    @property
    def due_date_obj(self) -> date | None:
        return date.fromisoformat(self.due_date) if self.due_date else None

    @property
    def is_overdue(self) -> bool:
        return bool(self.due_date_obj and not self.done and self.due_date_obj < date.today())

    # ── Serialisation ──

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(**data)

    # ── Display ──

    def display(self) -> str:
        status   = "✓" if self.done else "○"
        priority = PRIORITY_LABEL[self.priority_enum]
        due_str  = ""
        if self.due_date:
            tag = " !! OVERDUE" if self.is_overdue else ""
            due_str = f"  due {self.due_date}{tag}"
        title = f"[DONE] {self.title}" if self.done else self.title
        return f"  {status}  #{self.id:<4} {priority}  {title}{due_str}"


# ── Storage ───────────────────────────────────────────────────────

class TaskStore:
    def __init__(self, filepath: str = "tasks.json"):
        self.filepath = filepath
        self.tasks: list[Task] = self._load()

    def _load(self) -> list[Task]:
        if not os.path.exists(self.filepath):
            return []
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return [Task.from_dict(d) for d in json.load(f)]
        except (json.JSONDecodeError, KeyError) as e:
            sys.exit(f"Error reading {self.filepath}: {e}")

    def _save(self) -> None:
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump([t.to_dict() for t in self.tasks], f, indent=2)

    def _next_id(self) -> int:
        return max((t.id for t in self.tasks), default=0) + 1

    # ── CRUD ──

    def add(self, title: str, priority: str, due_date: str | None) -> Task:
        task = Task(
            id=self._next_id(),
            title=title,
            priority=priority,
            due_date=due_date,
        )
        self.tasks.append(task)
        self._save()
        return task

    def get(self, task_id: int) -> Task | None:
        return next((t for t in self.tasks if t.id == task_id), None)

    def mark_done(self, task_id: int) -> Task | None:
        task = self.get(task_id)
        if task:
            task.done = True
            self._save()
        return task

    def delete(self, task_id: int) -> Task | None:
        task = self.get(task_id)
        if task:
            self.tasks = [t for t in self.tasks if t.id != task_id]
            self._save()
        return task

    def clear_done(self) -> int:
        before = len(self.tasks)
        self.tasks = [t for t in self.tasks if not t.done]
        self._save()
        return before - len(self.tasks)

    def filter(
        self,
        priority: str | None = None,
        show_done: bool = True,
    ) -> list[Task]:
        tasks = self.tasks
        if not show_done:
            tasks = [t for t in tasks if not t.done]
        if priority:
            tasks = [t for t in tasks if t.priority == priority]
        return sorted(tasks, key=lambda t: (
            t.done,
            PRIORITY_ORDER[t.priority_enum],
            t.due_date or "9999",
        ))


# ── CLI Commands ──────────────────────────────────────────────────

def cmd_add(store: TaskStore, args: argparse.Namespace) -> None:
    # Validate due date format
    if args.due:
        try:
            date.fromisoformat(args.due)
        except ValueError:
            sys.exit("Invalid date format. Use YYYY-MM-DD (e.g. 2025-06-10)")

    task = store.add(
        title=args.title,
        priority=args.priority,
        due_date=args.due,
    )
    print(f"Added task #{task.id}:")
    print(task.display())


def cmd_list(store: TaskStore, args: argparse.Namespace) -> None:
    tasks = store.filter(
        priority=args.priority,
        show_done=not args.pending,
    )
    if not tasks:
        print("No tasks found.")
        return

    total    = len(store.tasks)
    done_cnt = sum(1 for t in store.tasks if t.done)
    overdue  = sum(1 for t in tasks if t.is_overdue)

    print(f"\nTasks  ({done_cnt}/{total} done{f', {overdue} overdue' if overdue else ''})\n")
    for task in tasks:
        print(task.display())
    print()


def cmd_done(store: TaskStore, args: argparse.Namespace) -> None:
    task = store.mark_done(args.id)
    if task:
        print(f"Marked done:")
        print(task.display())
    else:
        print(f"No task with id #{args.id}")


def cmd_delete(store: TaskStore, args: argparse.Namespace) -> None:
    task = store.delete(args.id)
    if task:
        print(f"Deleted task #{task.id}: {task.title}")
    else:
        print(f"No task with id #{args.id}")


def cmd_clear_done(store: TaskStore, args: argparse.Namespace) -> None:
    removed = store.clear_done()
    print(f"Removed {removed} completed task(s).")


# ── Argument Parser ───────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="task_manager",
        description="CLI Task Manager — manage tasks from the terminal.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python task_manager.py add "Submit report" --due 2025-06-15 --priority high
  python task_manager.py list
  python task_manager.py list --priority high --pending
  python task_manager.py done 3
  python task_manager.py delete 5
  python task_manager.py clear-done
        """,
    )
    parser.add_argument(
        "--file", default="tasks.json",
        help="Path to the tasks JSON file (default: tasks.json)",
    )

    sub = parser.add_subparsers(dest="command", metavar="command")
    sub.required = True

    # add
    p_add = sub.add_parser("add", help="Add a new task")
    p_add.add_argument("title", help="Task description")
    p_add.add_argument("--due", metavar="YYYY-MM-DD", help="Due date")
    p_add.add_argument(
        "--priority", choices=[p.value for p in Priority],
        default=Priority.MEDIUM.value, help="Priority level (default: medium)",
    )

    # list
    p_list = sub.add_parser("list", help="List tasks")
    p_list.add_argument(
        "--priority", choices=[p.value for p in Priority],
        help="Filter by priority",
    )
    p_list.add_argument(
        "--pending", action="store_true",
        help="Show only pending (not done) tasks",
    )

    # done
    p_done = sub.add_parser("done", help="Mark a task as done")
    p_done.add_argument("id", type=int, help="Task ID")

    # delete
    p_del = sub.add_parser("delete", help="Delete a task")
    p_del.add_argument("id", type=int, help="Task ID")

    # clear-done
    sub.add_parser("clear-done", help="Remove all completed tasks")

    return parser


# ── Entry Point ───────────────────────────────────────────────────

COMMANDS = {
    "add":        cmd_add,
    "list":       cmd_list,
    "done":       cmd_done,
    "delete":     cmd_delete,
    "clear-done": cmd_clear_done,
}

def main() -> None:
    parser = build_parser()
    args   = parser.parse_args()
    store  = TaskStore(filepath=args.file)
    COMMANDS[args.command](store, args)


if __name__ == "__main__":
    main()
