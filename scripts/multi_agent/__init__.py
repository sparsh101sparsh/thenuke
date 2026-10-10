"""Multi-Agent Authoring & Adversarial Review Subsystem for thenuke.

Coordinates specialized autonomous agents:
- ArchitectAgent: Syllabus structural design & contract specification
- ResearchAgent: Deep technical systems & POSIX internals research
- WriterAgent: Senior Staff Engineer Hinglish authoring (0% Devanagari)
- DiagramAgent: Publication-grade vector diagram generator & validator
- ReviewerAgent: Adversarial auditor enforcing 4-Pass QA gates
- MultiAgentOrchestrator: Autonomous collaborative pipeline manager
"""

from scripts.multi_agent.architect_agent import ArchitectAgent, SyllabusContract
from scripts.multi_agent.research_agent import ResearchAgent, ResearchBriefing
from scripts.multi_agent.writer_agent import WriterAgent, ChapterDraft
from scripts.multi_agent.diagram_agent import DiagramAgent
from scripts.multi_agent.reviewer_agent import ReviewerAgent, AuditReport
from scripts.multi_agent.agent_orchestrator import MultiAgentOrchestrator

__all__ = [
    "ArchitectAgent",
    "SyllabusContract",
    "ResearchAgent",
    "ResearchBriefing",
    "WriterAgent",
    "ChapterDraft",
    "DiagramAgent",
    "ReviewerAgent",
    "AuditReport",
    "MultiAgentOrchestrator",
]
