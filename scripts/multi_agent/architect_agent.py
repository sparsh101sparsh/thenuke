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
        if self.topic.strip().lower() != "git":
            return self.plan_universal_curriculum(profile)

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

    def plan_universal_curriculum(self, profile: Dict[str, Any]) -> SyllabusContract:
        """Dynamically designs an unconstrained, multi-phase curriculum for ANY domain or topic."""
        topic_clean = self.topic.strip()
        num_phases = int(profile.get("num_phases", 8))
        if num_phases < 2:
            num_phases = 6

        if any(k in topic_clean.lower() for k in ["english", "language", "grammar", "spoken"]):
            return self._plan_english_curriculum(profile)

        phase_templates = [
            (
                "FOUNDATIONS, TAXONOMY & FIRST PRINCIPLES",
                "Epistemological roots, foundational nomenclature, and core mental models.",
                [
                    ("First Principles & Core Definition", "Defining the domain, taxonomy, and mental model baseline."),
                    ("Historical Evolution & Paradigm Shifts", "Why legacy approaches failed and modern systems emerged."),
                    ("Core Axioms & Foundational Laws", "The unbendable rules and architectural primitives of the domain."),
                    ("Operational Environment & Tooling Baseline", "Setting up diagnostic environments, tooling, and verification."),
                ],
            ),
            (
                "PRIMITIVE UNITS & COMPONENT MECHANICS",
                "Low-level building blocks, structural units, and atomic behaviors.",
                [
                    ("Atomic Units & Data Structures", "Deconstructing fundamental building blocks and representations."),
                    ("State Lifecycle & Mutation Semantics", "How state transitions from transient to persistent form."),
                    ("Invariants & Verification Rules", "Enforcing correctness, boundary conditions, and validation."),
                    ("Component Composition & Interface Design", "Connecting atomic units into coherent operational nodes."),
                ],
            ),
            (
                "INTERMEDIATE PATTERNS & DATA FLOWS",
                "Structural coordination, pipeline flows, and synchronization mechanics.",
                [
                    ("Pipelines & Data Transformation Flow", "Tracing throughput across intermediate processing layers."),
                    ("Concurrency, Isolation & Conflict Resolution", "Managing concurrent operations, locking, and arbitration."),
                    ("Modular Architecture & Loose Coupling", "Partitioning systems into maintainable, autonomous modules."),
                    ("Error Handling & Fault Recovery", "Graceful degradation, retries, and invariant restoration."),
                ],
            ),
            (
                "ADVANCED INTERNALS & DEEP MECHANICS",
                "Low-level implementation engines, memory models, and execution details.",
                [
                    ("The Core Engine Under The Hood", "Stepping through internal execution pipelines line-by-line."),
                    ("Memory Layout, Optimization & Latency", "Physical layout, caching behavior, and latency reduction."),
                    ("Asynchronous Operations & Scheduling", "Event loops, dispatchers, and asynchronous state machines."),
                    ("Security Boundaries & Defensive Invariants", "Hardening interfaces against corruption, leaks, and exploits."),
                ],
            ),
            (
                "EDGE CASES, ANOMALIES & FAILURE POSTMORTEMS",
                "Dissecting complex failure modes, edge cases, and emergency recovery.",
                [
                    ("Failure Modes & Diagnostic Telemetry", "Recognizing silent data corruption and edge anomalies."),
                    ("High-Stakes Postmortems & Root Cause Analysis", "Real-world incident breakdowns and forensic recovery."),
                    ("Surgical Remediation & Rollback Strategies", "Safely unrolling catastrophic state mutations."),
                    ("Stress Testing & Resilience Benchmarks", "Validating system integrity under extreme adversarial loads."),
                ],
            ),
            (
                "ENTERPRISE PRODUCTION & ECOSYSTEM INTEGRATION",
                "Scaling, collaboration, monitoring, and industrial best practices.",
                [
                    ("Enterprise Architecture & Team Conventions", "Standardizing workflows, styling, and architectural rules."),
                    ("Automated Verification & Continuous Integration", "Building automated quality gates and verification suites."),
                    ("Monitoring, Observability & Performance Profiling", "Tracking production metrics, bottlenecks, and KPIs."),
                    ("Ecosystem Tooling, Automation & Extensions", "Leveraging modern CLI tooling and automation extensions."),
                ],
            ),
            (
                "PERFORMANCE TUNING & ADVANCED METAPROGRAMMING",
                "Extreme optimization, dynamic adaptation, and expert techniques.",
                [
                    ("Profiling Bottlenecks & Algorithmic Refinement", "Identifying critical paths and eliminating hot spots."),
                    ("Metaprogramming & Dynamic Code Synthesis", "Introspection, code generation, and declarative paradigms."),
                    ("Distributed Scaling & High-Availability Topology", "Scaling across heterogeneous nodes and multi-region clusters."),
                    ("Zero-Dependency Architectural Blueprints", "Building production-grade engines without third-party dependencies."),
                ],
            ),
            (
                "INDUSTRIAL CAPSTONE ENGINE & PRODUCTION IMPLEMENTATION",
                "End-to-end full-scale implementation of an enterprise production system.",
                [
                    ("System Architecture Specification & Blueprint", "Defining the formal specification, contracts, and schema."),
                    ("Core Engine Implementation From Scratch", "Writing the end-to-end working production engine in pure code."),
                    ("Industrial Verification & Integration Gauntlet", "Running full test suites, stress testing, and edge validation."),
                    ("Deployment, Operation & Long-Term Maintenance", "Production deployment, migration runbooks, and SLA compliance."),
                ],
            ),
        ]

        phases: List[PhaseContract] = []
        for p_idx in range(num_phases):
            tmpl_idx = p_idx % len(phase_templates)
            p_title, p_sub, ch_list = phase_templates[tmpl_idx]
            actual_pno = p_idx + 1
            if p_idx >= len(phase_templates):
                p_title = f"{p_title} (ADVANCED MODULE {p_idx - len(phase_templates) + 2})"

            chapters: List[ChapterContract] = []
            for ch_idx, (ch_title, ch_sub) in enumerate(ch_list):
                ch_num = f"{actual_pno}.{ch_idx + 1}"
                chapters.append(
                    ChapterContract(
                        chapter_num=ch_num,
                        title=f"{topic_clean}: {ch_title}",
                        subheading=ch_sub,
                        topics=[f"{topic_clean} {ch_title.split()[0]}", "Invariants", "Architecture"],
                        drill_ids=[ch_idx + 1] if ch_idx < 3 else [],
                    )
                )

            phases.append(
                PhaseContract(
                    phase_num=actual_pno,
                    title=f"{topic_clean.upper()} — {p_title}",
                    subtitle=p_sub,
                    topics_summary=f"{topic_clean} Core Mechanics, Invariants, Architecture, Industrial Drills",
                    chapters=chapters,
                    challenges_count=3,
                )
            )

        appendices = [
            {
                "letter": "A",
                "title": f"{topic_clean} Formal Axioms & Invariant Reference Guide",
                "scope": f"Complete mathematical/algorithmic invariants and rule sets governing {topic_clean}.",
            },
            {
                "letter": "B",
                "title": f"{topic_clean} Enterprise Incident Postmortems & Disaster Recovery",
                "scope": f"Real-world production failures in {topic_clean} and surgical resolution playbooks.",
            },
            {
                "letter": "C",
                "title": f"{topic_clean} 30 Industrial FAANG Machine-Coding Gauntlet",
                "scope": f"High-difficulty algorithmic and architectural challenges with complete verified solutions.",
            },
        ]

        return SyllabusContract(
            topic=topic_clean,
            edition_title=f"{topic_clean}: The Complete Reference Manual • Monochrome Edition",
            phases=phases,
            appendices=appendices,
            diagram_slots=[],
        )

    def _plan_english_curriculum(self, profile: Dict[str, Any]) -> SyllabusContract:
        """Specialized high-density curriculum for English Language & Communication Mastery."""
        phases_data = [
            (
                1,
                "PHONETICS, PRONUNCIATION & IPA ACOUSTICS",
                "Speech sound mechanics, vowel trapeze, plosives, and International Phonetic Alphabet.",
                "IPA Vowels, Diphthongs, Plosives, Syllable Stress, Intonation Contours",
                [
                    ("1.1", "International Phonetic Alphabet (IPA) Foundations", "Acoustic Articulation & Vowel Trapeze"),
                    ("1.2", "Consonant Articulation Mechanics", "Plosives, Fricatives, Affricates, and Nasals"),
                    ("1.3", "Word Stress & Syllabic Weight", "Primary Stress, Secondary Stress, and Reduced Vowels (Schwa)"),
                    ("1.4", "Connected Speech & Sandhi Phenomena", "Elision, Linking /r/, Glottal Stops, and Assimilation"),
                ],
            ),
            (
                2,
                "MORPHOLOGICAL SYNTAX & PARTS OF SPEECH",
                "Derivational morphology, noun phrases, determiners, and adjective ordering.",
                "Morphemes, Affixes, Countable vs Uncountable, Determiners, Royal Order of Adjectives",
                [
                    ("2.1", "Root Morphemes & Affixation", "Prefixes, Suffixes, and Semantic Derivations"),
                    ("2.2", "Noun Classification & Mass Invariants", "Countable, Uncountable, and Collective Noun Dynamics"),
                    ("2.3", "The Determiner Hierarchy", "Articles (a/an/the), Quantifiers, and Demonstratives"),
                    ("2.4", "The Royal Order of Adjectives", "Opinion, Size, Physical Quality, Shape, Age, Color, Origin, Material"),
                ],
            ),
            (
                3,
                "TENSE SYSTEMS & TEMPORAL ASPECT INVARIANTS",
                "The 12 English tenses, aspectual distinctions, and temporal anchoring.",
                "Simple, Continuous, Perfect, Perfect Continuous, State vs Dynamic Verbs",
                [
                    ("3.1", "The Aspect Matrix: Simple vs Continuous", "Habitual Truths vs In-Progress Dynamic States"),
                    ("3.2", "The Perfect Aspect: Past In Action", "Present Perfect Anteriority vs Simple Past Definitive Anchoring"),
                    ("3.3", "Past Perfect & Narrative Sequencing", "Had + V3 Anterior Ordering in Complex Narrative Clauses"),
                    ("3.4", "Future Modality & Stative Invariants", "Will vs Going to vs Present Continuous, Non-Continuous Stative Verbs"),
                ],
            ),
            (
                4,
                "MODAL AUXILIARIES & CONDITIONAL TOPOLOGY",
                "Epistemic vs deontic modality, zero to mixed conditionals, and hypothetical logic.",
                "Epistemic Modals, Deontic Modals, Zero/First/Second/Third/Mixed Conditionals",
                [
                    ("4.1", "Deontic Modals: Obligation & Permission", "Must vs Have to vs Should vs Ought to"),
                    ("4.2", "Epistemic Modals: Probability & Deduction", "Must be vs Can't be vs Might have been"),
                    ("4.3", "Standard Conditionals (0, 1, 2, 3)", "Real vs Unreal Hypothetical Topology"),
                    ("4.4", "Mixed Conditionals & Inverted Conditionals", "Had I known vs Were you to consider"),
                ],
            ),
            (
                5,
                "CLAUSE HIERARCHIES, COORDINATION & SUBORDINATION",
                "Sentence architecture, relative clauses, participial phrases, and punctuation.",
                "Independent Clauses, Subordinate Clauses, Restrictive vs Non-Restrictive, Oxford Comma",
                [
                    ("5.1", "Complex Sentence Architecture", "Subordinating Conjunctions and Dependent Clause Attachment"),
                    ("5.2", "Relative Clauses: Restrictive vs Non-Restrictive", "That vs Which, Punctuation Invariants"),
                    ("5.3", "Participial Phrases & Dangling Modifiers", "Present/Past Participles and Dangling Modifier Traps"),
                    ("5.4", "Inversion & Fronting for Rhetorical Focus", "Never had I seen, Seldom do we witness"),
                ],
            ),
            (
                6,
                "IDIOMATIC PHRASAL VERBS & COLLOCATIONS",
                "Particle semantics, separable vs inseparable phrasal verbs, and collocations.",
                "Transitive Phrasal Verbs, Particle Movement, Strong Collocations, Fixed Idioms",
                [
                    ("6.1", "The Semantic Logic of Prepositional Particles", "Up, Down, Out, Off, Over Metaphorical Vectors"),
                    ("6.2", "Separable vs Inseparable Transitive Phrasal Verbs", "Turn down the offer vs Turn it down"),
                    ("6.3", "High-Value Academic & Business Collocations", "Make vs Do, Bitterly disappointed vs Vitally important"),
                    ("6.4", "Idiomatic Precision in Executive Contexts", "Cutting corners, Biting the bullet, Moving the needle"),
                ],
            ),
            (
                7,
                "ADVANCED RHETORIC, COHESION & DISCOURSE",
                "Paragraph architecture, signposting, lexical cohesion, and style registers.",
                "Topic Sentences, Transition Markers, Lexical Cohesion, Active vs Passive Voice",
                [
                    ("7.1", "Macro-Structure: Topic Sentences & Paragraph Unity", "PEEL Framework (Point, Evidence, Explanation, Link)"),
                    ("7.2", "Cohesive Devices & Signposting", "Furthermore, In stark contrast, Consequently, Notwithstanding"),
                    ("7.3", "Strategic Passive Voice & Nominalization", "Objective Scientific Register vs Active Narrative Pacing"),
                    ("7.4", "Eliminating Redundancy & Cognitive Fluff", "Strunk & White Principles: Vigorous, Concise Expression"),
                ],
            ),
            (
                8,
                "EXECUTIVE COMMUNICATION & NEGOTIATION PRAGMATICS",
                "Cross-cultural pragmatics, diplomatic hedging, persuasive rhetoric, and speeches.",
                "Diplomatic Hedging, Escalation Protocols, Persuasive Rhetoric, Q&A Mastery",
                [
                    ("8.1", "Diplomatic Hedging & Softening Directives", "Could we possibly consider vs It would seem that"),
                    ("8.2", "Handling Disagreements & Constructive Pushback", "I see your point, however vs With all due respect"),
                    ("8.3", "The Rhetoric of Persuasion: Ethos, Pathos, Logos", "Structuring High-Stakes Pitches and Executive Briefings"),
                    ("8.4", "Spontaneous Impromptu Speaking & Frameworks", "PREP (Point, Reason, Example, Point) Framework"),
                ],
            ),
        ]
        requested_phases = int(profile.get("num_phases", len(phases_data)))
        if 2 <= requested_phases < len(phases_data):
            phases_data = phases_data[:requested_phases]

        phases: List[PhaseContract] = []
        for pno, title, sub, topics_sum, chs in phases_data:
            chapter_contracts = [
                ChapterContract(
                    chapter_num=c_num,
                    title=c_title,
                    subheading=c_sub,
                    topics=["English Mechanics", "Syntax", "Pronunciation", "Rhetoric"],
                    drill_ids=[idx + 1] if idx < 3 else [],
                )
                for idx, (c_num, c_title, c_sub) in enumerate(chs)
            ]
            phases.append(
                PhaseContract(
                    phase_num=pno,
                    title=f"ENGLISH MASTERY — {title}",
                    subtitle=sub,
                    topics_summary=topics_sum,
                    chapters=chapter_contracts,
                    challenges_count=3,
                )
            )

        appendices = [
            {
                "letter": "A",
                "title": "International Phonetic Alphabet (IPA) Complete Articulation Reference",
                "scope": "Acoustic chart of 44 English phonemes, vowel formant frequencies, and consonant voicing.",
            },
            {
                "letter": "B",
                "title": "Comprehensive Irregular Verb Morphology & Historical Ablaut Classes",
                "scope": "200+ irregular verb principal parts categorized by historical Germanic ablaut vowel changes.",
            },
            {
                "letter": "C",
                "title": "Executive Rhetoric & 500 High-Leverage Academic Collocations",
                "scope": "Formal register collocation dictionary for boardroom, legal, and academic publications.",
            },
        ]

        return SyllabusContract(
            topic="English Language & Communication Mastery",
            edition_title="English: The Complete Reference Manual • Monochrome Edition",
            phases=phases,
            appendices=appendices,
            diagram_slots=[],
        )
