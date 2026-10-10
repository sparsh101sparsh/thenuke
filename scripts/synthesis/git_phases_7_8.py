"""Git Engineering Reference Manual — Phases 7 & 8 Content.
Strict 100% Roman Hinglish narrative, zero Devanagari, production-grade code.
"""

from typing import Dict, Any, List

PHASE_7 = {
    "number": 7,
    "title": "Merging Strategies & Conflict Resolution",
    "topics": "Fast-Forward Merge, Three-Way Merge, Common Ancestor (Merge Base), Conflict Markers, Resolution Workflow, git merge --abort",
    "chapters": [
        {
            "title": "Chapter 7.1 — Fast-Forward Merges: Linear History Extension When No Divergence Exists",
            "body": """Git me do branches ko combine karne ka sabse simple aur clean scenario 'Fast-Forward Merge' hota hai.

Fast-Forward kab hota hai?
Jab target branch (`main`) me koi naye commits create nahi hue hain us time se jab tumne `feature` branch fork ki thi! In other words, `main` branch ka commit pointer `feature` branch ke direct ancestral path me lie karta hai.

Is scenario me Git ko koi naya merge commit create karne ki zaroorat nahi padti! Git simply `main` branch ke pointer file ko slide karke `feature` branch ke latest commit SHA-1 pe point kar deta hai! History 100% linear rehti hai.

Code: Executing Fast-Forward Merge
```bash
# Main branch pe switch karo:
$ git switch main

# Feature branch ko merge karo:
$ git merge feature/login
Updating 4b825dc..8c2d110
Fast-forward # Notice: Fast-forward keyword! No merge commit created!
 src/auth.ts | 14 ++++++++++++++
 1 file changed, 14 insertions(+)
```

[RULE]
Disabling Fast-Forward (--no-ff):
Enterprise teams me aksar `--no-ff` flag enforce kiya jata hai:
`git merge --no-ff feature/login`
Isse Git explicitly ek naya Merge Commit create karta hai, jo ye historical record preserve karta hai ki ek feature branch exist karti thi aur kab merge hui."""
        },
        {
            "title": "Chapter 7.2 — Three-Way Merges: Recursive/Ort Strategy, Merge Commits with Two Parents, Finding the Merge Base",
            "body": """Jab dono branches me independent commits add ho chuke hon (divergent history), tab Fast-Forward mathematically impossible hota hai. Git ko 'Three-Way Merge' execute karna padta hai.

Three-Way Merge ke teen inputs kya hote hain:
1. OURS: Active branch (`main`) ka latest commit snapshot.
2. THEIRS: Incoming branch (`feature`) ka latest commit snapshot.
3. BASE (Merge Base): Dono branches ka Lowest Common Ancestor (LCA) commit snapshot!

Git sirf OURS aur THEIRS ko compare nahi karta (agar sirf do ko compare karega toh Git ko pata nahi chalega ki kis side ne modification ki aur kis side ne deletion ki). Git BASE ko benchmark banata hai:
• Agar BASE me line X thi, OURS me change hui, lekin THEIRS me unchanged hai: Git OURS ka change silently accept kar leta hai.
• Agar BASE me line X thi, THEIRS me change hui, lekin OURS me unchanged hai: Git THEIRS ka change silently accept kar leta hai.
• Lekin agar BASE ki same line dono ne differently change kar di, tab Merge Conflict trigger hota hai!

Git 2.34+ me default merge strategy **ORT** ('Ostensibly Recursive's Twin') hai, jo legacy recursive engine se 10x faster aur conflict resolution me significantly smarter hai.

[DIAGRAM: three_way_merge]

[MENTAL MODEL]
Three-Way Merge Commit Architecture:
Normal commits ka exactly 1 parent pointer hota hai (`parent <sha>`).
Merge commit ka exactly 2 parent pointers hote hain:
`parent <ours_sha>`
`parent <theirs_sha>`"""
        },
        {
            "title": "Chapter 7.3 — Merge Conflict Anatomy: Understanding Conflict Markers (<<<<<<<, =======, >>>>>>>)",
            "body": """Jab Git automatic 3-way merge reconcile nahi kar pata, Git merge process pause kar deta hai, terminal me error emit karta hai, aur conflict wali files ke andar standard Conflict Markers inject kar deta hai.

[DIAGRAM: merge_conflict]

Conflict Markers ka exact anatomy samjho:
```text
<<<<<<< HEAD
const API_TIMEOUT = 5000; // Tumhari current branch (main) ka code
=======
const API_TIMEOUT = 3000; // Incoming branch (feature) ka code
>>>>>>> feature/latency-tuning
```

Anatomy Breakdown:
• `<<<<<<< HEAD`: Start of conflict block. Iske neeche tumhari current checked-out branch ka content hota hai.
• `=======`: Dividing line (separator). Ye separate karta hai tumhare changes aur incoming changes ko.
• `>>>>>>> <branch-name>`: End of conflict block. Iske upar incoming branch ka content hota hai.

[ENGINEERING GOTCHA]
Production code me disastrous build failure tab aati hai jab developer jaldi-baazi me code fix kar deta hai lekin galti se `<<<<<<< HEAD` ya `=======` wali string file me chhod deta hai! JavaScript runtime ya Python interpreter syntax error throw karta hai: `SyntaxError: Unexpected token '<'`. Hamesha merge complete karne se pehle markers search karo."""
        },
        {
            "title": "Chapter 7.4 — Conflict Resolution Workflow: Editing Markers, git add to Mark Resolved, git merge --abort",
            "body": """Merge conflict resolve karne ka standard 4-step production workflow:

Step 1: Inspect Conflicted Files
`git status` run karo. Conflicted files `both modified:` heading ke under dikhai dengi.

Step 2: Manual Edit & Decision
File ko editor me kholo. Teeno options me se ek choose karo:
- Option A: Current branch ka code rakho.
- Option B: Incoming branch ka code rakho.
- Option C: Dono code ko combine karke ek naya logic design karo.
Saare `<<<<<<<`, `=======`, `>>>>>>>` markers manually delete karo.

Step 3: Stage Resolved Files
`git add <file>` run karo. Git ke liye `git add` ka matlab hai: 'Maine is file ke conflict markers resolve kar diye hain.'

Step 4: Conclude Merge
`git commit` run karo. Git automatically ek pre-populated merge commit message template open karega (`Merge branch 'feature' into main`). Save aur exit karo.

Safety Abort Invariant:
Agar merge ke time complications aa jayein aur tum pristine clean state pe wapas aana chaho:
`git merge --abort`
Ye working directory ko merge start hone se pehle wali exact state pe instantly restore kar deta hai!

Code: Merge Conflict Resolution Hands-On
```bash
# Conflict trigger hua:
$ git merge feature/timeout-patch
Auto-merging src/config.ts
CONFLICT (content): Merge conflict in src/config.ts
Automatic merge failed; fix conflicts and then commit the result.

# Check status:
$ git status
Unmerged paths:
  (use "git add <file>..." to mark resolution)
	both modified:   src/config.ts

# File resolve karne ke baad:
$ git add src/config.ts
$ git commit -m "merge: resolve API_TIMEOUT conflict between main and feature"
[main 9d2a4f1] merge: resolve API_TIMEOUT conflict between main and feature
```"""
        }
    ],
    "challenges": {
        "c1": {
            "title": "CHALLENGE 7.1 — 3-WAY MERGE CONFLICT MARKER RESOLUTION TRACE",
            "prompt": "Given BASE, OURS (main), and THEIRS (feat), predict exact working file content with conflict markers when both modify the same timeout configuration. Show full resolution code.",
            "solution_title": "Solution 7.1: Conflict Marker Injection & Resolution Trace",
            "solution_code": """# BASE snapshot:
# const TIMEOUT = 1000;

# OURS (main):
# const TIMEOUT = 5000; // extended for enterprise SLA

# THEIRS (feat):
# const TIMEOUT = 2000; // optimized for microsecond latency

# Predict working file content generated by Git:
<<<<<<< HEAD
const TIMEOUT = 5000; // extended for enterprise SLA
=======
const TIMEOUT = 2000; // optimized for microsecond latency
>>>>>>> feat

# Senior Engineer Resolution:
# Combine both requirements by extracting environment configuration:
const TIMEOUT = Number(process.env.APP_TIMEOUT) || 5000; // Configurable: defaults to 5000ms SLA with test override

# Complete Resolution Commands:
$ git add src/config.js
$ git commit -m "merge(config): resolve TIMEOUT conflict with environment override" """
        },
        "c2": {
            "title": "CHALLENGE 7.2 — ALGORITHM: 3-WAY TEXT MERGE ENGINE IN PYTHON",
            "prompt": "Implement three_way_merge(base: str, ours: str, theirs: str) -> tuple[bool, str] in pure Python. Return (True, merged_text) if non-conflicting changes are reconcilable. Return (False, conflicted_text_with_markers) if conflicting line edits are present.",
            "solution_title": "Solution 7.2: Pure Python Three-Way Text Merge Engine",
            "solution_code": """from typing import Tuple, List

def three_way_merge(base_str: str, ours_str: str, theirs_str: str) -> Tuple[bool, str]:
    \"\"\"Reconciles two divergent text branches against a common ancestor.\"\"\"
    base = base_str.splitlines()
    ours = ours_str.splitlines()
    theirs = theirs_str.splitlines()

    max_len = max(len(base), len(ours), len(theirs))
    merged_lines: List[str] = []
    has_conflict = False

    for i in range(max_len):
        b = base[i] if i < len(base) else None
        o = ours[i] if i < len(ours) else None
        t = theirs[i] if i < len(theirs) else None

        if o == t:
            # Both made same change or no change
            if o is not None:
                merged_lines.append(o)
        elif o == b:
            # Ours unchanged, accept theirs
            if t is not None:
                merged_lines.append(t)
        elif t == b:
            # Theirs unchanged, accept ours
            if o is not None:
                merged_lines.append(o)
        else:
            # Both modified line differently -> CONFLICT!
            has_conflict = True
            merged_lines.append("<<<<<<< HEAD")
            if o is not None:
                merged_lines.append(o)
            merged_lines.append("=======")
            if t is not None:
                merged_lines.append(t)
            merged_lines.append(">>>>>>> THEIRS")

    return (not has_conflict, "\\n".join(merged_lines))

# Verification test:
base_txt = "host = '127.0.0.1'\\nport = 8080\\ndebug = False"
ours_txt = "host = '127.0.0.1'\\nport = 9000\\ndebug = False" # ours changed port
theirs_txt = "host = '127.0.0.1'\\nport = 8080\\ndebug = True" # theirs changed debug

success, result = three_way_merge(base_txt, ours_txt, theirs_txt)
print("Merge Cleanly Succeeded?", success) # True!
print("Reconciled Content:\\n" + result)
# port = 9000 and debug = True both cleanly merged!"""
        },
        "c3": {
            "title": "CHALLENGE 7.3 — INDUSTRIAL MINI-PROJECT: TERMINAL MERGE RESOLVER TUI",
            "prompt": "Build an interactive terminal conflict resolver script git-resolve-cli. Scans repository files for '<<<<<<< HEAD' markers, presents an interactive menu [1] Keep Ours [2] Keep Theirs [3] Keep Both, writes resolution to disk, and stages via 'git add'.",
            "solution_title": "Solution 7.3: Interactive Terminal Merge Conflict Resolver",
            "solution_code": """import os
import re
import subprocess
from pathlib import Path

CONFLICT_PATTERN = re.compile(
    r"<<<<<<< HEAD\\n(.*?)\\n=======\\n(.*?)\\n>>>>>>> [^\\n]+\\n",
    re.DOTALL
)

def resolve_file(filepath: Path) -> bool:
    content = filepath.read_text(encoding="utf-8")
    matches = list(CONFLICT_PATTERN.finditer(content))
    if not matches:
        return False

    print(f"\\nResolving {len(matches)} conflict hunk(s) in: {filepath}")
    new_content = content

    for i, match in enumerate(matches, 1):
        ours_block = match.group(1)
        theirs_block = match.group(2)

        print(f"\\n--- Conflict #{i} ---")
        print(f"[Ours]:\\n{ours_block}")
        print(f"[Theirs]:\\n{theirs_block}")

        choice = input("Select: [1] Keep Ours  [2] Keep Theirs  [3] Keep Both: ").strip()
        if choice == "1":
            replacement = ours_block + "\\n"
        elif choice == "2":
            replacement = theirs_block + "\\n"
        else:
            replacement = ours_block + "\\n" + theirs_block + "\\n"

        new_content = new_content.replace(match.group(0), replacement, 1)

    filepath.write_text(new_content, encoding="utf-8")
    subprocess.run(["git", "add", str(filepath)], check=True)
    print(f"✅ Staged resolved file: {filepath}")
    return True

def run_resolver() -> None:
    # Find all conflicted files
    try:
        status_out = subprocess.check_output(["git", "status", "-s"], text=True)
    except subprocess.CalledProcessError:
        print("[ERROR] Not in a git repo.")
        return

    conflicted = []
    for line in status_out.splitlines():
        if line.startswith("UU ") or line.startswith("AA "):
            conflicted.append(Path(line[3:].strip()))

    if not conflicted:
        print("No active merge conflicts detected!")
        return

    for f in conflicted:
        resolve_file(f)

    print("\\nAll conflicts resolved! Run 'git commit' to complete merge transaction.")

if __name__ == "__main__":
    run_resolver()"""
        }
    }
}

