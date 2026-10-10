"""Consolidated Git Engineering Reference Manual Content Hub.
Provides all 9 phases, 36+ chapters, 27 challenges with full working solutions,
and 3 comprehensive architectural deep-dive appendices.
Strict 100% Roman Hinglish narrative, zero Devanagari script.
"""

from typing import Dict, Any, List
from scripts.synthesis.git_phases_1_2 import PHASE_1, PHASE_2
from scripts.synthesis.git_phases_3_4 import PHASE_3, PHASE_4
from scripts.synthesis.git_phases_5_6 import PHASE_5, PHASE_6
from scripts.synthesis.git_phases_7_8 import PHASE_7, PHASE_8
from scripts.synthesis.git_phases_9_app import PHASE_9, APPENDICES

ALL_GIT_PHASES: List[Dict[str, Any]] = [
    PHASE_1,
    PHASE_2,
    PHASE_3,
    PHASE_4,
    PHASE_5,
    PHASE_6,
    PHASE_7,
    PHASE_8,
    PHASE_9,
]

GIT_APPENDICES: List[Dict[str, Any]] = APPENDICES


def build_full_git_manual_markdown(branding: str = "Prepared by @issparsh @sumitsingh097") -> str:
    """Builds the complete, publication-grade Git manual markdown string."""
    lines: List[str] = []

    # 1. Document Cover Title
    lines.append("# GIT: The Complete Engineering Reference")
    lines.append("## Architecture & Core Internals — Monochrome High-Density Engineering Edition")
    lines.append("")
    lines.append(f"{branding}")
    lines.append("")
    lines.append("=" * 80)
    lines.append("")

    # 2. Detailed Multi-Part Syllabus & Table of Contents (Part I to VI)
    lines.append("=" * 80)
    lines.append("DETAILED SYLLABUS & TABLE OF CONTENTS (PART I)")
    lines.append("Foundational version control systems, distributed architecture, repository setup, and configuration scopes.")
    lines.append("=" * 80)
    lines.append("")
    lines.append("PHASE 1 — VERSION CONTROL SYSTEMS & GIT PHILOSOPHY")
    lines.append("Topics: CVCS vs DVCS, Linus Torvalds, Content-Addressable Storage, Snapshots vs Deltas, SHA-1 Hashing")
    lines.append("Chapter 1.1: What Is Git? Centralised vs Distributed Architecture — Local Repositories and Offline Power.")
    lines.append("Chapter 1.2: The Linus Torvalds Origin — Why BitKeeper Breakage Led to a Performance-First Engine.")
    lines.append("Chapter 1.3: Snapshots, Not Deltas — How Git Models Project State as a Series of Complete Snapshots.")
    lines.append("Chapter 1.4: Content-Addressable Storage — SHA-1 Hashes, Cryptographic Integrity, and Immutability.")
    lines.append("Hands-On Challenges: Challenge 1 (DVCS vs CVCS Offline Commit Trace) • Challenge 2 (Content-Addressable Blob Storage) • Challenge 3 (Git Repository Scaffolder).")
    lines.append("")
    lines.append("PHASE 2 — REPOSITORY ARCHITECTURE & CONFIGURATION")
    lines.append("Topics: git init, .git Directory Internals, 3 Configuration Scopes, Global vs Local Identities, SSH Authentication")
    lines.append("Chapter 2.1: Initializing Repositories: git init, The Anatomy of the .git Directory (HEAD, config, objects, refs).")
    lines.append("Chapter 2.2: Git Configuration Hierarchy: System, Global, and Local Scopes (user.name, user.email, core.editor).")
    lines.append("Chapter 2.3: SSH & Authentication Setup: Keypairs, ssh-agent, and Secure Remote Communication.")
    lines.append("Chapter 2.4: Environment Customization: Useful Aliases, Default Branch Naming, and Push Defaults.")
    lines.append("Hands-On Challenges: Challenge 1 (Git Config Scope Precedence Trace) • Challenge 2 (Zero-Dependency INI Config Parser) • Challenge 3 (Multi-Profile Identity Switcher).")
    lines.append("")

    lines.append("=" * 80)
    lines.append("DETAILED SYLLABUS & TABLE OF CONTENTS (PART II)")
    lines.append("The Three Trees model, atomic commits, staging lifecycle, .gitignore patterns, and repository cleanliness.")
    lines.append("=" * 80)
    lines.append("")
    lines.append("PHASE 3 — THE THREE TREES & CORE LIFECYCLE")
    lines.append("Topics: Working Directory, Staging Area (Index), Repository (HEAD), git add, git commit, git status, Conventional Commits")
    lines.append("Chapter 3.1: The Three Trees Mental Model: Working Tree, Index/Staging Area, and HEAD Commit.")
    lines.append("Chapter 3.2: Staging Files: git add Deep Dive, Tracking New vs Modified Files, Staging Partial Hunks.")
    lines.append("Chapter 3.3: Atomic Commits: git commit, Commit Messages as Historical Documentation, Conventional Commits.")
    lines.append("Chapter 3.4: Inspecting State: git status Invariants, Untracked vs Tracked, Changes Staged for Commit.")
    lines.append("Hands-On Challenges: Challenge 1 (Three Trees State Machine Trace) • Challenge 2 (Binary Tree Object Serializer) • Challenge 3 (Pure Python Staging Simulator).")
    lines.append("")
    lines.append("PHASE 4 — FILE TRACKING, IGNORING & TREE CLEANLINESS")
    lines.append("Topics: .gitignore Rules, Pattern Syntax, Untracking Cached Files, .gitkeep Conventions, git clean Safeguards")
    lines.append("Chapter 4.1: Ignoring Files: .gitignore Syntax, Wildcards, Negation (!), and Directory Anchoring.")
    lines.append("Chapter 4.2: Untracking Already Committed Files: git rm --cached and Clearing the Index Cache.")
    lines.append("Chapter 4.3: Tracking Empty Directories: The .gitkeep Convention vs Git's Inability to Track Empty Trees.")
    lines.append("Chapter 4.4: Cleaning the Working Tree: git clean Flags (-n dry run, -fd), Safeguards Against Data Loss.")
    lines.append("Hands-On Challenges: Challenge 1 (.gitignore Negation & Pruning Trace) • Challenge 2 (Git Pathspec Pattern Matcher) • Challenge 3 (Pre-Commit Secret Scanner Hook).")
    lines.append("")

    lines.append("=" * 80)
    lines.append("DETAILED SYLLABUS & TABLE OF CONTENTS (PART III)")
    lines.append("History exploration, revision walks, commit ranges, diffing engines, branching architecture, and detached HEAD states.")
    lines.append("=" * 80)
    lines.append("")
    lines.append("PHASE 5 — HISTORY INSPECTION & DIFFING ENGINE")
    lines.append("Topics: git log Formatting, Revision Walk, Commit Ranges, git diff Engine, git show, git blame")
    lines.append("Chapter 5.1: Navigating History: git log Flags (--oneline, --graph, --decorate, --stat, -p).")
    lines.append("Chapter 5.2: Inspecting Diffs: git diff (Working Tree vs Index) vs git diff --staged (Index vs HEAD).")
    lines.append("Chapter 5.3: Comparing Branches and Commits: Double-Dot (..) vs Triple-Dot (...) Range Semantics.")
    lines.append("Chapter 5.4: Single Object Inspection: git show, Examining Specific Blobs and Commits via SHA-1.")
    lines.append("Hands-On Challenges: Challenge 1 (Commit Range Double vs Triple Dot Trace) • Challenge 2 (Myers Diff Algorithm) • Challenge 3 (Interactive Terminal Commit Graph Viewer).")
    lines.append("")
    lines.append("PHASE 6 — BRANCHING & POINTER MECHANICS")
    lines.append("Topics: Branch as a 41-Byte Pointer, git branch, git checkout, git switch, Detached HEAD State, Branch Deletion")
    lines.append("Chapter 6.1: Branch Architecture: Why Git Branches Are Cheap 41-Byte SHA-1 Pointer Files in refs/heads/.")
    lines.append("Chapter 6.2: Branch Creation & Switching: git branch vs git switch vs git checkout (-b).")
    lines.append("Chapter 6.3: The Detached HEAD State: What Happens When HEAD Points to a Commit Instead of a Branch Ref.")
    lines.append("Chapter 6.4: Deleting and Renaming Branches: Safe Delete (-d) vs Force Delete (-D), Upstream Tracking.")
    lines.append("Hands-On Challenges: Challenge 1 (Detached HEAD State & Garbage Collection Trace) • Challenge 2 (Lowest Common Ancestor Merge Base Finder) • Challenge 3 (Automated Stale Branch Cleanup Engine).")
    lines.append("")

    lines.append("=" * 80)
    lines.append("DETAILED SYLLABUS & TABLE OF CONTENTS (PART IV)")
    lines.append("Fast-forward and 3-way merge algorithms, conflict resolution, stashing stacks, and semantic release tagging.")
    lines.append("=" * 80)
    lines.append("")
    lines.append("PHASE 7 — MERGING STRATEGIES & CONFLICT RESOLUTION")
    lines.append("Topics: Fast-Forward Merge, Three-Way Merge, Common Ancestor (Merge Base), Conflict Markers, Resolution Workflow, git merge --abort")
    lines.append("Chapter 7.1: Fast-Forward Merges: Linear History Extension When No Divergence Exists.")
    lines.append("Chapter 7.2: Three-Way Merges: Recursive/Ort Strategy, Merge Commits with Two Parents, Finding the Merge Base.")
    lines.append("Chapter 7.3: Merge Conflict Anatomy: Understanding Conflict Markers (<<<<<<<, =======, >>>>>>>).")
    lines.append("Chapter 7.4: Conflict Resolution Workflow: Editing Markers, git add to Mark Resolved, git merge --abort.")
    lines.append("Hands-On Challenges: Challenge 1 (3-Way Merge Conflict Marker Resolution Trace) • Challenge 2 (3-Way Text Merge Engine) • Challenge 3 (Terminal Merge Conflict Resolver TUI).")
    lines.append("")
    lines.append("PHASE 8 — ADVANCED WORKING TREE MANIPULATION & STASHING")
    lines.append("Topics: git stash Stack, Stash Internals, git restore, Lightweight vs Annotated Tags, GPG Signing, Semantic Versioning")
    lines.append("Chapter 8.1: Stashing Uncommitted Changes: git stash push, git stash pop vs apply, Inspecting the Stash Stack.")
    lines.append("Chapter 8.2: Stashing Untracked Files (-u) and Stash Branching: Safely Context-Switching in Mid-Feature.")
    lines.append("Chapter 8.3: Undoing Changes in the Modern Era: git restore (--staged vs working tree) vs Legacy git checkout.")
    lines.append("Chapter 8.4: Git Tags & Semantic Releases: Lightweight Tags vs Annotated Tags (git tag -a -m), GPG Signing.")
    lines.append("Hands-On Challenges: Challenge 1 (Git Stash Stack & Untracked Files Trace) • Challenge 2 (Worktree Stash Stack Engine) • Challenge 3 (Semantic Release & Annotated Tag Generator).")
    lines.append("")

    lines.append("=" * 80)
    lines.append("DETAILED SYLLABUS & TABLE OF CONTENTS (PART V)")
    lines.append("History linearization, interactive rebase, remote operations, enterprise workflows, and Capstone Mini-Git CLI.")
    lines.append("=" * 80)
    lines.append("")
    lines.append("PHASE 9 — HISTORY REWRITING, REBASE & DISTRIBUTED WORKFLOWS")
    lines.append("Topics: git rebase, Interactive Rebase (-i), The Golden Rule of Rebasing, Remote Workflows, Pull Requests, Capstone Mini-Git CLI")
    lines.append("Chapter 9.1: Git Rebase Fundamentals: Replaying Commits Onto a New Base, Linearizing Commit History.")
    lines.append("Chapter 9.2: Interactive Rebase (git rebase -i): Squashing, Fixups, Rewording, and Dropping Commits.")
    lines.append("Chapter 9.3: The Golden Rule of Rebasing: Never Rebase Commits That Have Been Pushed to Public Remotes.")
    lines.append("Chapter 9.4: Remote Operations: git remote, git fetch vs git pull (--rebase), git push (--force-with-lease).")
    lines.append("Chapter 9.5: Enterprise Collaborative Workflows: GitHub Flow vs Trunk-Based Development vs Gitflow.")
    lines.append("Hands-On Challenges: Challenge 1 (Rebase vs Merge Topology Divergence Trace) • Challenge 2 (Interactive Rebase Plan Engine) • Challenge 3 (Capstone: Zero-Dependency Mini-Git CLI Engine pygit.py).")
    lines.append("")

    lines.append("=" * 80)
    lines.append("DETAILED SYLLABUS & TABLE OF CONTENTS (PART VI)")
    lines.append("Low-level object database internals, disaster recovery gauntlet, and 30 FAANG architectural interview scenarios.")
    lines.append("=" * 80)
    lines.append("")
    lines.append("APPENDICES — ARCHITECTURAL DEEP DIVES & MACHINE CODING GAUNTLET")
    lines.append("Deep Dive A: Git Plumbing & Object Database Internals — Blobs, Trees, Commits, Tags, zlib, cat-file, packed-refs, and packfiles.")
    lines.append("Deep Dive B: The Catastrophe Recovery Gauntlet — git reflog, Rescuing Deleted Branches, fsck --lost-found, and accidental force-push recovery.")
    lines.append("Deep Dive C: 30 FAANG Version Control Scenario Questions & Solutions — Scale, Monorepos vs Polyrepos, Hook security, and DAG algorithms.")
    lines.append("<!-- END SYLLABUS -->")
    lines.append("")

    # 3. Render Each Phase
    for phase in ALL_GIT_PHASES:
        lines.append("=" * 80)
        lines.append(f"PHASE {phase['number']} — {phase['title'].upper()}")
        lines.append(f"Topics: {phase['topics']}")
        lines.append("=" * 80)
        lines.append("")

        for ch in phase["chapters"]:
            lines.append(f"## {ch['title']}")
            lines.append("")
            lines.append(ch["body"])
            lines.append("")

        # Render Practice Drills
        lines.append("=" * 80)
        lines.append(f"PHASE {phase['number']} — PRACTICE DRILLS")
        lines.append("=" * 80)
        lines.append("")

        for c_key in ["c1", "c2", "c3"]:
            c = phase["challenges"][c_key]
            lines.append(f"### {c['title']}")
            lines.append("")
            lines.append("Problem Statement & Requirements:")
            lines.append(c["prompt"])
            lines.append("")
            lines.append(f"Code: {c['solution_title']}")
            lines.append("```python" if "import " in c["solution_code"] or "def " in c["solution_code"] else "```bash")
            lines.append(c["solution_code"].strip())
            lines.append("```")
            lines.append("")

    # 4. Render Appendices
    lines.append("=" * 80)
    lines.append("APPENDICES — ARCHITECTURAL DEEP DIVES & MACHINE CODING")
    lines.append("=" * 80)
    lines.append("")

    for app in GIT_APPENDICES:
        lines.append(f"## {app['title']}")
        lines.append(f"Scope: {app['scope']}")
        lines.append("")
        lines.append(app["body"])
        lines.append("")

    full_text = "\n".join(lines)
    return full_text
