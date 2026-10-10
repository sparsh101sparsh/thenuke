"""Git Engineering Reference Manual — Phases 5 & 6 Content.
Strict 100% Roman Hinglish narrative, zero Devanagari, production-grade code.
"""

from typing import Dict, Any, List

PHASE_5 = {
    "number": 5,
    "title": "History Inspection & Diffing Engine",
    "topics": "git log Formatting, Revision Walk, Commit Ranges, git diff Engine, git show, git blame",
    "chapters": [
        {
            "title": "Chapter 5.1 — Navigating History: git log Flags (--oneline, --graph, --decorate, --stat, -p)",
            "body": """Git me commit history sirf ek flat list nahi hai — ye ek Directed Acyclic Graph (DAG) hai jisme branches fork hoti hain aur merge hoti hain. Default `git log` command terminals me bahut verbose aur overwhelming lagti hai. Senior engineers specific diagnostic flags use karke exact signal extract karte hain.

Diagnostic Flags Checklist:
• `--oneline`: Har commit ko ek single compact line me abbreviate karta hai (7-character short SHA-1 + subject).
• `--graph`: Terminal me ASCII art branching tree render karta hai (`*`, `|\\`, `|/`).
• `--decorate`: Batata hai ki branch pointers (`HEAD -> main`, `origin/feat`) kaunse commit pe point kar rahe hain.
• `--stat`: Har commit me changed files, insertions count, aur deletions count ki numerical summary deta hai.
• `-p` (Patch): Actual line-by-line diff content print karta hai.
• `-n <count>`: Output ko last N commits tak limit karta hai.
• `--author="Sparsh"`: Specific developer ke commits filter karta hai.
• `--since="2.weeks.ago"`: Time-based audit filter lagata hai.

Code: High-Signal Git Log Commands
```bash
# Production status inspection:
$ git log --oneline --graph --decorate -n 5
* 4b825dc (HEAD -> main, origin/main) feat(auth): add OAuth2 refresh loop
* 19a8f21 fix(db): close idle connection on client abort
| * 8c2d110 (origin/feature-search) feat(search): implement trie lookup
|/  
* e4f2b90 chore: upgrade node to LTS v20.12.0

# Numerical commit change impact inspect karo:
$ git log -1 --stat
commit 4b825dc642cb6eb9a060e54bf8d69288fbee4904
Author: Sparsh <sparsh@enterprise.io>
Date:   Sat Oct 10 14:22:10 2026 +0530

    feat(auth): add OAuth2 refresh loop

 src/auth/token.service.ts | 42 +++++++++++++++++++++++++++++++++---------
 src/auth/token.spec.ts    | 18 ++++++++++++++++++
 2 files changed, 51 insertions(+), 9 deletions(-)
```

[MENTAL MODEL]
Git Log DAG Traversal:
Git commit history ko reverse topological order me traverse karta hai. HEAD se start karke parent pointers ko walk karta hai jab tak root commit (jiska parent NULL hai) na mil jaye."""
        },
        {
            "title": "Chapter 5.2 — Inspecting Diffs: git diff (Working Tree vs Index) vs git diff --staged (Index vs HEAD)",
            "body": """`git diff` command ka purpose do tree structures ke beech ka cryptographic delta compute karna hai. Sabse common developer mistake ye hoti hai ki wo bina flags ke `git diff` chalate hain aur unhe staged changes nahi dikhte!

The Two Diff Modes Invariant:
1. `git diff` (Unstaged Diff):
   Compares **Working Tree** against **Index (Staging Area)**.
   Ye batata hai: 'Maine staging karne ke baad disk pe kya naya code likha hai jo abhi tak `git add` nahi hua?'
2. `git diff --staged` ya `git diff --cached`:
   Compares **Index (Staging Area)** against **HEAD (Last Commit)**.
   Ye batata hai: 'Agar main abhi `git commit` maru, toh agle commit me kaunse exact lines include honge?'

Code: Diff Target Comparison Protocol
```bash
# Scenario: Staged change vs Unstaged change
$ git diff          # Nothing printed! Kyunki sab staged hai!

# Correct command for staged inspection:
$ git diff --staged
diff --git a/src/cache.ts b/src/cache.ts
index a1b2c3d..e5f6g7h 100644
--- a/src/cache.ts
+++ b/src/cache.ts
@@ -10,3 +10,5 @@ export class MemoryCache {
+    // Staged addition:
+    private lruList: DoublyLinkedList = new DoublyLinkedList();
```"""
        },
        {
            "title": "Chapter 5.3 — Comparing Branches and Commits: Double-Dot (..) vs Triple-Dot (...) Range Semantics",
            "body": """Git commit range queries me double-dot (`..`) aur triple-dot (`...`) ka behavior fundamentally different hota hai. Ye FAANG technical screen ka favorite question hai.

1. Double-Dot Range (`A..B`): Set Difference
   Reachable from B, but NOT reachable from A (`B - A`).
   Example: `git log main..feature`
   Ye un saare commits ko list karta hai jo `feature` branch pe hain lekin `main` branch me nahi hain.
   Diff context me: `git diff A..B` seedha commit A aur commit B ke tree states ko compare karta hai.

2. Triple-Dot Range (`A...B`): Symmetric Difference
   Commits that are reachable from either A OR B, but NOT from both!
   Diff context me (CRITICAL): `git diff main...feature`
   Diff me triple-dot ka behavior completely change ho jata hai:
   `git diff A...B` commit B ko commit A se compare nahi karta — balki commit B ko A aur B ke **Lowest Common Ancestor (Merge Base)** se compare karta hai!
   Ye exactly wahi diff hai jo GitHub Pull Request page pe dikhata hai!

[MENTAL MODEL]
       C1 --- C2 --- C3 (main)
      /
C0 ---
      \\
       D1 --- D2 (feature)

Merge Base = C0.
`git diff main..feature` compares C3 vs D2 (includes main's C1, C2, C3 changes as reversals).
`git diff main...feature` compares C0 vs D2 (shows ONLY what feature introduced)!"""
        },
        {
            "title": "Chapter 5.4 — Single Object Inspection: git show, Examining Specific Blobs and Commits via SHA-1",
            "body": """Jab tumhe kisi specific historical commit, tag, ya raw blob object ko directly inspect karna ho bina branch checkout kiye, `git show` primary tool hai.

Code: Investigating Objects via git show
```bash
# Specific commit ki complete metadata aur patch view karo:
$ git show 4b825dc

# Specific file ka historical version view karo kisi purane commit se:
$ git show 4b825dc:src/server.ts # Prints exact code of server.ts at commit 4b825dc

# Line-by-line blame trace (kis author ne kaunsi line kab change ki):
$ git blame -L 10,20 src/auth/token.ts
4b825dc (Sparsh 2026-10-10 14:22:10 +0530 10) export function verifyJWT(token: string) {
4b825dc (Sparsh 2026-10-10 14:22:10 +0530 11)   if (!token) throw new UnauthorizedError();
```"""
        }
    ],
    "challenges": {
        "c1": {
            "title": "CHALLENGE 5.1 — COMMIT RANGE SEMANTICS TRACE (DOUBLE VS TRIPLE DOT)",
            "prompt": "Given commit DAG where main has C1->C2->C3 and feature branched from C1 with C1->C4->C5. Predict exact output of git log main..feature, git log feature..main, git log main...feature, and git diff main...feature. Explain merge base semantics.",
            "solution_title": "Solution 5.1: Commit Range Topological Trace",
            "solution_code": """# DAG Topology:
#       C2 --- C3 (main)
#      /
# C1 --
#      \\
#       C4 --- C5 (feature)

# 1. git log main..feature
# Reachable from feature (C5, C4, C1) minus reachable from main (C3, C2, C1):
# Output: C5, C4

# 2. git log feature..main
# Reachable from main (C3, C2, C1) minus reachable from feature (C5, C4, C1):
# Output: C3, C2

# 3. git log main...feature (Symmetric difference)
# Output: C5, C4, C3, C2 (Commits unique to either branch)

# 4. git diff main...feature
# Evaluates diff against Merge Base (C1):
# Compares snapshot C1 against snapshot C5.
# Output: Shows ONLY modifications introduced by feature (C4 + C5).
# C2 and C3 modifications on main are ignored. (Identical to GitHub PR view)."""
        },
        "c2": {
            "title": "CHALLENGE 5.2 — ALGORITHM: MYERS DIFF ALGORITHM IN PYTHON",
            "prompt": "Implement the Myers Diff algorithm in pure Python: myers_diff(lines_a: list[str], lines_b: list[str]) -> list[str]. Finds Shortest Edit Script (SES) using greedy diagonal search. Outputs unified diff format with ' ', '+', and '-' prefixes. O(N * D) complexity.",
            "solution_title": "Solution 5.2: Production Myers Diff Algorithm Engine",
            "solution_code": """from typing import List

def myers_diff(a: List[str], b: List[str]) -> List[str]:
    \"\"\"Computes shortest edit script between two lists of lines using Myers Greedy Algorithm.\"\"\"
    n, m = len(a), len(b)
    max_d = n + m
    # V array stores furthest reaching x for each diagonal k (offset by max_d)
    v = {1: 0}
    trace = []

    for d in range(max_d + 1):
        v_copy = v.copy()
        trace.append(v_copy)
        for k in range(-d, d + 1, 2):
            # Decide whether to move down (insertion) or right (deletion)
            if k == -d or (k != d and v.get(k - 1, 0) < v.get(k + 1, 0)):
                x = v.get(k + 1, 0)
            else:
                x = v.get(k - 1, 0) + 1
            y = x - k

            # Snake: follow diagonal matches for free
            while x < n and y < m and a[x] == b[y]:
                x += 1
                y += 1

            v[k] = x
            if x >= n and y >= m:
                # Target reached! Backtrack path:
                return _backtrack_myers(trace, a, b, d, n, m)
    return []

def _backtrack_myers(trace, a, b, d, n, m) -> List[str]:
    diff = []
    x, y = n, m
    for d_step in range(d, 0, -1):
        v = trace[d_step]
        k = x - y
        prev_k = k + 1 if (k == -d_step or (k != d_step and v.get(k - 1, 0) < v.get(k + 1, 0))) else k - 1
        prev_x = v[prev_k]
        prev_y = prev_x - prev_k

        while x > prev_x and y > prev_y:
            diff.append(f"  {a[x - 1]}")
            x -= 1
            y -= 1
        if d_step > 0:
            if x == prev_x:
                diff.append(f"+ {b[y - 1]}")
                y -= 1
            elif y == prev_y:
                diff.append(f"- {a[x - 1]}")
                x -= 1
    while x > 0 and y > 0:
        diff.append(f"  {a[x - 1]}")
        x -= 1
        y -= 1
    return list(reversed(diff))

# Test:
lines_orig = ["function add(a, b) {", "  return a + b;", "}"]
lines_mod  = ["function add(a, b) {", "  // validation", "  if (!a) return 0;", "  return a + b;", "}"]
diff_result = myers_diff(lines_orig, lines_mod)
print("\\n".join(diff_result))"""
        },
        "c3": {
            "title": "CHALLENGE 5.3 — INDUSTRIAL MINI-PROJECT: TERMINAL COMMIT GRAPH VIEWER",
            "prompt": "Build a zero-dependency terminal visualizer in Python that reads .git/refs/heads/ and traverses parent commit pointers in .git/objects/ to print an ASCII commit DAG with hashes, branch pointers, and commit subjects. Under 100 lines.",
            "solution_title": "Solution 5.3: Pure Python Commit DAG ASCII Visualizer",
            "solution_code": """import os
import zlib
from pathlib import Path
from typing import Dict, List, Set

def parse_commit_object(obj_bytes: bytes) -> Dict[str, Any]:
    header, _, body = obj_bytes.partition(b"\\x00")
    lines = body.decode("utf-8", errors="replace").splitlines()
    parents = []
    message = ""
    in_msg = False
    for line in lines:
        if in_msg:
            message += line + "\\n"
        elif line.startswith("parent "):
            parents.append(line.split()[1])
        elif line == "":
            in_msg = True
    return {"parents": parents, "message": message.strip().splitlines()[0] if message.strip() else ""}

def view_commit_graph(repo_root: Path) -> None:
    git_dir = repo_root / ".git"
    refs_dir = git_dir / "refs" / "heads"
    
    # 1. Collect all local branches
    branches: Dict[str, str] = {} # commit_sha -> branch_name
    for b_file in refs_dir.glob("*"):
        branches[b_file.read_text().strip()] = b_file.name

    # 2. Get HEAD
    head_content = (git_dir / "HEAD").read_text().strip()
    head_sha = ""
    if head_content.startswith("ref: refs/heads/"):
        b_name = head_content[16:]
        b_path = refs_dir / b_name
        if b_path.exists():
            head_sha = b_path.read_text().strip()

    # 3. BFS traversal
    visited: Set[str] = set()
    queue = list(branches.keys())
    
    print("\\n=== COMMIT DAG REPOSITORY GRAPH ===")
    while queue:
        sha = queue.pop(0)
        if sha in visited or not sha:
            continue
        visited.add(sha)

        obj_path = git_dir / "objects" / sha[:2] / sha[2:]
        if not obj_path.exists():
            continue
        raw = zlib.decompress(obj_path.read_bytes())
        info = parse_commit_object(raw)

        # Build decoration tag
        tags = []
        if sha == head_sha:
            tags.append(f"HEAD -> {branches.get(sha, '')}")
        elif sha in branches:
            tags.append(branches[sha])
        dec_str = f" ({', '.join(tags)})" if tags else ""

        print(f"* {sha[:7]}{dec_str} {info['message']}")
        for p in info["parents"]:
            queue.append(p)

# Run test on current repository:
view_commit_graph(Path("."))"""
        }
    }
}

