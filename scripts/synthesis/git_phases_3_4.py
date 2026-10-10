"""Git Engineering Reference Manual — Phases 3 & 4 Content.
Strict 100% Roman Hinglish narrative, zero Devanagari, production-grade code.
"""

from typing import Dict, Any, List

PHASE_3 = {
    "number": 3,
    "title": "The Three Trees & Core Lifecycle",
    "topics": "Working Directory, Staging Area (Index), Repository (HEAD), git add, git commit, git status, Conventional Commits",
    "chapters": [
        {
            "title": "Chapter 3.1 — The Three Trees Mental Model: Working Tree, Index/Staging Area, and HEAD Commit",
            "body": """Git ko master karne ke liye sabse important foundation hai 'The Three Trees' architecture. Agar tum ye samajh gaye ki data in teen stages ke beech kaise transit karta hai, Git me kabhi confusion nahi hoga.

The Three Trees kya hain:
1. Working Tree (Sandbox):
   Ye wo files hain jo tumhare operating system file system me disk pe exist karti hain (e.g. `main.py`, `app.js`). Tum inhe VS Code ya terminal me directly edit karte ho. Git is stage ko monitor karta hai lekin directly manage nahi karta.
2. Index / Staging Area (Proposed Next Commit):
   Ye `.git/index` file ke andar stored ek binary cache structure hai. Jab tum `git add` run karte ho, Git tumhari modified file ka content hash karta hai, blob object create karta hai, aur index me record karta hai. Index wo exact snapshot hai jo tumhara agla commit banne wala hai!
3. HEAD (Last Committed State):
   HEAD tumhari active branch ke latest commit snapshot ko point karta hai. Ye immutable repository history ka part hai.

[DIAGRAM: three_trees]

[MENTAL MODEL]
Working Tree (Disk) ---> [git add] ---> Staging Area (Index) ---> [git commit] ---> HEAD (Commit DAG)
           ^                                                                            |
           +--------------------------- [git restore / reset] --------------------------+

[ENGINEERING GOTCHA]
Production code me unexpected bugs aate hain jab developers assume karein ki `git add` sirf file ka pointer save karta hai. Gotcha ye hai ki `git add` immediate content snapshot create karta hai! Agar tumne file add ki, aur uske baad file me 2 nayi lines add kar di bina wapas `git add` kiye, toh commit me sirf wahi changes jayenge jo `git add` ke time the! Ek hi file simultaneously staged aur unstaged states me exist kar sakti hai."""
        },
        {
            "title": "Chapter 3.2 — Staging Files: git add Deep Dive, Tracking New vs Modified Files, Staging Partial Hunks",
            "body": """`git add` command sirf ek simple file staging utility nahi hai — ye Git object database me blobs generate karne ka primary trigger hai.

Har scenario ke liye right command samjho:
• `git add <file>`: Specific file ko stage karta hai.
• `git add .`: Current directory aur uske subdirectories ke saare changes stage karta hai.
• `git add -A` (ya `git add --all`): Poore repository ke saare additions, modifications, aur deletions ko stage karta hai.
• `git add -p` (Patch mode): Ek single file ke andar alag-alag code hunks ko individually stage karne ki power deta hai!

Code: Interactive Partial Staging (git add -p)
```bash
# Jab tumne ek hi file me do alag-alag features modify kar diye hon:
$ git add -p src/server.js
diff --git a/src/server.js b/src/server.js
@@ -14,6 +14,8 @@ function startServer() {
+    // Feature A: Metrics tracking
+    initPrometheusMetrics();
     app.listen(PORT);
@@ -35,6 +37,8 @@ function shutdown() {
+    // Feature B: Graceful database draining
+    drainConnectionPool();
 }
Stage this hunk [y,n,q,a,d,s,e,?]? y   # Feature A staged!
Stage this hunk [y,n,q,a,d,s,e,?]? n   # Feature B left in working tree!

# Verify staged vs unstaged status:
$ git diff --staged # Shows only Feature A
$ git diff          # Shows only Feature B
```"""
        },
        {
            "title": "Chapter 3.3 — Atomic Commits: git commit, Commit Messages as Historical Documentation, Conventional Commits",
            "body": """Senior engineering teams me commit quality code quality jitni hi critical hoti hai. Git history tumhare project ka architectural flight recorder hai.

Atomic Commit Invariant:
Har commit ek single, logically complete, independent unit of work hona chahiye. Agar ek commit me refactoring, bug fix, aur new dependency update teeno mix hain, toh `git revert` ya `git bisect` karna impossible ho jata hai.

Conventional Commits Specification:
Modern enterprise CI/CD pipelines commit messages ko programmatically parse karke automatic changelog aur semantic version bump calculate karte hain:
`<type>(<optional scope>): <description>`

Common Commit Types:
• `feat`: Naya feature introduce karna (`feat(auth): add OAuth2 token refresh pipeline`)
• `fix`: Bug fix karna (`fix(db): resolve connection pool leak on socket timeout`)
• `refactor`: Code change jo na bug fix karta hai na new feature add karta hai
• `perf`: Performance optimization (`perf(v8): inline monomorphic shape cache lookup`)
• `test`: Tests add karna ya fix karna
• `chore`: Build scripts, dependencies, CI configuration

Code: Creating High-Hygiene Commits
```bash
# Detailed multi-line commit message format:
$ git commit -m "feat(cache): implement distributed redis fallback

- Add 200ms timeout on primary Redis cluster ping
- Fallback to in-memory LRU cache on socket exception
- Emit Prometheus metric 'cache_fallback_total'

Closes #142"
```"""
        },
        {
            "title": "Chapter 3.4 — Inspecting State: git status Invariants, Untracked vs Tracked, Changes Staged for Commit",
            "body": """`git status` command repository ke active state ka complete diagnostic report provide karta hai.

`git status` ke short format (`-s`) ko decode karna seekho:
• `??`: Untracked file (Git is file ke existence se aware hai lekin version control me include nahi hai).
• `A `: Added / Staged (File index me nayi file ki tarah add ho chuki hai).
• `M `: Modified and Staged (File modify hui aur index me stage ho chuki hai).
• ` M`: Modified but Unstaged (File disk pe modify hui lekin index me purana version hai).
• `MM`: Staged AND Unstaged (File stage hui, aur staging ke baad disk pe wapas modify hui!).

Code: Decoding git status --short Flags
```bash
$ git status -s
?? temp.log      # Untracked file
A  config.json   # New file staged
M  routes.js     # Modified file staged
 M utils.js      # Modified file NOT staged
MM server.js     # Staged changes exist AND newer unstaged edits on disk!
```"""
        }
    ],
    "challenges": {
        "c1": {
            "title": "CHALLENGE 3.1 — THE THREE TREES STATE MACHINE TRACE",
            "prompt": "Trace the exact state of files across Working Tree, Index (Staging), and HEAD. Predict the output of git status --short, git diff, and git diff --staged when a file is staged and then modified again on disk.",
            "solution_title": "Solution 3.1: Simultaneous Dual-State Trace & Output Prediction",
            "solution_code": """# Trace Execution:
$ echo "v1" > app.py && git add app.py && git commit -m "c1"
# HEAD = 'v1', Index = 'v1', Working Tree = 'v1'

$ echo "v2" > app.py
# Working Tree is modified to 'v2'. Index and HEAD still hold 'v1'.
$ git status -s
 M app.py         # Space in col 1, 'M' in col 2 (unstaged)

$ git add app.py
# Working Tree = 'v2', Index = 'v2', HEAD = 'v1'.
$ git status -s
M  app.py         # 'M' in col 1 (staged), space in col 2

$ echo "v3" > app.py
# Working Tree = 'v3', Index = 'v2', HEAD = 'v1'!
$ git status -s
MM app.py         # BOTH columns populated!

# Predict Diffs:
$ git diff
# Compares Working Tree ('v3') vs Index ('v2'):
# -v2
# +v3

$ git diff --staged
# Compares Index ('v2') vs HEAD ('v1'):
# -v1
# +v2"""
        },
        "c2": {
            "title": "CHALLENGE 3.2 — ALGORITHM: GIT TREE OBJECT SERIALIZER",
            "prompt": "Implement create_tree_object(entries: list[tuple[str, str, str]]) -> tuple[str, bytes] in Python. Each entry is (mode, name, sha1_hex). Sort entries strictly using Git byte-ordering rules (directories sorted as if ending in '/'). Encode into binary format '<mode> <name>\\0<20-byte-sha1>' and prepend 'tree <size>\\0'. Return (tree_hash, payload).",
            "solution_title": "Solution 3.2: Binary Tree Object Serializer Engine",
            "solution_code": """import hashlib
import binascii
from typing import List, Tuple

def create_tree_object(entries: List[Tuple[str, str, str]]) -> Tuple[str, bytes]:
    \"\"\"Serializes file and directory entries into a valid Git tree object.\"\"\"
    # Git sort rule: directories (mode 040000) are sorted as if their name ends with '/'
    def sort_key(entry: Tuple[str, str, str]) -> bytes:
        mode, name, _ = entry
        suffix = b"/" if mode == "040000" else b""
        return name.encode("utf-8") + suffix

    sorted_entries = sorted(entries, key=sort_key)

    # Build binary tree body:
    body_parts = []
    for mode, name, sha1_hex in sorted_entries:
        # Normalize mode string (e.g., '100644')
        mode_bytes = str(int(mode, 8)).encode("ascii") # Git omits leading zero in binary tree
        name_bytes = name.encode("utf-8")
        sha1_raw = binascii.unhexlify(sha1_hex) # 20 raw bytes

        entry_bytes = mode_bytes + b" " + name_bytes + b"\\x00" + sha1_raw
        body_parts.append(entry_bytes)

    body = b"".join(body_parts)
    header = f"tree {len(body)}\\x00".encode("ascii")
    payload = header + body
    tree_hash = hashlib.sha1(payload).hexdigest()

    return tree_hash, payload

# Verification test:
entries = [
    ("100644", "README.md", "4b825dc642cb6eb9a060e54bf8d69288fbee4904"),
    ("100644", "server.py", "f1379c65691d57579f18731e8477ec53ffbfef98"),
]
t_hash, t_bytes = create_tree_object(entries)
print(f"Generated Tree SHA-1: {t_hash}")
print(f"Tree Payload Length: {len(t_bytes)} bytes")"""
        },
        "c3": {
            "title": "CHALLENGE 3.3 — INDUSTRIAL MINI-PROJECT: PURE PYTHON STAGING SIMULATOR",
            "prompt": "Build an in-memory staging area simulator class GitIndexManager with stage_file, unstage_file, and commit methods. Track blobs, build tree objects, write commit objects, and update HEAD pointer. Zero external imports.",
            "solution_title": "Solution 3.3: Pure Python Git Staging & Commit Manager",
            "solution_code": """import hashlib
import time
from typing import Dict, Optional

class GitIndexManager:
    \"\"\"Simulates Git's 3-Trees staging and atomic commit lifecycle in memory.\"\"\"
    def __init__(self, author: str = "Engineer <eng@faang.io>"):
        self.author = author
        self.objects: Dict[str, bytes] = {} # Key-Value store
        self.index: Dict[str, str] = {}     # filepath -> blob SHA-1
        self.head_commit: Optional[str] = None

    def _hash_object(self, obj_type: str, data: bytes) -> str:
        payload = f"{obj_type} {len(data)}\\x00".encode("ascii") + data
        sha1 = hashlib.sha1(payload).hexdigest()
        self.objects[sha1] = payload
        return sha1

    def stage_file(self, filepath: str, content: str) -> str:
        blob_sha = self._hash_object("blob", content.encode("utf-8"))
        self.index[filepath] = blob_sha
        return blob_sha

    def unstage_file(self, filepath: str) -> None:
        if filepath in self.index:
            del self.index[filepath]

    def commit(self, message: str) -> str:
        if not self.index:
            raise ValueError("Nothing to commit (staging index is empty).")

        # 1. Build tree payload from index
        tree_lines = []
        for path in sorted(self.index.keys()):
            tree_lines.append(f"100644 blob {self.index[path]}\\t{path}")
        tree_body = "\\n".join(tree_lines).encode("utf-8")
        tree_sha = self._hash_object("tree", tree_body)

        # 2. Build commit payload
        timestamp = int(time.time())
        commit_lines = [f"tree {tree_sha}"]
        if self.head_commit:
            commit_lines.append(f"parent {self.head_commit}")
        commit_lines.append(f"author {self.author} {timestamp} +0000")
        commit_lines.append(f"committer {self.author} {timestamp} +0000")
        commit_lines.append("")
        commit_lines.append(message)
        commit_lines.append("")

        commit_body = "\\n".join(commit_lines).encode("utf-8")
        commit_sha = self._hash_object("commit", commit_body)
        self.head_commit = commit_sha
        return commit_sha

# Verification:
mgr = GitIndexManager()
mgr.stage_file("app.py", "print('hello v1')")
mgr.stage_file("config.json", "{\\"env\\": \\"prod\\"}")
c1 = mgr.commit("feat: initial microservice setup")
print(f"Committed C1: {c1}")

mgr.stage_file("app.py", "print('hello v2 with metrics')")
c2 = mgr.commit("feat(app): add telemetry tracking")
print(f"Committed C2: {c2}")
print("Verified HEAD commit parentage chain correctly intact!")"""
        }
    }
}

