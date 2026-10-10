"""Architect Agent for thenuke multi-agent authoring system.

Responsible for:
1. Deconstructing the ingested corpus and grilling profile.
2. Generating a structured, multi-phase curriculum syllabus contract.
3. Defining chapter specifications, learning objectives, and code drill contracts.
4. Specifying mandatory vector diagram slots for architectural milestones.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ChapterContract:
    """Contract specification for a single reference manual chapter."""
    chapter_num: str
    title: str
    subheading: str
    topics: List[str]
    required_diagram: Optional[str] = None
    target_word_count: int = 1200
    drill_ids: List[int] = field(default_factory=list)


@dataclass
class PhaseContract:
    """Contract specification for a high-level curriculum phase."""
    phase_num: int
    title: str
    subtitle: str
    topics_summary: str
    chapters: List[ChapterContract] = field(default_factory=list)
    challenges_count: int = 3


@dataclass
class SyllabusContract:
    """Full curriculum contract across all phases and appendices."""
    topic: str
    edition_title: str
    phases: List[PhaseContract] = field(default_factory=list)
    appendices: List[Dict[str, Any]] = field(default_factory=list)
    diagram_slots: List[str] = field(default_factory=list)


class ArchitectAgent:
    """Specialized Agent responsible for document architecture and structural blueprints."""

    def __init__(self, topic: str = "Git"):
        self.topic = topic

    def plan_curriculum(self, profile: Dict[str, Any]) -> SyllabusContract:
        """Plans the curriculum contract according to grilling preferences."""
        level_of_detail = profile.get("level_of_detail", "senior_architect")
        diagram_dense = profile.get("visual_threshold", "diagram_dense") == "diagram_dense"

        # Construct standard 9-phase Git architecture contract
        phases = [
            PhaseContract(
                phase_num=1,
                title="VERSION CONTROL SYSTEMS & GIT PHILOSOPHY",
                subtitle="Foundational version control systems, distributed architecture, repository setup.",
                topics_summary="CVCS vs DVCS, Linus Torvalds, Content-Addressable Storage, Snapshots vs Deltas, SHA-1 Hashing",
                chapters=[
                    ChapterContract(
                        chapter_num="1.1",
                        title="What Is Git? Centralised vs Distributed Architecture",
                        subheading="Local Repositories and Offline Power",
                        topics=["DVCS vs CVCS", "Offline commits", "Peer-to-peer replication"],
                        drill_ids=[1],
                    ),
                    ChapterContract(
                        chapter_num="1.2",
                        title="The Linus Torvalds Origin: BitKeeper Breakdown",
                        subheading="Why BitKeeper Breakage Led to a Performance-First Engine",
                        topics=["Linux kernel workflow", "BitKeeper history", "Design goals: Speed, Simplicity, Non-linear"],
                    ),
                    ChapterContract(
                        chapter_num="1.3",
                        title="Snapshots, Not Deltas: Project State as First-Class Values",
                        subheading="How Git Models State as Cryptographic Immutable Snapshots",
                        topics=["Delta storage vs Snapshot DAG", "Storage efficiency", "Directed Acyclic Graphs"],
                    ),
                    ChapterContract(
                        chapter_num="1.4",
                        title="Content-Addressable Storage & Cryptographic Hashing",
                        subheading="SHA-1/SHA-256 Hashes, Object Invariants, and Immutability",
                        topics=["SHA-1 hashing", "Blobs", "Trees", "Commits", "Annotated Tags"],
                        required_diagram="object_model",
                        drill_ids=[2, 3],
                    ),
                ],
            ),
            PhaseContract(
                phase_num=2,
                title="REPOSITORY ARCHITECTURE & CONFIGURATION",
                subtitle="The .git directory structure, configuration scopes, and authentication.",
                topics_summary="git init, .git Directory Internals, 3 Configuration Scopes, SSH Authentication",
                chapters=[
                    ChapterContract(
                        chapter_num="2.1",
                        title="Initializing Repositories: The Anatomy of .git",
                        subheading="HEAD, config, objects, refs, and the Binary Index File",
                        topics=[".git/objects", ".git/refs", ".git/HEAD", ".git/index binary format"],
                        required_diagram="index_binary",
                        drill_ids=[1],
                    ),
                    ChapterContract(
                        chapter_num="2.2",
                        title="Configuration Scope Hierarchy",
                        subheading="System, Global, and Local Scopes Precedence",
                        topics=["/etc/gitconfig", "~/.gitconfig", ".git/config", "Scope precedence"],
                        drill_ids=[2],
                    ),
                    ChapterContract(
                        chapter_num="2.3",
                        title="SSH & Cryptographic Authentication",
                        subheading="Keypairs, ssh-agent, and Protocol Mechanics",
                        topics=["ed25519", "ssh-agent forwarding", "Personal Access Tokens", "Credential helpers"],
                    ),
                    ChapterContract(
                        chapter_num="2.4",
                        title="Environment Customization & Enterprise Ergonomics",
                        subheading="Aliases, Push Defaults, and Default Branch Names",
                        topics=["git config alias", "push.default simple", "core.autocrlf input"],
                        drill_ids=[3],
                    ),
                ],
            ),
            PhaseContract(
                phase_num=3,
                title="THE THREE TREES & CORE LIFECYCLE",
                subtitle="Working Directory, Staging Index, and HEAD Repository transitions.",
                topics_summary="Working Directory, Staging Area (Index), Repository (HEAD), git add, git commit",
                chapters=[
                    ChapterContract(
                        chapter_num="3.1",
                        title="The Three Trees Mental Model",
                        subheading="Working Tree, Index / Staging Area, and HEAD Commit Transitions",
                        topics=["Three Trees architecture", "Stat cache", "Virtual stage index"],
                        required_diagram="three_trees",
                        drill_ids=[1],
                    ),
                    ChapterContract(
                        chapter_num="3.2",
                        title="Staging Files: git add Under The Hood",
                        subheading="Tracking New vs Modified Files, Staging Partial Hunks",
                        topics=["git add -p", "Blob creation on stage", "lstat optimization"],
                        drill_ids=[2],
                    ),
                    ChapterContract(
                        chapter_num="3.3",
                        title="Atomic Commits & Historical Documentation",
                        subheading="git commit Invariants, Conventional Commits, and Commit Metadata",
                        topics=["Commit anatomy", "Conventional Commits", "Atomic commit hygiene"],
                    ),
                    ChapterContract(
                        chapter_num="3.4",
                        title="Inspecting State: git status Invariants",
                        subheading="Untracked, Modified, Staged State Machines",
                        topics=["git status porcelain", "Diff tree traversal", "Two-way compare"],
                        drill_ids=[3],
                    ),
                ],
            ),
            PhaseContract(
                phase_num=4,
                title="FILE TRACKING, IGNORING & TREE CLEANLINESS",
                subtitle="Pathspec rules, .gitignore parsing, cached removals, and working tree sanitation.",
                topics_summary=".gitignore Rules, Pattern Syntax, Untracking Cached Files, .gitkeep, git clean",
                chapters=[
                    ChapterContract(
                        chapter_num="4.1",
                        title="Ignoring Files: .gitignore Deep Dive",
                        subheading="Glob Patterns, Directory Anchoring, Negation (!), and Comments",
                        topics=["Wildcards", "Directory trailing slash", "Negation precedence", ".git/info/exclude"],
                        drill_ids=[1, 2],
                    ),
                    ChapterContract(
                        chapter_num="4.2",
                        title="Untracking Committed Files",
                        subheading="git rm --cached vs Physical File Deletion",
                        topics=["Index unlinking", "Accidental secrets", "Filter-repo vs cached rm"],
                    ),
                    ChapterContract(
                        chapter_num="4.3",
                        title="Tracking Empty Directories",
                        subheading="The .gitkeep Convention vs Git Tree Invariants",
                        topics=["Why Git ignores empty folders", "Tree object format", ".gitkeep pattern"],
                    ),
                    ChapterContract(
                        chapter_num="4.4",
                        title="Sanitizing the Working Tree",
                        subheading="git clean Safeguards (-n dry-run, -fd) Against Data Loss",
                        topics=["Untracked files", "Ignored directory deletion", "clean.requireForce"],
                        drill_ids=[3],
                    ),
                ],
            ),
            PhaseContract(
                phase_num=5,
                title="HISTORY INSPECTION & DIFFING ENGINE",
                subtitle="Revision walks, formatting graphs, commit ranges, and diff algorithms.",
                topics_summary="git log Formatting, Revision Walk, Commit Ranges, git diff Engine, git blame",
                chapters=[
                    ChapterContract(
                        chapter_num="5.1",
                        title="Navigating History: git log Internals",
                        subheading="Revision Walks, Formatting Strings, and Graph Visualization",
                        topics=["git log --graph", "--format=pretty", "Topological order vs Date order"],
                        drill_ids=[3],
                    ),
                    ChapterContract(
                        chapter_num="5.2",
                        title="Diffing Engines: Working Tree vs Index vs HEAD",
                        subheading="git diff vs git diff --staged Mechanics",
                        topics=["Myers diff algorithm", "Histogram diff", "Patience diff"],
                        drill_ids=[2],
                    ),
                    ChapterContract(
                        chapter_num="5.3",
                        title="Commit Ranges: Double-Dot vs Triple-Dot",
                        subheading="Reachable Sets vs Symmetric Difference Semantics",
                        topics=["A..B vs A...B in git log vs git diff", "Merge base calculation"],
                        drill_ids=[1],
                    ),
                    ChapterContract(
                        chapter_num="5.4",
                        title="Single Object Inspection & Forensic History",
                        subheading="git show and git blame Line-Level Accountability",
                        topics=["git show SHA-1", "git blame -L", "git log -S pickaxe"],
                    ),
                ],
            ),
            PhaseContract(
                phase_num=6,
                title="BRANCHING & POINTER MECHANICS",
                subtitle="Lightweight pointer manipulation, ref hierarchy, and detached HEAD states.",
                topics_summary="Branch Pointers, HEAD Symref, Fast-Forward Merges, Detached HEAD",
                chapters=[
                    ChapterContract(
                        chapter_num="6.1",
                        title="Branch Pointers Under The Hood",
                        subheading="41-Byte Text Files in refs/heads/ and Fast-Forward Merges",
                        topics=["Branch as pointer", "refs/heads/*", "Fast-forward pointer slide"],
                        required_diagram="branching_dag",
                        drill_ids=[1],
                    ),
                    ChapterContract(
                        chapter_num="6.2",
                        title="The HEAD Pointer & Symbolic References",
                        subheading="ref: refs/heads/main vs Detached HEAD Commit Pointers",
                        topics=["Symbolic ref", "Detached HEAD state", "HEAD inspection"],
                        drill_ids=[2],
                    ),
                    ChapterContract(
                        chapter_num="6.3",
                        title="Branch Management & Lifecycles",
                        subheading="Creation, Renaming, Deletion (-d vs -D safety)",
                        topics=["git branch -m", "git branch -d", "Unmerged branch warning"],
                    ),
                    ChapterContract(
                        chapter_num="6.4",
                        title="Modern Branch Switching: git switch vs git checkout",
                        subheading="Separation of Concerns in Modern Git CLI",
                        topics=["git switch -c", "git restore", "Deprecation of dual-purpose checkout"],
                        drill_ids=[3],
                    ),
                ],
            ),
            PhaseContract(
                phase_num=7,
                title="MERGING STRATEGIES & CONFLICT RESOLUTION",
                subtitle="3-way merges, recursive engines, LCA calculation, and conflict surgery.",
                topics_summary="Fast-Forward vs 3-Way Merge, LCA Calculation, Conflict Markers, git rerere",
                chapters=[
                    ChapterContract(
                        chapter_num="7.1",
                        title="Merge Strategies: Fast-Forward vs True 3-Way Merge",
                        subheading="Recursive Engine, Lowest Common Ancestor (LCA), and Merge Commits",
                        topics=["git merge-base", "LCA discovery", "Merge commit dual-parents"],
                        required_diagram="three_way_merge",
                        drill_ids=[1],
                    ),
                    ChapterContract(
                        chapter_num="7.2",
                        title="Merge Strategies Deep Dive: ORT vs Recursive vs Ours vs Octopus",
                        subheading="The Ostensibly Recursive's Twin (ORT) Default Engine",
                        topics=["ORT engine (Git 2.33+)", "Octopus merges", "Ours strategy vs ours option"],
                    ),
                    ChapterContract(
                        chapter_num="7.3",
                        title="Merge Conflict Anatomy & Surgical Resolution",
                        subheading="Understanding Diff3 Conflict Markers and Conflict State Recovery",
                        topics=["<<<<<<< markers", "diff3 style", "Stage 1, 2, 3 in index"],
                        required_diagram="merge_conflict",
                        drill_ids=[2],
                    ),
                    ChapterContract(
                        chapter_num="7.4",
                        title="Reuse Recorded Resolution: git rerere",
                        subheading="Automating Repetitive Conflict Resolutions in Long-Lived Branches",
                        topics=["rerere.enabled", "rr-cache directory", "Pre-image / Post-image matching"],
                        drill_ids=[3],
                    ),
                ],
            ),
            PhaseContract(
                phase_num=8,
                title="HISTORY REWRITING & RECOVERY SYSTEMS",
                subtitle="Rebase patch replays, interactive squashing, reset mutations, and the reflog safety net.",
                topics_summary="git rebase, Interactive Rebase, git reset --soft/--mixed/--hard, git reflog",
                chapters=[
                    ChapterContract(
                        chapter_num="8.1",
                        title="Git Rebase Under The Hood",
                        subheading="Detaching Commits and Replaying Patches Linearly Onto Upstream",
                        topics=["Linear history", "Patch replay", "Golden Rule of Rebase"],
                        required_diagram="rebase_replay",
                        drill_ids=[1],
                    ),
                    ChapterContract(
                        chapter_num="8.2",
                        title="Interactive Rebase: git rebase -i",
                        subheading="Pick, Squash, Fixup, Reword, Edit, and Dropping Commits",
                        topics=["Todo script", "Squash vs Fixup", "Autosquash workflow"],
                        drill_ids=[2],
                    ),
                    ChapterContract(
                        chapter_num="8.3",
                        title="Undoing Changes: git reset (--soft vs --mixed vs --hard)",
                        subheading="State Mutations Across the Three Trees",
                        topics=["--soft", "--mixed", "--hard", "Safety boundaries"],
                        required_diagram="reset_matrix",
                        drill_ids=[3],
                    ),
                    ChapterContract(
                        chapter_num="8.4",
                        title="The Safety Net: git reflog & Dangling Object Recovery",
                        subheading="Recovering 'Deleted' Commits, Branches, and Hard-Reset State",
                        topics=["HEAD reflog", "logs/refs/*", "Dangling commit salvage", "git fsck"],
                    ),
                ],
            ),
            PhaseContract(
                phase_num=9,
                title="DISTRIBUTED REMOTES & ADVANCED PLUMBING",
                subtitle="Remote tracking branches, transport protocols, packfiles, and plumbing commands.",
                topics_summary="Remotes, origin, Tracking Branches, git push/pull/fetch, Plumbing Commands",
                chapters=[
                    ChapterContract(
                        chapter_num="9.1",
                        title="Remote Architecture: Remotes, origin, and Tracking Branches",
                        subheading="refs/remotes/origin/* vs Local Branches and Tracking Configuration",
                        topics=["Remote-tracking refs", "fetch refspec", "Upstream branch tracking"],
                        required_diagram="remote_sync",
                        drill_ids=[1],
                    ),
                    ChapterContract(
                        chapter_num="9.2",
                        title="Synchronization Protocols: git fetch, pull, and push",
                        subheading="Smart HTTP vs SSH Transport, Force-With-Lease Safety",
                        topics=["Packfile negotiation", "git pull --rebase", "git push --force-with-lease"],
                        drill_ids=[2],
                    ),
                    ChapterContract(
                        chapter_num="9.3",
                        title="Plumbing vs Porcelain: Low-Level Internal Tools",
                        subheading="hash-object, cat-file, mktree, commit-tree, and update-ref",
                        topics=["Porcelain layer", "Plumbing layer", "Building a repository manually"],
                        drill_ids=[3],
                    ),
                    ChapterContract(
                        chapter_num="9.4",
                        title="Repository Maintenance & Storage Optimization",
                        subheading="Loose Objects vs Packfiles, git gc, repack, and Pruning Mechanics",
                        topics=["Packfiles (.pack)", "Index files (.idx)", "Delta compression", "git gc --prune"],
                    ),
                ],
            ),
        ]

        # Appendices
        appendices = [
            {
                "letter": "A",
                "title": "The Myers Diff Algorithm & Longest Common Subsequence (LCS)",
                "scope": "Graph traversal, edit distance matrices, time complexity O((N+M)D), and diff generation.",
            },
            {
                "letter": "B",
                "title": "Git Internal Packfile Format & Delta Compression",
                "scope": "Packfile v2 header, variable-length integer encoding, OFS_DELTA vs REF_DELTA, and fanout tables.",
            },
            {
                "letter": "C",
                "title": "Enterprise Git Workflows & Monorepo Scaling",
                "scope": "Trunk-based development, GitHub Flow, Git LFS pointer format, sparse-checkout, and scalar.",
            },
        ]

        # Extract all diagram slots
        diagram_slots = [
            ch.required_diagram
            for p in phases
            for ch in p.chapters
            if ch.required_diagram is not None
        ]

        return SyllabusContract(
            topic=self.topic,
            edition_title="Architecture & Core Internals — Monochrome High-Density Engineering Edition",
            phases=phases,
            appendices=appendices,
            diagram_slots=diagram_slots,
        )