PHASE_8 = {
    "number": 8,
    "title": "Advanced Working Tree Manipulation & Stashing",
    "topics": "git stash Stack, Stash Internals, git restore, Lightweight vs Annotated Tags, GPG Signing, Semantic Versioning",
    "chapters": [
        {
            "title": "Chapter 8.1 — Stashing Uncommitted Changes: git stash push, git stash pop vs apply, Inspecting the Stash Stack",
            "body": """Jab tum kisi feature branch pe half-baked work kar rahe ho aur production me critical P0 incident aa jaye, tum messy uncommitted code commit nahi karna chahte.

`git stash` ek LIFO (Last-In, First-Out) stack structure hai jisme tum apne uncommitted changes (both staged and unstaged) temporarily store kar sakte ho, working tree clean state pe reset kar sakte ho, aur incident fix karne ke baad wapas restore kar sakte ho.

Essential Stash Commands:
• `git stash push -m "WIP: auth token logic"`: Descriptively labeled snapshot stack me push karta hai.
• `git stash list`: Poori stash stack inspect karta hai (`stash@{0}`, `stash@{1}`).
• `git stash pop`: Latest stash (`stash@{0}`) apply karta hai AUR stack se remove karta hai.
• `git stash apply`: Stash apply karta hai LEKIN stack me preserve rakhta hai (safe retry option).
• `git stash drop stash@{1}`: Specific stash entry delete karta hai.
• `git stash clear`: Poori stack wipe kar deta hai.

Code: Stashing & Context Switching Protocol
```bash
# Feature work temporarily shelve karo:
$ git stash push -m "WIP: payment retry loop"
Saved working directory and index state On feature/pay: WIP: payment retry loop

# Inspect stack:
$ git stash list
stash@{0}: On feature/pay: WIP: payment retry loop
stash@{1}: On main: WIP: telemetry config

# Hotfix complete hone ke baad restore karo:
$ git stash pop
On branch feature/pay
Changes not staged for commit:
  modified:   src/payment.ts
Dropped refs/stash@{0} (d2e4f1a)
```"""
        },
        {
            "title": "Chapter 8.2 — Stashing Untracked Files (-u) and Stash Branching: Safely Context-Switching in Mid-Feature",
            "body": """Sabse common developer shock:
'Maine git stash kiya, lekin meri nayi banayi hui files abhi bhi working tree me padi hain!'

Gotcha ye hai ki default `git stash` sirf TRACKED files ko stash karta hai! Agar tumne 5 nayi files create ki theen jo abhi tak `git add` nahi hui theen, wo untracked files disk pe hi reh jayengi.

Untracked files ko stash karne ke liye mandatory flag:
`git stash -u` (ya `git stash --include-untracked`)

Stash Branching:
Agar stashed changes itne complex the ki wo target branch pe cleanly apply nahi ho rahe, tum unhe direct nayi branch me materialize kar sakte ho:
`git stash branch <new-branch-name> stash@{0}`"""
        },
        {
            "title": "Chapter 8.3 — Undoing Changes in the Modern Era: git restore (--staged vs working tree) vs Legacy git checkout",
            "body": """Git 2.23+ me file undoing operations ko completely modernize kiya gaya `git restore` ke through.

The Modern Restore Invariants:
1. Discard Unstaged Changes in Working Tree:
   `git restore <file>`
   File ko Index (ya HEAD) ke latest state pe reset karta hai. Working tree ke unsaved modifications permanently wipe ho jate hain!
2. Unstage Files from Index back to Working Tree:
   `git restore --staged <file>`
   (Legacy `git reset HEAD <file>` ka clean alternative). File ko staging area se nikalta hai lekin disk pe tumhara code 100% untouched rehta hai!

[DIAGRAM: reset_matrix]

Code: Modern Undoing Operations
```bash
# Scenario 1: Galti se git add . kar diya:
$ git add .
# Safely unstage all without losing single character of work:
$ git restore --staged .

# Scenario 2: Bad edits in a single file discard karo:
$ git restore src/broken_experiment.ts
```"""
        },
        {
            "title": "Chapter 8.4 — Git Tags & Semantic Releases: Lightweight Tags vs Annotated Tags (git tag -a -m), GPG Signing",
            "body": """Git me Tags release checkpoints (v1.0.0, v2.1.4) mark karne ke liye use hote hain.

Two Types of Tags Invariant:
1. Lightweight Tag: Sirf ek 41-byte pointer file jo `.git/refs/tags/` me commit hash store karti hai (like a branch that never moves).
   `git tag v1.0.0`
2. Annotated Tag: Full Git object database object jisme tagger name, email, timestamp, PGP cryptographic signature, aur release notes message store hota hai! Production releases me strictly Annotated Tags use karne chahiye:
   `git tag -a v1.0.0 -m "Release version 1.0.0 — Production LTS"`

Pushing Tags Invariant:
Default `git push` tags ko remote pe push NAHI karta! Tags ko explicitly push karna padta hai:
`git push origin v1.0.0` ya `git push origin --tags`

Code: Managing Production Semantic Release Tags
```bash
# Create signed annotated tag:
$ git tag -a v2.4.0 -m "Release v2.4.0: High-performance caching engine"

# Inspect tag object metadata:
$ git show v2.4.0
tag v2.4.0
Tagger: Sparsh <sparsh@enterprise.io>
Date:   Sat Oct 10 16:00:00 2026 +0530

Release v2.4.0: High-performance caching engine
-----
commit 4b825dc...
```"""
        }
    ],
    "challenges": {
        "c1": {
            "title": "CHALLENGE 8.1 — GIT STASH STACK & UNTRACKED FILES TRACE",
            "prompt": "Trace working directory and stash list state when developer modifies tracked file, creates untracked .env file, runs git stash push without -u, and then runs git stash push -u. Predict exact output of git stash list and pop behavior.",
            "solution_title": "Solution 8.1: Stash Stack & Untracked Files Lifecycle Trace",
            "solution_code": """# Trace Step-by-Step:
$ echo "tracked mod" >> app.js
$ echo "secret key" > .env  # Untracked

# 1. Stash without -u:
$ git stash push -m "WIP 1"
# app.js is stashed and reverted to HEAD state.
# .env is UNTOUCHED! Still sitting untracked on disk!
$ git status -s
?? .env

# 2. Stash with -u:
$ git stash push -u -m "WIP 2 with secrets"
# .env is now safely stashed into stash object tree!
# Working directory is 100% pristine clean!

# 3. Predict git stash list:
$ git stash list
stash@{0}: On main: WIP 2 with secrets   # Latest pushed
stash@{1}: On main: WIP 1

# 4. Pop specific stash:
$ git stash pop stash@{1}
# Restores 'WIP 1'. stash@{0} remains in the stack."""
        },
        "c2": {
            "title": "CHALLENGE 8.2 — ALGORITHM: WORKTREE STASH STACK ENGINE",
            "prompt": "Implement GitStashManager in pure Python. Manage LIFO stack with push(diff, untracked, msg), pop(index=0), apply(index=0), and list_stashes(). Zero external dependencies with O(1) push and pop.",
            "solution_title": "Solution 8.2: Pure Python Stash Stack Engine",
            "solution_code": """from dataclasses import dataclass
from typing import List, Dict, Optional
import time

@dataclass
class StashEntry:
    index: int
    message: str
    timestamp: float
    diff: str
    untracked_files: Dict[str, str]

class GitStashManager:
    \"\"\"LIFO stack engine simulating Git Stash architecture.\"\"\"
    def __init__(self):
        self._stack: List[StashEntry] = []

    def push(self, diff: str, untracked: Optional[Dict[str, str]] = None, message: str = "WIP") -> int:
        entry = StashEntry(
            index=0, # Will be indexed dynamically
            message=message,
            timestamp=time.time(),
            diff=diff,
            untracked_files=untracked or {}
        )
        self._stack.insert(0, entry) # Insert at head of LIFO
        return len(self._stack)

    def list_stashes(self) -> List[str]:
        output = []
        for idx, entry in enumerate(self._stack):
            output.append(f"stash@{{{idx}}}: {entry.message}")
        return output

    def pop(self, index: int = 0) -> StashEntry:
        if index >= len(self._stack):
            raise IndexError(f"Stash index {index} out of range.")
        return self._stack.pop(index)

    def apply(self, index: int = 0) -> StashEntry:
        if index >= len(self._stack):
            raise IndexError(f"Stash index {index} out of range.")
        return self._stack[index] # Preserves in stack

# Test verification:
sm = GitStashManager()
sm.push("diff --git a/app.py", {"config.json": "{}"}, "WIP: payment v1")
sm.push("diff --git a/server.py", {}, "WIP: metrics v2")
print("Stash List:\\n", "\\n".join(sm.list_stashes()))
# stash@{0}: WIP: metrics v2
# stash@{1}: WIP: payment v1
popped = sm.pop(0)
print(f"Popped stash: {popped.message}")"""
        },
        "c3": {
            "title": "CHALLENGE 8.3 — INDUSTRIAL MINI-PROJECT: SEMANTIC RELEASE & ANNOTATED TAG GENERATOR",
            "prompt": "Build an automated release tool git-semver-release in Python. Walks commit history since latest annotated tag, parses Conventional Commits (feat -> minor, fix -> patch, BREAKING CHANGE -> major), creates annotated tag, and generates Markdown changelog.",
            "solution_title": "Solution 8.3: Automated Semantic Versioning Release Engine",
            "solution_code": """import subprocess
import re
from typing import Tuple, List

def calculate_next_version(current_tag: str, commits: List[str]) -> Tuple[str, str]:
    # Parse current tag (e.g., 'v1.4.2')
    match = re.match(r"^v?(\\d+)\\.(\\d+)\\.(\\d+)$", current_tag)
    if not match:
        major, minor, patch = 0, 1, 0
    else:
        major, minor, patch = map(int, match.groups())

    bump = "patch"
    changelog_entries = []

    for c in commits:
        changelog_entries.append(f"- {c}")
        if "BREAKING CHANGE" in c or "!" in c.split(":")[0]:
            bump = "major"
        elif c.startswith("feat") and bump != "major":
            bump = "minor"

    if bump == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump == "minor":
        minor += 1
        patch = 0
    else:
        patch += 1

    next_version = f"v{major}.{minor}.{patch}"
    changelog = f"# Release {next_version}\\n\\n" + "\\n".join(changelog_entries)
    return next_version, changelog

def create_release():
    # 1. Fetch latest tag
    try:
        latest_tag = subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"], text=True).strip()
    except subprocess.CalledProcessError:
        latest_tag = "v0.0.0"

    # 2. Get commit subjects since latest tag
    commit_range = f"{latest_tag}..HEAD" if latest_tag != "v0.0.0" else "HEAD"
    commits = subprocess.check_output(["git", "log", commit_range, "--pretty=format:%s"], text=True).splitlines()

    if not commits:
        print("No new commits since last release!")
        return

    next_ver, notes = calculate_next_version(latest_tag, commits)
    print(f"Bumping version from {latest_tag} -> {next_ver}")
    print("\\nRelease Notes:\\n", notes)

    # 3. Create annotated tag
    subprocess.run(["git", "tag", "-a", next_ver, "-m", notes], check=True)
    print(f"✅ Successfully created annotated tag {next_ver}!")

if __name__ == "__main__":
    create_release()"""
        }
    }
}
