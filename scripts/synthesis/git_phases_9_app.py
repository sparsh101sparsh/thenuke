"""Git Engineering Reference Manual — Phase 9 & Appendices Content.
Strict 100% Roman Hinglish narrative, zero Devanagari, production-grade code.
"""

from typing import Dict, Any, List

PHASE_9 = {
    "number": 9,
    "title": "History Rewriting, Rebase & Distributed Workflows",
    "topics": "git rebase, Interactive Rebase (-i), The Golden Rule of Rebasing, Remote Workflows, Pull Requests, Capstone Mini-Git CLI",
    "chapters": [
        {
            "title": "Chapter 9.1 — Git Rebase Fundamentals: Replaying Commits Onto a New Base, Linearizing Commit History",
            "body": """Git me do branches ko synchronize karne ke do distinct architectural approaches hote hain: `git merge` aur `git rebase`. Dono ka end result code level pe identical hota hai, lekin commit history ka topology completely alag hota hai.

Rebase ka mental model samjho:
Jab tum `git checkout feature && git rebase main` run karte ho, Git teen steps perform karta hai:
1. Common Ancestor (Merge Base) dhoondhta hai.
2. `feature` branch ke saare unique commits ko temporarily memory me 'shelve' karta hai (as patches).
3. `feature` branch ke base pointer ko reset karke `main` branch ke latest commit tip pe le jata hai.
4. Shelved commits ko ek-ek karke `main` ke tip pe dobara 'replay' karta hai!

CRITICAL HASH INVARIANT:
Kyunki har commit ka parent pointer badal gaya (pehle parent purana commit tha, ab parent `main` ka latest commit hai), har commit ka SHA-1 hash COMPLETELY REGENERATE hota hai! Rebase purane commits ko modify nahi karta — ye brand new commits create karta hai with new timestamps and new parent hashes!

[DIAGRAM: rebase_replay]

Code: Linearizing Commit History via Git Rebase
```bash
# Branch topology before rebase:
# main:    C1 -> C2
# feature: C1 -> C3 -> C4

$ git switch feature
$ git rebase main
First, rewinding head to replay your work on top of it...
Applying: feat: add payment validation
Applying: feat: add stripe webhooks

# Branch topology after rebase:
# main:    C1 -> C2
# feature: C1 -> C2 -> C3' -> C4' (Perfect straight line!)
```"""
        },
        {
            "title": "Chapter 9.2 — Interactive Rebase (git rebase -i): Squashing, Fixups, Rewording, and Dropping Commits",
            "body": """Development ke dauran developers aksar chhote, messy commits create karte hain: 'fix typo', 'wip test', 'oops forgot file'. Pull Request merge karne se pehle history ko clean, atomic commits me condense karna enterprise standard hai. Iske liye `git rebase -i` (Interactive Rebase) use hota hai.

Interactive Rebase Command Palette:
• `pick` (`p`): Commit ko as-is preserve karo.
• `reword` (`r`): Commit content preserve karo, lekin commit message edit karo.
• `edit` (`e`): Rebase ko is commit pe pause karo taaki tum files modify kar sako.
• `squash` (`s`): Commit ko previous commit me merge kar do AUR dono ke commit messages ko combine karo.
• `fixup` (`f`): Commit ko previous commit me merge kar do LEKIN iska commit message discard kar do! (Best for typo fixes).
• `drop` (`d`): Commit ko history se permanently delete kar do!

Code: Performing Interactive Rebase
```bash
# Last 3 commits ko interactively rebase karo:
$ git rebase -i HEAD~3

# Git tumhare default editor me ye TODO sheet kholega:
# -------------------------------------------------------------
# pick 4b825dc feat(auth): implement token validation
# f 8c2d110 fix typo in token error message      <-- 'f' for fixup!
# r e4f2b90 feat(auth): add logout endpoint      <-- 'r' for reword!
# -------------------------------------------------------------
# Save aur close karo. Git automatically cleanly condense kar dega!
```"""
        },
        {
            "title": "Chapter 9.3 — The Golden Rule of Rebasing: Never Rebase Commits That Have Been Pushed to Public Remotes",
            "body": """Git engineering me ek absolute rule hai jise 'The Golden Rule of Rebasing' kehte hain.

THE GOLDEN RULE:
NEVER rebase commits that have already been pushed to a public / shared remote branch!

Kyun?
Kyunki rebase purane commits ko discard karke naye hashes ke sath fresh commits generate karta hai. Agar kisi doosre developer ne tumhare purane commits pull kar liye the, aur tumne remote branch rebase karke force push kar di:
1. Unka local DAG aur remote DAG diverge ho jayega.
2. Jab wo pull karenge, Git duplicate commits create kar dega.
3. Merge conflicts ka massive loop start ho jayega.

Rule of Thumb:
• Local private feature branch pe: Rebase FREELY use karo taaki history pristine clean rahe.
• Shared public branch pe (`main`, `develop`): STRICTLY `git merge` use karo."""
        },
        {
            "title": "Chapter 9.4 — Remote Operations: git remote, git fetch vs git pull (--rebase), git push (--force-with-lease)",
            "body": """Distributed workflow me remote repositories ke sath synchronize karne ke liye core primitives:

`git fetch` vs `git pull`:
• `git fetch`: Remote se naye objects aur branch pointers download karta hai (`origin/main`), lekin tumhari local working tree ya branch ko touch nahi karta! 100% safe diagnostic command.
• `git pull`: `git fetch` + `git merge origin/main` in one shot!

Enterprise Pull Invariant:
Modern teams me `git pull --rebase` recommend kiya jata hai taaki har pull pe ugly 'Merge branch main into feature' commits create na hon.

The Danger of Force Push (--force-with-lease):
Kabhi bhi blind `git push -f` mat chalao! Agar kisi teammate ne tumhare push karne se pehle branch pe koi commit push kiya tha, `-f` unka kaam permanently wipe kar dega.
Hamesha use karo:
`git push --force-with-lease`
Ye GitHub remote ko check karta hai: agar remote pe koi unexpected new commit hai, push immediately reject ho jayega!

[DIAGRAM: remote_sync]

Code: Enterprise Remote Synchronization Protocol
```bash
# Remote inspect karo:
$ git remote -v
origin  git@github.com:enterprise/service.git (fetch)
origin  git@github.com:enterprise/service.git (push)

# Safe pull with rebase:
$ git pull --rebase origin main

# Safe atomic force-push after clean rebase:
$ git push --force-with-lease origin feature/auth
```"""
        },
        {
            "title": "Chapter 9.5 — Enterprise Collaborative Workflows: GitHub Flow vs Trunk-Based Development vs Gitflow",
            "body": """Enterprise software engineering me teen primary branching models dominate karte hain:

1. GitHub Flow (Lightweight & Continuous Deployment):
   • Single permanent branch: `main` (hamesha production-ready deployable).
   • Har feature ke liye short-lived branch (`feature/user-profile`).
   • Pull Request (PR) open karo, peer review aur automated CI tests pass karo.
   • Squash-and-merge into `main`, immediately deploy to production.

2. Trunk-Based Development (High Velocity Tech Companies - Google/Meta):
   • Saare developers direct `main` (trunk) pe commits push karte hain ya extremely short-lived PRs (< 24 hours).
   • Feature Flags (Toggles) use hote hain uncompleted features ko production me hide karne ke liye. Zero long-lived branches!

3. Gitflow (Traditional Scheduled Release Cycles):
   • Permanent branches: `master`, `develop`.
   • Supporting branches: `feature/*`, `release/*`, `hotfix/*`.
   • Heavy merge overhead, but useful for strict versioned binary releases."""
        }
    ],
    "challenges": {
        "c1": {
            "title": "CHALLENGE 9.1 — REBASE VS MERGE TOPOLOGY & COMMIT HASH DIVERGENCE TRACE",
            "prompt": "Given main with C1->C2, and feature with C1->C3->C4. Compare Case A (git merge main) versus Case B (git rebase main). Predict commit count, commit hashes, parentage pointers, and explain why rebasing pushed public branches causes upstream collision disasters.",
            "solution_title": "Solution 9.1: Rebase vs Merge Topological Divergence Trace",
            "solution_code": """# Topology Setup:
# main:    C1 ---> C2
# feature: C1 ---> C3 ---> C4

# Case A: git checkout feature && git merge main
# Resulting Commits on feature: 4 commits (C1, C3, C4, C_merge)
# Hashes of C3 and C4: PRESERVED intact.
# Parentage of tip (C_merge): TWO PARENTS (parent 1 = C4, parent 2 = C2).
# History graph: Non-linear diamond topology.

# Case B: git checkout feature && git rebase main
# Resulting Commits on feature: 4 commits (C1, C2, C3', C4')
# Hashes of C3 and C4: REPLACED by brand new hashes C3' and C4'!
# Parentage of tip (C4'): ONE PARENT (C4' -> C3' -> C2 -> C1).
# History graph: 100% linear chain.

# Disaster Analysis:
# If C3 and C4 were already pushed to origin, remote still has original C3 and C4.
# After rebase, local has C3' and C4'. When another teammate pushes or pulls,
# Git sees divergent histories with identical diffs, creating duplicate commits:
# C1 -> C2 -> C3 -> C4 -> C3' -> C4' and triggering merge hell."""
        },
        "c2": {
            "title": "CHALLENGE 9.2 — ALGORITHM: INTERACTIVE REBASE PLAN ENGINE",
            "prompt": "Implement rebase_executor(commits: list[dict], plan: list[tuple[str, str]]) -> list[dict] in pure Python. Support commands pick, squash, fixup, reword, drop. When squash/fixup occurs, combine commit diffs and manage commit messages. Regenerate commit hashes sequentially.",
            "solution_title": "Solution 9.2: Pure Python Interactive Rebase Plan Engine",
            "solution_code": """import hashlib
from typing import List, Tuple, Dict, Any

def rebase_executor(commits: List[Dict[str, Any]], plan: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
    \"\"\"Simulates git rebase -i execution across a list of commit dictionaries.\"\"\"
    rebased: List[Dict[str, Any]] = []

    for action, target_sha in plan:
        commit = next((c for c in commits if c["sha"] == target_sha), None)
        if not commit:
            continue

        if action == "drop":
            continue

        elif action == "pick":
            rebased.append(commit.copy())

        elif action == "reword":
            new_commit = commit.copy()
            new_commit["message"] = f"[REWORDED] {commit['message']}"
            rebased.append(new_commit)

        elif action in ("squash", "fixup"):
            if not rebased:
                raise ValueError(f"Cannot {action} without a preceding commit.")
            prev = rebased[-1]
            # Combine diff changes
            prev["diff"] += f"\\n{commit['diff']}"
            if action == "squash":
                prev["message"] += f"\\n\\nSquashed: {commit['message']}"
            # fixup leaves prev['message'] unchanged!

    # Regenerate hashes sequentially
    parent_sha = "0000000"
    for c in rebased:
        payload = f"tree:{c['diff']} parent:{parent_sha} msg:{c['message']}".encode("utf-8")
        c["sha"] = hashlib.sha1(payload).hexdigest()[:7]
        parent_sha = c["sha"]

    return rebased

# Test:
sample_commits = [
    {"sha": "c1", "message": "feat: user login", "diff": "+login()"},
    {"sha": "c2", "message": "fix typo", "diff": "+fix_typo"},
    {"sha": "c3", "message": "wip docs", "diff": "+readme"},
]
plan = [
    ("pick", "c1"),
    ("fixup", "c2"),  # Combines into c1, drops message
    ("reword", "c3"), # Keeps c3, updates message
]
result = rebase_executor(sample_commits, plan)
print(f"Rebase Result ({len(result)} commits):")
for r in result:
    print(f"  [{r['sha']}] {r['message']}")"""
        },
        "c3": {
            "title": "CHALLENGE 9.3 — INDUSTRIAL MINI-PROJECT: COMPLETE ZERO-DEPENDENCY MINI-GIT CLI (pygit)",
            "prompt": "Implement a fully functional zero-dependency mini-Git CLI pygit.py in Python supporting init, hash-object, cat-file, write-tree, commit-tree, and log. Must read and write standard zlib-compressed objects and traverse parentage pointers.",
            "solution_title": "Solution 9.3: Capstone Zero-Dependency Mini-Git CLI Engine (pygit.py)",
            "solution_code": """#!/usr/bin/env python3
\"\"\"pygit.py — Standalone Zero-Dependency Git Engine Implementation.\"\"\"
import os
import sys
import zlib
import hashlib
import time
from pathlib import Path

def get_git_dir() -> Path:
    cur = Path(".").resolve()
    while cur != cur.parent:
        if (cur / ".git").is_dir():
            return cur / ".git"
        cur = cur.parent
    return Path(".git")

def cmd_init(args):
    repo = Path(args[0]) if args else Path(".")
    git_dir = repo / ".git"
    (git_dir / "objects").mkdir(parents=True, exist_ok=True)
    (git_dir / "refs" / "heads").mkdir(parents=True, exist_ok=True)
    (git_dir / "HEAD").write_text("ref: refs/heads/main\\n")
    print(f"Initialized empty Git repository in {git_dir}")

def hash_object_data(obj_type: str, data: bytes, write: bool = False) -> str:
    header = f"{obj_type} {len(data)}\\x00".encode("ascii")
    payload = header + data
    sha1 = hashlib.sha1(payload).hexdigest()
    if write:
        git_dir = get_git_dir()
        obj_path = git_dir / "objects" / sha1[:2] / sha1[2:]
        obj_path.parent.mkdir(parents=True, exist_ok=True)
        obj_path.write_bytes(zlib.compress(payload))
    return sha1

def cmd_hash_object(args):
    write = "-w" in args
    files = [a for a in args if a != "-w"]
    for f in files:
        data = Path(f).read_bytes()
        sha = hash_object_data("blob", data, write=write)
        print(sha)

def cmd_cat_file(args):
    if len(args) < 2 or args[0] != "-p":
        print("Usage: pygit cat-file -p <sha>")
        return
    sha = args[1]
    git_dir = get_git_dir()
    obj_path = git_dir / "objects" / sha[:2] / sha[2:]
    raw = zlib.decompress(obj_path.read_bytes())
    _, _, body = raw.partition(b"\\x00")
    sys.stdout.buffer.write(body)

def cmd_write_tree(args):
    git_dir = get_git_dir()
    entries = []
    for root, dirs, files in os.walk("."):
        if ".git" in root:
            continue
        for f in files:
            p = Path(root) / f
            data = p.read_bytes()
            sha = hash_object_data("blob", data, write=True)
            rel = str(p).lstrip("./")
            entries.append(f"100644 blob {sha}\\t{rel}")
    tree_data = "\\n".join(sorted(entries)).encode("utf-8")
    tree_sha = hash_object_data("tree", tree_data, write=True)
    print(tree_sha)

def cmd_commit_tree(args):
    tree_sha = args[0]
    parent_sha = None
    msg = "Default commit message"
    i = 1
    while i < len(args):
        if args[i] == "-p":
            parent_sha = args[i+1]
            i += 2
        elif args[i] == "-m":
            msg = args[i+1]
            i += 2
        else:
            i += 1
    lines = [f"tree {tree_sha}"]
    if parent_sha:
        lines.append(f"parent {parent_sha}")
    lines.append(f"author Sparsh <sparsh@enterprise.io> {int(time.time())} +0000")
    lines.append(f"committer Sparsh <sparsh@enterprise.io> {int(time.time())} +0000")
    lines.append("")
    lines.append(msg)
    lines.append("")
    commit_sha = hash_object_data("commit", "\\n".join(lines).encode("utf-8"), write=True)
    # Update HEAD ref
    git_dir = get_git_dir()
    (git_dir / "refs" / "heads" / "main").write_text(commit_sha + "\\n")
    print(commit_sha)

def main():
    if len(sys.argv) < 2:
        print("pygit — Zero-Dependency Git CLI\\nCommands: init, hash-object, cat-file, write-tree, commit-tree")
        return
    cmd = sys.argv[1]
    args = sys.argv[2:]
    cmds = {
        "init": cmd_init,
        "hash-object": cmd_hash_object,
        "cat-file": cmd_cat_file,
        "write-tree": cmd_write_tree,
        "commit-tree": cmd_commit_tree,
    }
    if cmd in cmds:
        cmds[cmd](args)
    else:
        print(f"Unknown command: {cmd}")

if __name__ == "__main__":
    main()"""
        }
    }
}

