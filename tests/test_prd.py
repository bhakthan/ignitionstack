"""Tests for PRD generation and persistence."""


from ignition.stages.prd import generate_prd, init_progress, load_prd, save_prd


class TestPRDGeneration:
    def test_generate_prd(self, sample_requirements, sample_tasks, sample_config):
        prd = generate_prd("test-proj", sample_requirements, sample_tasks, sample_config)
        assert prd.project_name == "test-proj"
        assert prd.domain == "healthcare"
        assert len(prd.tasks) == 5

    def test_save_and_load_prd(self, sample_prd, tmp_work_dir):
        path = save_prd(sample_prd, tmp_work_dir)
        assert path.exists()
        assert path.name == "PRD.json"

        loaded = load_prd(tmp_work_dir)
        assert loaded.project_name == sample_prd.project_name
        assert len(loaded.tasks) == len(sample_prd.tasks)

    def test_init_progress(self, sample_prd, tmp_work_dir):
        path = init_progress(tmp_work_dir, sample_prd)
        assert path.exists()
        content = path.read_text()
        assert "meridian-portal" in content
        assert "Iteration Log" in content
