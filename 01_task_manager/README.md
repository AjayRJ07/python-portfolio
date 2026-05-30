# CLI Task Manager

A command-line task manager built with Python — demonstrating OOP, File I/O, argparse, enums, and dataclasses.

---

## Features

- Add tasks with **due dates** and **priority levels** (high / medium / low)
- List tasks sorted by priority and due date
- Filter by priority or show only pending tasks
- Mark tasks as done
- Delete individual tasks or bulk-clear completed ones
- Persistent JSON storage — tasks survive between sessions

---

## Setup

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/python-portfolio.git
cd python-portfolio/01_task_manager

# (Optional) create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Usage

```bash
# Add tasks
python task_manager.py add "Submit report" --due 2025-06-15 --priority high
python task_manager.py add "Buy groceries" --priority medium
python task_manager.py add "Read a book"   --priority low

# List all tasks
python task_manager.py list

# List only high-priority pending tasks
python task_manager.py list --priority high --pending

# Mark task #1 as done
python task_manager.py done 1

# Delete task #3
python task_manager.py delete 3

# Remove all completed tasks
python task_manager.py clear-done

# Use a custom file
python task_manager.py --file work_tasks.json list
```

### Sample output

```
Tasks  (1/3 done, 1 overdue)

  ✓  #1    [HIGH]  [DONE] Submit report
  ○  #3    [HIGH]  Buy groceries  due 2025-06-15
  ○  #2    [LOW]   Read a book
```

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Project Structure

```
01_task_manager/
├── task_manager.py      # Main app
├── requirements.txt
├── .gitignore
├── README.md
└── tests/
    └── test_task_manager.py
```

---

## Concepts Covered

| Concept | Where |
|---|---|
| OOP — classes & dataclasses | `Task`, `TaskStore` |
| Enums | `Priority` |
| File I/O — JSON read/write | `TaskStore._load()`, `._save()` |
| argparse subcommands | `build_parser()` |
| Properties & computed attributes | `Task.is_overdue` |
| Sorting & filtering | `TaskStore.filter()` |
| Unit testing with pytest | `tests/` |

---

## Tech Stack

Python 3.11+ · argparse · dataclasses · json · pytest
