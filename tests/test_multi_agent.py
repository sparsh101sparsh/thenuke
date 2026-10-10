"""Unit and integration tests for thenuke multi-agent authoring system."""

from pathlib import Path
import pytest

from scripts.multi_agent.architect_agent import ArchitectAgent
from scripts.multi_agent.research_agent import ResearchAgent
from scripts.multi_agent.diagram_agent import DiagramAgent
from scripts.multi_agent.writer_agent import WriterAgent
from scripts.multi_agent.reviewer_agent import ReviewerAgent
from scripts.multi_agent.agent_orchestrator import MultiAgentOrchestrator
from scripts.diagramming.vector_diagrams import DIAGRAM_REGISTRY


def test_architect_agent_curriculum():
    architect = ArchitectAgent(topic="Git")
    syllabus = architect.plan_curriculum({"level_of_detail": "senior_architect"})
    assert syllabus.topic == "Git"
    assert len(syllabus.phases) == 9
    assert len(syllabus.diagram_slots) == 9
    assert len(syllabus.appendices) == 3


def test_research_agent_briefings():
    researcher = ResearchAgent(topic="Git")
    briefing = researcher.get_briefing(phase_num=1, chapter_num="1.4")
    assert briefing.chapter_num == "1.4"
    assert briefing.diagram_spec == "object_model"
    assert len(briefing.systems_primitives) > 0
    assert len(briefing.c_structs_or_specs) > 0


def test_diagram_agent_validation():
    diagrammer = DiagramAgent()
    assert len(diagrammer.available_diagrams) == 9
    for name in DIAGRAM_REGISTRY.keys():
        valid, err = diagrammer.validate_diagram(name)
        assert valid is True, f"Diagram '{name}' failed validation: {err}"


def test_reviewer_agent_markdown_audit():
    reviewer = ReviewerAgent()
    clean_sample = (
        "# Sample Document\n"
        "[DIAGRAM: object_model]\n"
        "[DIAGRAM: index_binary]\n"
        "[DIAGRAM: three_trees]\n"
        "[DIAGRAM: branching_dag]\n"
        "[DIAGRAM: three_way_merge]\n"
        "[DIAGRAM: merge_conflict]\n"
        "[DIAGRAM: rebase_replay]\n"
        "[DIAGRAM: reset_matrix]\n"
        "[DIAGRAM: remote_sync]\n"
        + "\n".join(f"CHALLENGE {i}" for i in range(1, 28))
    )
    ok, issues = reviewer.audit_markdown_source(clean_sample)
    assert ok is True, f"Clean sample failed audit: {issues}"

    # Devanagari failure test
    devanagari_sample = clean_sample + "\nनमस्ते दुनिया"
    ok, issues = reviewer.audit_markdown_source(devanagari_sample)
    assert ok is False
    assert any("Pass 2 Failed" in iss for iss in issues)


def test_multi_agent_orchestrator_end_to_end(tmp_path):
    target_pdf = tmp_path / "multi_agent_test.pdf"
    orchestrator = MultiAgentOrchestrator(topic="Git")
    compiled_path, report = orchestrator.run_multi_agent_pipeline(target_pdf)

    assert compiled_path.exists()
    assert report.passed is True
    assert report.pass_1_layout_clean is True
    assert report.pass_2_zero_devanagari is True
    assert report.pass_3_diagram_density is True
    assert report.pass_4_drills_complete is True
    assert report.total_pages >= 60
