"""Tests for Universal Agnostic Curriculum and Arbitrary Phase Allocation."""

import pytest
from scripts.multi_agent.architect_agent import ArchitectAgent
from scripts.multi_agent.writer_agent import WriterAgent
from scripts.multi_agent.reviewer_agent import ReviewerAgent


@pytest.mark.parametrize("phases", [4, 6, 8, 12])
def test_universal_architect_unconstrained_phases(phases):
    architect = ArchitectAgent(topic="Distributed Systems")
    syllabus = architect.plan_universal_curriculum({"num_phases": phases})
    assert len(syllabus.phases) == phases, f"Expected {phases} phases, got {len(syllabus.phases)}"
    assert syllabus.topic == "Distributed Systems"


def test_english_curriculum_specialization():
    architect = ArchitectAgent(topic="English Fluency & Spoken Communication")
    syllabus = architect.plan_universal_curriculum({"num_phases": 6})
    assert len(syllabus.phases) == 6
    assert any("phonetics" in p.title.lower() or "cadence" in p.title.lower() or "foundations" in p.title.lower() for p in syllabus.phases)


def test_universal_writer_synthesis_and_reviewer_audit():
    architect = ArchitectAgent(topic="Compiler Engineering")
    syllabus = architect.plan_universal_curriculum({"num_phases": 4})
    writer = WriterAgent(topic="Compiler Engineering")
    md = writer.assemble_full_manual(syllabus)

    reviewer = ReviewerAgent()
    ok, issues = reviewer.audit_markdown_source(md, topic="Compiler Engineering", expected_phases=4)
    assert ok, f"Markdown audit failed: {issues}"
    assert len(issues) == 0