PHASE_6 = {
    "number": 6,
    "title": "Branching & Pointer Mechanics",
    "topics": "Branch as a 41-Byte Pointer, git branch, git checkout, git switch, Detached HEAD State, Branch Deletion",
    "chapters": [
        {
            "title": "Chapter 6.1 — Branch Architecture: Why Git Branches Are Cheap 41-Byte SHA-1 Pointer Files in refs/heads/",
            "body": """Other VCS systems me branching ek heavy operation hoti thi: poore project directory ka ek naya physical copy banta tha, jo megabytes ya gigabytes disk consume karta tha.

Git me branch kya hai?
Git me ek branch sirf ek 41-byte text file hoti hai jo `.git/refs/heads/<branch-name>` me rehti hai! Aur us file ke andar sirf ek 40-character SHA-1 commit hash aur ek newline character hota hai!

Iska matlab:
• Git me nayi branch create karna instant (microsecond O(1)) operation hai.
• Chahe project 50GB ka ho aur usme 100,000 commits hon, ek nayi branch create karne me sirf 41 bytes disk space lagti hai!
• Branch switch karne me sirf HEAD reference file change hoti hai aur un files ko disk pe update kiya jata hai jo dono branches ke beech different hain.

Code: Inspecting Branch Pointers Directly on Disk
```bash
# Nayi branch create karo:
$ git branch feature/payment-gateway

# Check on disk:
$ ls -la .git/refs/heads/
-rw-r--r--  1 sparsh  staff  41 Oct 10 14:00 feature/payment-gateway
-rw-r--r--  1 sparsh  staff  41 Oct 10 14:00 main

# Read branch file content:
$ cat .git/refs/heads/feature/payment-gateway
4b825dc642cb6eb9a060e54bf8d69288fbee4904 # Exactly 41 bytes!

# Jab tum commit karte ho, Git sirf is 41-byte file ke content ko naye SHA-1 se update karta hai!
```

[MENTAL MODEL]
Branches are not containers of commits. Branches are movable labels pointing to the tip of a commit DAG chain."""
        },
        {
            "title": "Chapter 6.2 — Branch Creation & Switching: git branch vs git switch vs git checkout (-b)",
            "body": """Git ke historical command set me `git checkout` overloaded command thi: ye branch bhi switch karti thi, files ko restore bhi karti thi, aur commits pe time-travel bhi karti thi.

Git v2.23+ me Git core team ne do dedicated, single-responsibility commands introduce kiye:
1. `git switch`: Sirf branches switch aur create karne ke liye.
2. `git restore`: Working tree aur staged files ko restore/discard karne ke liye.

Modern Switching Commands:
• `git switch <branch>`: Existing branch pe switch karo.
• `git switch -c <branch>` (ya legacy `git checkout -b <branch>`): Nayi branch create karo aur immediately switch karo.
• `git branch -a`: Saari local aur remote tracking branches list karo.

Code: Modern Branch Navigation
```bash
# Nayi branch banao aur switch karo:
$ git switch -c feature/auth-redesign
Switched to a new branch 'feature/auth-redesign'

# Wapas main branch pe switch karo:
$ git switch main
Switched to branch 'main'

# Previous branch pe fast switch karo (like cd -):
$ git switch -
Switched to branch 'feature/auth-redesign'
```"""
        },
        {
            "title": "Chapter 6.3 — The Detached HEAD State: What Happens When HEAD Points to a Commit Instead of a Branch Ref",
            "body": """Detached HEAD State Git ka sabse misunderstanding generate karne wala state hai, lekin internally ye bahut simple aur logical hai.

Normal State (Attached HEAD):
Normally `.git/HEAD` file me kisi branch ka symbolic reference hota hai:
`ref: refs/heads/main`
Jab tum commit create karte ho, Git HEAD ke through `main` branch pointer ko aage badha deta hai.

Detached HEAD State:
Jab tum kisi specific commit hash pe checkout karte ho (e.g. `git checkout 4b825dc` ya `git checkout HEAD~2`), HEAD branch file ko point karne ke bajaye seedha us commit hash ko point karne lagta hai!
`.git/HEAD`: `4b825dc642cb6eb9a060e54bf8d69288fbee4904`

DANGER: Agar tum Detached HEAD state me naye commits create karte ho, wo commits kisi bhi branch se attached nahi hote! Jab tum wapas `git switch main` karoge, wo naye commits 'orphan' ya 'dangling' ban jayenge! Agar 30-90 din tak unhe koi branch point nahi karegi, Git Garbage Collection (`git gc`) unhe permanently delete kar dega!

Code: Rescuing Work from Detached HEAD State
```bash
# Galti se detached state me commit create kar diya:
$ git checkout 19a8f21 # Historical commit
Note: switching to '19a8f21'. You are in 'detached HEAD' state.

$ echo "emergency patch" >> fix.txt && git commit -am "temp hotfix"
[detached HEAD 7e2d9a1] temp hotfix # Commit created in detached state!

# RESCUE: Is commit pe naya branch pointer attach karo:
$ git switch -c hotfix/detached-rescue
Switched to a new branch 'hotfix/detached-rescue' # Ab safe hai! Never lost!
```"""
        },
        {
            "title": "Chapter 6.4 — Deleting and Renaming Branches: Safe Delete (-d) vs Force Delete (-D), Upstream Tracking",
            "body": """Branch lifecycle me unmerged vs merged branches ko safely delete karna zaroori hota hai.

Branch Deletion Rules:
• `git branch -d <branch>` (Safe Delete): Git verify karta hai ki kya is branch ke commits already target branch me merge ho chuke hain. Agar unmerged commits hain, Git deletion refuse kar dega warning ke sath: `The branch 'feature' is not fully merged.`
• `git branch -D <branch>` (Force Delete): Git forcefully branch pointer delete kar deta hai chahe commits unmerged kyu na hon. (Commits physically delete nahi hote, sirf ref pointer delete hota hai; commits reflog me rehte hain).
• `git branch -m <old> <new>`: Branch rename karta hai.

Code: Safe vs Force Branch Deletion
```bash
# Safe deletion attempt on unmerged feature branch:
$ git branch -d feature/experimental
error: The branch 'feature/experimental' is not fully merged.
If you are sure you want to delete it, run 'git branch -D feature/experimental'.

# Force delete when feature is officially abandoned:
$ git branch -D feature/experimental
Deleted branch feature/experimental (was 7e2d9a1).

# Delete remote branch on GitHub:
$ git push origin --delete feature/experimental
To github.com:sparsh/app.git
 - [deleted]         feature/experimental
```"""
        }
    ],
    "challenges": {
        "c1": {
            "title": "CHALLENGE 6.1 — DETACHED HEAD STATE & GARBAGE COLLECTION TRACE",
            "prompt": "Trace the state of HEAD pointer, branch references, and commit reachability when a developer checks out HEAD~2, creates a commit C_orph, and switches back to main. Explain why C_orph becomes dangling and how git reflog saves it before git gc.",
            "solution_title": "Solution 6.1: Detached HEAD State & Garbage Collection Trace",
            "solution_code": """# Trace Step-by-Step:
# 1. Start: HEAD -> main -> C3.
# 2. $ git checkout HEAD~2
#    HEAD now directly stores SHA-1 of commit C1. Detached state entered.
# 3. $ echo 'hotfix' > fix.txt && git commit -am 'c_orph'
#    New commit C_orph is created. C_orph's parent is C1.
#    HEAD advances to point directly to C_orph.
#    CRITICAL: No branch ref in refs/heads/ was updated!
# 4. $ git checkout main
#    HEAD points back to refs/heads/main.
#    C_orph is now UNREACHABLE from any branch or tag ref!
# 5. Result:
#    - C_orph does NOT appear in 'git log'.
#    - It is a 'dangling commit'.
#    - But .git/logs/HEAD (reflog) still records: 'commit: c_orph'.
#    - Developers can run 'git branch rescue-branch <sha_of_c_orph>' within 30-90 days
#      before 'git gc' prunes unreachable objects."""
        },
        "c2": {
            "title": "CHALLENGE 6.2 — ALGORITHM: LOWEST COMMON ANCESTOR (MERGE BASE) FINDER",
            "prompt": "Implement find_merge_base(dag: dict[str, list[str]], commit_a: str, commit_b: str) -> str in Python. dag maps commit hashes to list of parent commit hashes. Perform BFS / topological search from both commit tips to return closest shared ancestor.",
            "solution_title": "Solution 6.2: Lowest Common Ancestor (Merge Base) Finder",
            "solution_code": """from collections import deque
from typing import Dict, List, Set, Optional

def find_merge_base(dag: Dict[str, List[str]], commit_a: str, commit_b: str) -> Optional[str]:
    \"\"\"Finds the Lowest Common Ancestor (Merge Base) of two commits in a DAG.\"\"\"
    if commit_a == commit_b:
        return commit_a

    def get_ancestors_with_depth(start_commit: str) -> Dict[str, int]:
        depths = {start_commit: 0}
        queue = deque([(start_commit, 0)])
        while queue:
            curr, d = queue.popleft()
            for parent in dag.get(curr, []):
                if parent not in depths or depths[parent] > d + 1:
                    depths[parent] = d + 1
                    queue.append((parent, d + 1))
        return depths

    ancestors_a = get_ancestors_with_depth(commit_a)
    ancestors_b = get_ancestors_with_depth(commit_b)

    # Find common ancestors
    common = set(ancestors_a.keys()) & set(ancestors_b.keys())
    if not common:
        return None

    # Pick common ancestor with lowest combined depth distance (closest ancestor)
    merge_base = min(common, key=lambda c: ancestors_a[c] + ancestors_b[c])
    return merge_base

# Verification test on diamond DAG:
#       C2 --- C3 (commit_a)
#      /
# C1 --
#      \\
#       C4 --- C5 (commit_b)
dag_sample = {
    "C3": ["C2"],
    "C2": ["C1"],
    "C5": ["C4"],
    "C4": ["C1"],
    "C1": [],
}
mb = find_merge_base(dag_sample, "C3", "C5")
print(f"Calculated Merge Base: {mb}") # C1"""
        },
        "c3": {
            "title": "CHALLENGE 6.3 — INDUSTRIAL MINI-PROJECT: AUTOMATED STALE BRANCH CLEANUP ENGINE",
            "prompt": "Build a production CLI tool git-prune-stale in Python. Queries merged branches against target 'main', excludes protected branches (main, master, prod, staging), prompts for safe deletion via 'git branch -d', and emits a JSON audit summary.",
            "solution_title": "Solution 6.3: Production Stale Branch Pruning Engine",
            "solution_code": """import subprocess
import json
from datetime import datetime, timezone
from typing import List

PROTECTED_BRANCHES = {"main", "master", "develop", "production", "staging"}

def prune_stale_branches(target_branch: str = "main", dry_run: bool = True) -> None:
    # 1. Fetch merged local branches
    cmd = ["git", "branch", "--merged", target_branch]
    try:
        output = subprocess.check_output(cmd, text=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to query branches: {e}")
        return

    merged_candidates = []
    for line in output.splitlines():
        b_name = line.replace("*", "").strip()
        if b_name and b_name not in PROTECTED_BRANCHES:
            merged_candidates.append(b_name)

    if not merged_candidates:
        print(f"[INFO] No stale merged branches found against '{target_branch}'.")
        return

    print(f"Found {len(merged_candidates)} stale branches merged into '{target_branch}':")
    for b in merged_candidates:
        print(f"  - {b}")

    audit_log = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "target_branch": target_branch,
        "dry_run": dry_run,
        "deleted_branches": [],
    }

    if dry_run:
        print("\\n[DRY-RUN] No branches were deleted. Pass dry_run=False to delete.")
        return

    for b in merged_candidates:
        res = subprocess.run(["git", "branch", "-d", b], capture_output=True, text=True)
        if res.returncode == 0:
            print(f"✅ Deleted: {b}")
            audit_log["deleted_branches"].append(b)
        else:
            print(f"❌ Failed to delete {b}: {res.stderr.strip()}")

    print("\\nAudit Report:\\n", json.dumps(audit_log, indent=2))

if __name__ == "__main__":
    prune_stale_branches(dry_run=True)"""
        }
    }
}
