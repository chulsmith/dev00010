import importlib.util
import sys
import tempfile
import types
import unittest
from datetime import datetime
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("04.todo_manager_web.py")
SPEC = importlib.util.spec_from_file_location("todo_manager_web", MODULE_PATH)
todo_manager = importlib.util.module_from_spec(SPEC)
# UI rendering is not exercised by these domain-logic tests.
sys.modules.setdefault("streamlit", types.ModuleType("streamlit"))
SPEC.loader.exec_module(todo_manager)


class ToggleTodoCompletionTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_todo_file = todo_manager.TODO_FILE
        todo_manager.TODO_FILE = str(Path(self.temp_dir.name) / "todos.json")

    def tearDown(self):
        todo_manager.TODO_FILE = self.original_todo_file
        self.temp_dir.cleanup()

    def test_toggle_todo_completion_marks_an_incomplete_item_done(self):
        """Catches a missing state update when the list checkbox is checked."""
        todos = [{"id": 1, "done": False, "done_at": None}]

        changed = todo_manager.toggle_todo_completion(todos, 1, True)

        self.assertTrue(changed)
        self.assertTrue(todos[0]["done"])
        self.assertIsNotNone(todos[0]["done_at"])
        datetime.fromisoformat(todos[0]["done_at"])

    def test_toggle_todo_completion_can_restore_an_item_to_incomplete(self):
        """Catches a checkbox that cannot reflect an unchecked item."""
        todos = [{"id": 1, "done": True, "done_at": "2026-08-23T10:00:00"}]

        changed = todo_manager.toggle_todo_completion(todos, 1, False)

        self.assertTrue(changed)
        self.assertFalse(todos[0]["done"])
        self.assertIsNone(todos[0]["done_at"])


class BasicTodoCreationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_todo_file = todo_manager.TODO_FILE
        todo_manager.TODO_FILE = str(Path(self.temp_dir.name) / "todos.json")

    def tearDown(self):
        todo_manager.TODO_FILE = self.original_todo_file
        self.temp_dir.cleanup()

    def test_add_basic_todo_uses_default_priority_and_no_due_date(self):
        """Catches a simple add form that creates incomplete task data incorrectly."""
        todos = []

        saved = todo_manager.add_basic_todo(todos, "Streamlit 공부하기")

        self.assertTrue(saved)
        self.assertEqual(todos[0]["text"], "Streamlit 공부하기")
        self.assertEqual(todos[0]["priority"], 3)
        self.assertIsNone(todos[0]["due"])
        self.assertFalse(todos[0]["done"])


class TodoTableRowTests(unittest.TestCase):
    def test_todo_table_row_includes_completion_and_dates(self):
        """Catches a table that omits status or displays the wrong task metadata."""
        todo = {
            "id": 1,
            "text": "발표 자료 만들기",
            "created_at": "2026-08-23T09:30:00",
            "done": True,
            "done_at": "2026-08-23T11:00:00",
        }

        row = todo_manager.todo_table_row(todo)

        self.assertEqual(
            row,
            {
                "완료": True,
                "할 일": "발표 자료 만들기",
                "생성일": "2026-08-23 09:30",
                "완료일": "2026-08-23 11:00",
            },
        )


class TodoPresentationTests(unittest.TestCase):
    def test_sort_todos_places_completed_items_after_incomplete_items(self):
        """Catches completed tasks appearing before an incomplete task."""
        todos = [
            {"id": 1, "done": True, "priority": 3, "due": None},
            {"id": 2, "done": False, "priority": 3, "due": None},
            {"id": 3, "done": True, "priority": 3, "due": None},
        ]

        sorted_todos = todo_manager.sort_todos(todos)

        self.assertEqual([todo["id"] for todo in sorted_todos], [2, 1, 3])

    def test_completed_todo_text_uses_neon_lime_and_strikethrough(self):
        """Catches completed rows that no longer visibly stand out."""
        html = todo_manager.todo_text_html({"text": "운동하기", "done": True})

        self.assertEqual(
            html,
            '<span style="color: #39FF14; text-decoration: line-through;">운동하기</span>',
        )


if __name__ == "__main__":
    unittest.main()