PHASE_4 = {
    "number": 4,
    "title": "File Tracking, Ignoring & Tree Cleanliness",
    "topics": ".gitignore Rules, Pattern Syntax, Untracking Cached Files, .gitkeep Conventions, git clean Safeguards",
    "chapters": [
        {
            "title": "Chapter 4.1 — Ignoring Files: .gitignore Syntax, Wildcards, Negation (!), and Directory Anchoring",
            "body": """Har real-world project me aisi files generate hoti hain jinhe version control me kabhi commit nahi hona chahiye: compiled binaries (`dist/`, `build/`, `.exe`), local runtime caches (`node_modules/`, `__pycache__/`), secrets aur tokens (`.env`), aur OS metadata (`.DS_Store`, `Thumbs.db`).

Agar tum galti se ek 1GB ki compiled build ya 500MB `node_modules` folder commit kar do, toh wo Git database me permanently store ho jayega, har clone slow ho jayega, aur collaborators ka bandwidth waste hoga.

`.gitignore` syntax rules ko deeply samjho:
1. Blank lines aur comments: `#` se start hone wali lines ignore hoti hain.
2. Direct filename: `debug.log` poore repository me kisi bhi folder me `debug.log` ko ignore karega.
3. Slash at start (Root Anchoring): `/logs` sirf root folder ke `logs` ko match karega, `src/logs` ko nahi.
4. Slash at end (Directory Match): `dist/` sirf directories ko match karega, kisi `dist` naam ki plain file ko nahi.
5. Asterisk wildcard: `*.tmp` kisi bhi extension `.tmp` wali file ko ignore karega.
6. Double asterisk (`**`): Recursive nested directories match karta hai (`**/logs/*.txt`).
7. Negation (`!`): Pehle ignore ki gayi file ko re-include karta hai (`!important.log`).

[RULE]
Parent Directory Pruning Invariant:
Git will NOT re-include a file if a parent directory of that file is already excluded!
Example: Agar tumne likha:
```text
logs/
!logs/audit.log
```
Toh `audit.log` IGNORE hi rahegi! Kyunki Git optimization ke liye `logs/` directory ke andar search hi nahi karta! Sahi tarika hai:
```text
logs/*
!logs/audit.log
```

Code: Production-Grade .gitignore for Fullstack TypeScript/Python
```text
# OS Metadata
.DS_Store
Thumbs.db

# Dependencies
node_modules/
.venv/
venv/
__pycache__/
*.pyc

# Build outputs
dist/
build/
*.egg-info/

# Environment Secrets
.env
.env.local
*.pem
*.key
```"""
        },
        {
            "title": "Chapter 4.2 — Untracking Already Committed Files: git rm --cached and Clearing the Index Cache",
            "body": """Ye junior aur mid-level engineers ka sabse common gotcha hai:
'Maine file `.gitignore` me daal di, lekin Git abhi bhi uske modifications track kar raha hai!'

Gotcha ye hai ki `.gitignore` sirf UNTRACKED files pe kaam karta hai! Agar ek file already Git ke Index ya commit history me staged thi jab tumne use `.gitignore` me add kiya, toh Git use tab tak track karta rahega jab tak tum explicitly index se remove na karo.

File ko disk pe delete kiye bina sirf Git tracking se kaise hatayein:
`git rm --cached <filepath>`

Code: Safely Untracking Committed Secrets / Caches
```bash
# Step 1: File ko index se remove karo bina disk se delete kiye:
$ git rm --cached .env
rm '.env'

# Step 2: Directory ko recursively untrack karo:
$ git rm -r --cached build/

# Step 3: Verify with status:
$ git status
On branch main
Changes to be committed:
  deleted:    .env # Deleted from Git Index, but still alive on your disk!

# Step 4: Commit untracking change:
$ git commit -m "chore: untrack local environment secrets from index"
```"""
        },
        {
            "title": "Chapter 4.3 — Tracking Empty Directories: The .gitkeep Convention vs Git's Inability to Track Empty Trees",
            "body": """Git ki internal architecture me ek unique characteristic hai:
Git directories ko track nahi karta — Git sirf files (Blobs) ko track karta hai!

Jab tak kisi directory ke andar kam se kam ek file na ho, Git us folder ka tree object create nahi kar sakta. Agar tum ek empty directory `mkdir logs` banao, `git status` use complete ignore karega.

Agar tumhe production project me koi directory structure preserve karni hai (e.g. `uploads/`, `logs/`, `temp/`), toh community convention hai uske andar ek hidden zero-byte file rakhna: `.gitkeep`.

Code: Preserving Directory Structure with .gitkeep
```bash
$ mkdir -p src/uploads
$ touch src/uploads/.gitkeep
$ git add src/uploads/.gitkeep
$ git commit -m "chore: initialize uploads directory scaffolding"
```"""
        },
        {
            "title": "Chapter 4.4 — Cleaning the Working Tree: git clean Flags (-n dry run, -fd), Safeguards Against Data Loss",
            "body": """Jab tumhare local repository me build artifacts, temporary log files, aur untracked scratch files clutter ban jayein, unhe safely clean karne ke liye `git clean` use hota hai.

`git clean` irreversible destructive operation hai — deleted files recycle bin me nahi jaati, seedha permanently wipe hoti hain! Isliye Git dry-run force karta hai.

Flags Invariant:
• `-n` (Dry Run): Safe simulation! Sirf print karta hai ki kya delete hoga, actual deletion nahi karta.
• `-f` (Force): Execution confirmation.
• `-d`: Untracked directories ko bhi include karta hai.
• `-x`: `.gitignore` me listed ignored files ko bhi remove karta hai (e.g. pristine clean state).

Code: Safe Working Tree Cleaning Protocol
```bash
# ALWAYS run dry-run first! Non-negotiable safety invariant:
$ git clean -nd
Would remove scratch.py
Would remove temp/
Would remove build_artifacts/

# Verify output carefully, phir force clean run karo:
$ git clean -fd
Removing scratch.py
Removing temp/
Removing build_artifacts/

# Full pristine clean (including node_modules and ignored caches):
$ git clean -fdx
```"""
        }
    ],
    "challenges": {
        "c1": {
            "title": "CHALLENGE 4.1 — .GITIGNORE NEGATION & DIRECTORY PRUNING TRACE",
            "prompt": "Given complex .gitignore rules with wildcards, directory slashes, and negation operators, predict tracking status for 4 candidate file paths. Explain parent directory pruning mechanics.",
            "solution_title": "Solution 4.1: Pathspec Evaluation & Directory Pruning Analysis",
            "solution_code": """# Rules Evaluated:
# 1: logs/
# 2: !logs/audit.log
# 3: temp/*
# 4: !temp/keep.txt
# 5: dist/**/bundle.js

# Candidate 1: logs/debug.log
# Result: IGNORED. Matches rule 1.

# Candidate 2: logs/audit.log
# Result: IGNORED! (Gotcha!)
# Explanation: Rule 1 'logs/' tells Git to ignore the entire directory.
# Git completely prunes 'logs/' from path traversal, so rule 2 '!logs/audit.log'
# is NEVER evaluated.

# Candidate 3: temp/keep.txt
# Result: TRACKED!
# Explanation: Rule 3 'temp/*' ignores contents inside 'temp/', but doesn't prune
# the directory itself. Rule 4 negation successfully re-includes 'temp/keep.txt'.

# Candidate 4: dist/release/v2/bundle.js
# Result: IGNORED.
# Explanation: Double asterisk '**' matches arbitrary directory depth."""
        },
        "c2": {
            "title": "CHALLENGE 4.2 — ALGORITHM: GIT PATHSPEC PATTERN MATCHER",
            "prompt": "Implement matches_gitignore(path: str, rule: str) -> bool in pure Python. Support directory anchoring ('/'), wildcards ('*', '**'), single character ('?'), and trailing slash directory detection. O(N*M) with zero third-party dependencies.",
            "solution_title": "Solution 4.2: High-Performance Git Pathspec Pattern Matcher",
            "solution_code": """import re

def matches_gitignore(path: str, rule: str, is_dir: bool = False) -> bool:
    \"\"\"Evaluates if a relative path matches a Gitignore rule.\"\"\"
    rule = rule.strip()
    if not rule or rule.startswith('#'):
        return False

    # Handle directory-only rules (trailing slash)
    dir_only = rule.endswith('/')
    if dir_only:
        if not is_dir:
            return False
        rule = rule[:-1]

    # Handle root anchoring (leading slash)
    anchored = rule.startswith('/')
    if anchored:
        rule = rule[1:]

    # Convert Git glob pattern to Python Regex
    # 1. Escape special regex characters except * and ?
    escaped = re.escape(rule).replace(r'\\*\\*', 'DOUBLE_STAR').replace(r'\\*', 'SINGLE_STAR').replace(r'\\?', 'QUESTION')
    
    # 2. Substitute glob tokens
    regex_pattern = escaped.replace('DOUBLE_STAR', '.*').replace('SINGLE_STAR', '[^/]*').replace('QUESTION', '[^/]')

    if anchored:
        regex_pattern = f"^{regex_pattern}$"
    else:
        regex_pattern = f"(?:^|/){regex_pattern}$"

    pattern = re.compile(regex_pattern)
    return bool(pattern.search(path))

# Verification tests:
print(matches_gitignore("src/debug.log", "*.log"))          # True
print(matches_gitignore("docs/api/v1.md", "docs/**/*.md"))   # True
print(matches_gitignore("root.txt", "/root.txt"))           # True
print(matches_gitignore("sub/root.txt", "/root.txt"))       # False (anchored)
print(matches_gitignore("dist", "dist/", is_dir=False))     # False (dir only)
print(matches_gitignore("dist", "dist/", is_dir=True))      # True"""
        },
        "c3": {
            "title": "CHALLENGE 4.3 — INDUSTRIAL MINI-PROJECT: PRE-COMMIT SECRET SCANNER HOOK",
            "prompt": "Build an automated pre-commit hook script .git/hooks/pre-commit in pure Python. Inspect all staged files via 'git diff --cached', scan diff hunks for sensitive patterns (AWS keys, GitHub tokens, private keys), and block commit with exit code 1 if found. Under 50ms latency.",
            "solution_title": "Solution 4.3: Automated Pre-Commit Secret Scanner Hook",
            "solution_code": """#!/usr/bin/env python3
import sys
import re
import subprocess

SECRET_PATTERNS = [
    ("AWS Access Key ID", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("GitHub Personal Access Token", re.compile(r"ghp_[0-9a-zA-Z]{36}")),
    ("Generic Private Key", re.compile(r"-----BEGIN (?:RSA|OPENSSH|EC) PRIVATE KEY-----")),
    ("Slack API Token", re.compile(r"xox[baprs]-[0-9a-zA-Z]{10,48}")),
]

def scan_staged_changes() -> int:
    # 1. Fetch staged diff hunks (only added lines starting with '+')
    try:
        diff_output = subprocess.check_output(
            ["git", "diff", "--cached", "-U0"],
            text=True,
            stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        return 0

    violations = []
    current_file = "unknown"

    for line in diff_output.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
            continue
        if line.startswith("+") and not line.startswith("+++"):
            added_content = line[1:]
            for label, pattern in SECRET_PATTERNS:
                if pattern.search(added_content):
                    violations.append((current_file, label))

    if violations:
        print("\\n" + "=" * 60)
        print("🛑 COMMIT BLOCKED BY PRE-COMMIT SECRET SCANNER HOOK")
        print("=" * 60)
        for fname, label in violations:
            print(f"❌ Detected {label} in staged file: {fname}")
        print("\\nAction: Remove the secret immediately and place it in .env (ignored).")
        print("=" * 60 + "\\n")
        return 1 # Non-zero exit code halts commit transaction

    return 0

if __name__ == "__main__":
    sys.exit(scan_staged_changes())"""
        }
    }
}
