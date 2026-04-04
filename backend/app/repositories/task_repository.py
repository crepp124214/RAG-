from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.models import Task


class TaskRepository:
    def __init__(self, db_session: Session) -> None:
        self.db_session = db_session

    def get_by_id(self, task_id: str) -> Task | None:
        return self.db_session.get(Task, task_id)

    def add(self, task: Task) -> Task:
        self.db_session.add(task)
        self.db_session.flush()
        return task
