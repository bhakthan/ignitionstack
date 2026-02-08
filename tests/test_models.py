"""Tests for core data models."""

from pathlib import Path

from ignition.models import (
    PRD,
    InputType,
    Task,
    TaskCategory,
    TaskStatus,
    detect_input_type,
)


class TestInputType:
    def test_detect_text(self, tmp_path: Path):
        f = tmp_path / "use-case.txt"
        f.write_text("hello")
        assert detect_input_type(f) == InputType.TEXT

    def test_detect_pdf(self, tmp_path: Path):
        f = tmp_path / "doc.pdf"
        f.write_bytes(b"%PDF")
        assert detect_input_type(f) == InputType.PDF

    def test_detect_pptx(self, tmp_path: Path):
        f = tmp_path / "deck.pptx"
        f.write_bytes(b"PK")
        assert detect_input_type(f) == InputType.PPTX

    def test_detect_docx(self, tmp_path: Path):
        f = tmp_path / "doc.docx"
        f.write_bytes(b"PK")
        assert detect_input_type(f) == InputType.DOCX

    def test_detect_image(self, tmp_path: Path):
        f = tmp_path / "screenshot.png"
        f.write_bytes(b"\x89PNG")
        assert detect_input_type(f) == InputType.IMAGE

    def test_detect_unknown_defaults_text(self, tmp_path: Path):
        f = tmp_path / "data.xyz"
        f.write_text("unknown")
        assert detect_input_type(f) == InputType.TEXT


class TestTask:
    def test_passes_tbic_default(self):
        t = Task(
            id=1,
            title="Test task",
            category=TaskCategory.BACKEND,
            description="A task",
        )
        assert t.passes_tbic is True

    def test_fails_tbic_when_not_bounded(self):
        t = Task(
            id=1,
            title="Big task",
            category=TaskCategory.BACKEND,
            description="Too big",
            bounded=False,
        )
        assert t.passes_tbic is False


class TestPRD:
    def test_next_task_no_deps(self, sample_tasks):
        prd = PRD(
            project_name="test",
            description="test",
            tasks=sample_tasks,
        )
        # Task 1 and 3 have no deps — next should be task 1
        assert prd.next_task is not None
        assert prd.next_task.id == 1

    def test_next_task_after_completion(self, sample_tasks):
        sample_tasks[0].status = TaskStatus.DONE  # task 1 done
        sample_tasks[2].status = TaskStatus.DONE  # task 3 done
        prd = PRD(project_name="test", description="test", tasks=sample_tasks)
        # task 2 depends on 1 (done) — should be next
        assert prd.next_task is not None
        assert prd.next_task.id == 2

    def test_progress_pct(self, sample_tasks):
        sample_tasks[0].status = TaskStatus.DONE
        prd = PRD(project_name="test", description="test", tasks=sample_tasks)
        assert prd.progress_pct == 20.0

    def test_progress_pct_empty(self):
        prd = PRD(project_name="test", description="test", tasks=[])
        assert prd.progress_pct == 0.0

    def test_pending_tasks(self, sample_tasks):
        sample_tasks[0].status = TaskStatus.DONE
        prd = PRD(project_name="test", description="test", tasks=sample_tasks)
        assert len(prd.pending_tasks) == 4