APPENDICES = [
    {
        "title": "Appendix A — Git Plumbing & Object Database Internals",
        "scope": "The 4 Object Types (Blobs, Trees, Commits, Annotated Tags), zlib Compression, git cat-file, Packed Refs, and Packfile Garbage Collection",
        "body": """Git ke commands do categories me divide hote hain:
1. Porcelain Commands: High-level user-facing commands (jaise `git add`, `git commit`, `git checkout`, `git branch`).
2. Plumbing Commands: Low-level engine primitives (jaise `git hash-object`, `git cat-file`, `git mktree`, `git write-tree`, `git commit-tree`).

The 4 Object Types in Git Database:
Git ke `.git/objects/` database me exactly 4 types ke objects store hote hain:
• Blob: Raw file contents store karta hai. Filename, permissions, aur timestamps blob me store NAHI hote — sirf pure file bytes!
• Tree: Directory hierarchy represent karta hai. Tree ke andar filename, file mode (`100644` for files, `100755` for executables, `040000` for subdirectories), aur unke corresponding blob/tree SHA-1 hashes hote hain.
• Commit: Top-level snapshot pointer. Isme tree object ka SHA-1, parent commit ka SHA-1, author info, committer info, timestamp, aur commit message hota hai.
• Annotated Tag: Permanent release pointer with PGP signatures and tagger notes.

Packfiles & Garbage Collection (`git gc`):
Jab repository purani hoti hai aur hazaron loose objects accumulate ho jate hain, Git unhe compact karta hai. Loose objects ko single binary `.pack` file me assemble karta hai aur sliding-window delta compression apply karta hai. Isse repository size 80-90% shrink ho jata hai!

Code: Low-Level Plumbing Inspection
```bash
# Object ka type inspect karo:
$ git cat-file -t 4b825dc
commit

# Object ka size in bytes:
$ git cat-file -s 4b825dc
246

# Object ka pretty-printed content:
$ git cat-file -p 4b825dc
tree 8c2d110f...
parent 19a8f21e...
author Sparsh <sparsh@enterprise.io> 1760100000 +0530
committer Sparsh <sparsh@enterprise.io> 1760100000 +0530

feat(auth): implement token validation
```"""
    },
    {
        "title": "Appendix B — The Catastrophe Recovery Gauntlet",
        "scope": "git reflog Navigation, Recovering Deleted Branches, Dangling Commits Recovery via git fsck --lost-found, and Fixing Accidental Force Pushes",
        "body": """Git me virtually nothing is truly lost jab tak garbage collection (`git gc`) 30 se 90 din baad execute na ho. Even if you accidentally deleted your entire feature branch or executed `git reset --hard HEAD~10`, Git keeps an internal audit ledger: **The Reflog**.

What is git reflog?
Reflog (`Reference Log`) har us point ko record karta hai jahan tumhare local repository me HEAD ya koi branch pointer move hua tha. Chahe wo commit ho, checkout ho, rebase ho, ya hard reset ho!

Catastrophe 1: Accidentally Deleted Unmerged Branch
```bash
# Disaster:
$ git branch -D feature/critical-architecture
Deleted branch feature/critical-architecture (was 7e2d9a1).

# Recovery via Reflog:
$ git reflog | head -n 5
7e2d9a1 HEAD@{0}: checkout: moving from feature/critical-architecture to main
7e2d9a1 HEAD@{1}: commit: implement distributed raft consensus

# Instantly resurrect branch:
$ git branch feature/critical-architecture 7e2d9a1
# Branch 100% restored with zero data loss!
```

Catastrophe 2: Accidental `git reset --hard`
```bash
# Disaster: Accidental reset destroyed last 5 commits:
$ git reset --hard HEAD~5

# Recovery:
$ git reflog
4b825dc HEAD@{0}: reset: moving to HEAD~5
8f12a90 HEAD@{1}: commit: feat: caching layer # This was the latest commit!

$ git reset --hard 8f12a90 # Boom! Back to future!
```

Catastrophe 3: Dangling Object Rescue via `git fsck`
Agar reflog bhi expire ho jaye, `git fsck --lost-found` database scan karta hai aur saare unreferenced blobs aur commits ko `.git/lost-found/` folder me recover kar deta hai."""
    },
    {
        "title": "Appendix C — 30 FAANG Version Control Machine Coding & Scenario Questions",
        "scope": "Top 30 Tier-1 Architecture, Distributed Systems, Monorepo Scale, and Machine Coding Problems with Detailed Solutions",
        "body": """FAANG Interview Scenario Masterclass:

Q1: What are the engineering tradeoffs between Mono-repo and Poly-repo architecture at scale?
Answer:
• Mono-repo (Google Piper, Meta): Single atomic commits cross-service refactorings execute kar sakte hain; dependency diamond problem eliminate ho jati hai. Lekin extreme tooling scale require karta hai (sparse-checkout, virtual file systems jaise VFS for Git, custom distributed build systems jaise Bazel).
• Poly-repo: Clear microservice ownership boundary aur fast clone speed. Lekin cross-service contracts update karna multiple synchronized PRs require karta hai aur version drift common hota hai.

Q2: How does Git prevent SHA-1 collision attacks in modern versions?
Answer:
Git 2.13+ uses 'Sha1DC' (SHA-1 Collision Detection library). Ye incoming objects ko inspect karta hai specific cryptographic patterns ke liye jo known collision generation techniques (jaise SHAttered) use karte hain. Agar collision detected hota hai, Git object write abort kar deta hai. Future Git versions transition kar rahe hain SHA-256 (Object Format 2).

Q3: What happens under the hood during a sparse checkout in massive enterprise repositories?
Answer:
`git sparse-checkout` Git ke index me `SKIP_WORKTREE` bit manipulate karta hai. Git working tree me sirf un directories aur files ko populate karta hai jo sparse-checkout pattern me defined hain, while internal index pura repository structure maintain karta hai.

Q4: Explain the difference between `git revert` and `git reset` on public branches.
Answer:
`git reset` commit pointers ko piche move karta hai aur historical commits ko discard karta hai (rewrites history — public branches pe strictly prohibited). `git revert` ek naya inverse commit create karta hai jo targeted commit ke changes ko reverse karta hai, without modifying existing commit history (safe for public branches).

Q5: Design a high-throughput pre-receive hook for enterprise branch protection.
Answer:
A pre-receive hook executes on the server receiving standard input: `<old-value> <new-value> <ref-name>`.
It enforces:
1. Reject zero-SHA deletions on protected branches (`refs/heads/main`).
2. Reject non-fast-forward push updates (disabling force push).
3. Validate GPG commit signatures using authorized public keyrings.
4. Verify Conventional Commit regex patterns."""
    }
]
