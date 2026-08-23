import json
import os
from datetime import datetime
from html import escape
import streamlit as st

# 할일 데이터 파일 경로 (앱 폴더에 저장)
TODO_FILE = "todos.json"


def load_todos():
    """Load todos from JSON file. Returns a list."""
    try:
        if os.path.exists(TODO_FILE):
            with open(TODO_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except (json.JSONDecodeError, IOError):
        return []


def save_todos(todos):
    """Save todos list to JSON file."""
    try:
        with open(TODO_FILE, 'w', encoding='utf-8') as f:
            json.dump(todos, f, ensure_ascii=False, indent=2)
        return True
    except IOError:
        return False


def get_next_id(todos):
    if not todos:
        return 1
    return max(todo['id'] for todo in todos) + 1


def get_priority_emoji(priority):
    emojis = {1: "🔴", 2: "🟠", 3: "🟡", 4: "🟢", 5: "🔵"}
    return emojis.get(priority, "⚪")


def format_date(date_str):
    if not date_str:
        return ""
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M')
    except Exception:
        return date_str


def todo_table_row(todo):
    """Return the display values used by one to-do table row."""
    return {
        '완료': todo.get('done', False),
        '할 일': todo.get('text', ''),
        '생성일': format_date(todo.get('created_at')),
        '완료일': format_date(todo.get('done_at')) if todo.get('done_at') else '-',
    }


def sort_todos(todos):
    """Sort incomplete tasks first, then priority and due date."""
    return sorted(
        todos,
        key=lambda todo: (
            todo.get('done', False),
            -int(todo.get('priority', 3)),
            todo.get('due') or '9999-12-31',
        ),
    )


def todo_text_html(todo):
    """Return safe task text, highlighted when the task is complete."""
    text = escape(str(todo.get('text', '')))
    if todo.get('done', False):
        return f'<span style="color: #39FF14; text-decoration: line-through;">{text}</span>'
    return text


def add_todo_cli_style(todos, text, due, priority):
    new_todo = {
        'id': get_next_id(todos),
        'text': text,
        'created_at': datetime.now().isoformat(),
        'due': due if due else None,
        'priority': priority,
        'done': False,
        'done_at': None,
    }
    todos.append(new_todo)
    saved = save_todos(todos)
    return saved


def add_basic_todo(todos, text):
    """Add a to-do from the minimal input form."""
    return add_todo_cli_style(todos, text, due=None, priority=3)


def mark_complete(todos, todo_id):
    return toggle_todo_completion(todos, todo_id, True)


def toggle_todo_completion(todos, todo_id, is_done):
    """Update a to-do item's completion state and persist the change."""
    for todo in todos:
        if todo['id'] == todo_id:
            if todo.get('done', False) == is_done:
                return False
            todo['done'] = is_done
            todo['done_at'] = datetime.now().isoformat() if is_done else None
            return save_todos(todos)
    return False


def delete_todo_by_id(todos, todo_id):
    for i, todo in enumerate(todos):
        if todo['id'] == todo_id:
            todos.pop(i)
            return save_todos(todos)
    return False


def clear_done_todos_action(todos):
    remaining = [t for t in todos if not t.get('done')]
    if len(remaining) == len(todos):
        return False
    saved = save_todos(remaining)
    if saved:
        todos.clear()
        todos.extend(remaining)
    return saved


def main():
    st.set_page_config(page_title="To-Do Manager", layout="wide")
    st.title("📋 To-Do Manager (Streamlit)")

    # Load todos once into session state
    if 'todos' not in st.session_state:
        st.session_state.todos = load_todos()

    todos = st.session_state.todos

    # Left column: add / actions
    left, right = st.columns([1, 2])

    with left:
        st.header("➕ Add To-Do")
        with st.form(key='add_form', clear_on_submit=True):
            input_col, button_col = st.columns([4, 1])
            text = input_col.text_input('할일 내용을 입력하세요', label_visibility='collapsed', placeholder='할 일을 입력하세요')
            submitted = button_col.form_submit_button('추가', use_container_width=True)

            if submitted:
                if not text.strip():
                    st.error('할일 내용을 입력해야 합니다.')
                else:
                    if add_basic_todo(todos, text.strip()):
                        st.success('할일이 추가되었습니다.')
                    else:
                        st.error('할일 저장에 실패했습니다.')

        st.markdown('---')
        st.header('Actions')
        if st.button('완료된 항목 모두 삭제'):
            if clear_done_todos_action(todos):
                st.success('완료된 항목이 모두 삭제되었습니다.')
            else:
                st.info('삭제할 완료된 항목이 없습니다.')

        if st.button('새로고침'):
            st.session_state.todos = load_todos()
            st.rerun()

    # Right column: list and manage
    with right:
        st.header('📝 To-Do List')

        filter_option = st.radio('Filter', options=['전체', '미완료', '완료'], index=0, horizontal=True)

        if filter_option == '전체':
            filtered = todos
        elif filter_option == '미완료':
            filtered = [t for t in todos if not t.get('done')]
        else:
            filtered = [t for t in todos if t.get('done')]

        filtered = sort_todos(filtered)

        st.write(f'총 {len(filtered)}개')

        headers = st.columns([0.1, 0.38, 0.2, 0.2, 0.12])
        for column, label in zip(headers, ['완료', '할 일', '생성일', '완료일', '삭제']):
            column.markdown(f'**{label}**')
        st.divider()

        for todo in filtered:
            row = todo_table_row(todo)
            cols = st.columns([0.1, 0.38, 0.2, 0.2, 0.12])
            done_cb = cols[0].checkbox('', value=todo.get('done', False), key=f'done-{todo["id"]}')

            if done_cb != todo.get('done', False):
                if toggle_todo_completion(todos, todo['id'], done_cb):
                    st.session_state.todos = todos
                    st.rerun()
                st.error('할일 상태를 저장하지 못했습니다.')

            cols[1].markdown(todo_text_html(todo), unsafe_allow_html=True)
            cols[2].write(row['생성일'])
            cols[3].write(row['완료일'])

            if cols[4].button('삭제', key=f'delete-{todo["id"]}'):
                if delete_todo_by_id(todos, todo['id']):
                    st.session_state.todos = todos
                    st.success('할일이 삭제되었습니다.')
                    st.rerun()
                else:
                    st.error('삭제에 실패했습니다.')

            st.divider()

        st.markdown('---')
        st.caption('우선순위: 1(🔴) - 5(🔵)')


if __name__ == '__main__':
    main()
