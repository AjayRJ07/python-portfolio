import pytest
import json
from datetime import date, timedelta
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from task_manager import Task, TaskStore, Priority


# ── Fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def store(tmp_path):
    """Fresh TaskStore backed by a temp file."""
    return TaskStore(filepath=str(tmp_path / "tasks.json"))


@pytest.fixture
def populated_store(store):
    """TaskStore with a few tasks pre-loaded."""
    store.add("Buy groceries",   priority="high",   due_date=None)
    store.add("Read a book",     priority="low",    due_date=None)
    store.add("Submit report",   priority="high",   due_date=str(date.today() + timedelta(days=3)))
    return store


# ── Task Model ────────────────────────────────────────────────────

class TestTask:
    def test_default_priority_is_medium(self):
        t = Task(id=1, title="Test")
        assert t.priority == "medium"

    def test_is_overdue_past_due(self):
        yesterday = str(date.today() - timedelta(days=1))
        t = Task(id=1, title="Old task", due_date=yesterday)
        assert t.is_overdue is True

    def test_is_overdue_future_due(self):
        tomorrow = str(date.today() + timedelta(days=1))
        t = Task(id=1, title="Future task", due_date=tomorrow)
        assert t.is_overdue is False

    def test_is_overdue_done_task_not_overdue(self):
        yesterday = str(date.today() - timedelta(days=1))
        t = Task(id=1, title="Done task", done=True, due_date=yesterday)
        assert t.is_overdue is False

    def test_to_dict_and_from_dict_roundtrip(self):
        t = Task(id=1, title="Round trip", priority="high", due_date="2025-12-01")
        assert Task.from_dict(t.to_dict()) == t

    def test_display_shows_done_marker(self):
        t = Task(id=1, title="Done task", done=True)
        assert "✓" in t.display()
        assert "[DONE]" in t.display()

    def test_display_shows_overdue(self):
        yesterday = str(date.today() - timedelta(days=1))
        t = Task(id=1, title="Late", due_date=yesterday)
        assert "OVERDUE" in t.display()


# ── TaskStore CRUD ────────────────────────────────────────────────

class TestTaskStore:
    def test_add_task_increments_id(self, store):
        t1 = store.add("First",  priority="medium", due_date=None)
        t2 = store.add("Second", priority="medium", due_date=None)
        assert t1.id == 1
        assert t2.id == 2

    def test_add_persists_to_disk(self, tmp_path):
        path = str(tmp_path / "tasks.json")
        s1 = TaskStore(filepath=path)
        s1.add("Persist me", priority="low", due_date=None)
        s2 = TaskStore(filepath=path)
        assert len(s2.tasks) == 1
        assert s2.tasks[0].title == "Persist me"

    def test_get_returns_correct_task(self, populated_store):
        t = populated_store.get(2)
        assert t is not None
        assert t.title == "Read a book"

    def test_get_returns_none_for_missing_id(self, store):
        assert store.get(999) is None

    def test_mark_done(self, populated_store):
        task = populated_store.mark_done(1)
        assert task.done is True
        # Verify persisted
        reloaded = TaskStore(filepath=populated_store.filepath)
        assert reloaded.get(1).done is True

    def test_mark_done_missing_id_returns_none(self, store):
        assert store.mark_done(999) is None

    def test_delete_removes_task(self, populated_store):
        populated_store.delete(1)
        assert populated_store.get(1) is None
        assert len(populated_store.tasks) == 2

    def test_delete_missing_id_returns_none(self, store):
        assert store.delete(999) is None

    def test_clear_done_removes_only_done(self, populated_store):
        populated_store.mark_done(1)
        populated_store.mark_done(2)
        removed = populated_store.clear_done()
        assert removed == 2
        assert len(populated_store.tasks) == 1
        assert populated_store.tasks[0].title == "Submit report"


# ── Filter & Sort ────────────────────────────────────────────────

class TestFilter:
    def test_filter_by_priority(self, populated_store):
        high_tasks = populated_store.filter(priority="high")
        assert all(t.priority == "high" for t in high_tasks)
        assert len(high_tasks) == 2

    def test_filter_pending_excludes_done(self, populated_store):
        populated_store.mark_done(1)
        pending = populated_store.filter(show_done=False)
        assert all(not t.done for t in pending)

    def test_sort_puts_high_priority_first(self, populated_store):
        tasks = populated_store.filter(show_done=False)
        priorities = [t.priority for t in tasks if not t.done]
        high_indices = [i for i, p in enumerate(priorities) if p == "high"]
        low_indices  = [i for i, p in enumerate(priorities) if p == "low"]
        if high_indices and low_indices:
            assert min(high_indices) < max(low_indices)

    def test_done_tasks_sorted_last(self, populated_store):
        populated_store.mark_done(1)
        tasks = populated_store.filter()
        done_indices = [i for i, t in enumerate(tasks) if t.done]
        pending_indices = [i for i, t in enumerate(tasks) if not t.done]
        if done_indices and pending_indices:
            assert min(done_indices) > max(pending_indices)
