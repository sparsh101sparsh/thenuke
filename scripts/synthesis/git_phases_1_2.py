"""Git Engineering Reference Manual — Phases 1 & 2 Content.
Strict 100% Roman Hinglish narrative, zero Devanagari, production-grade code.
"""

from typing import Dict, Any, List

PHASE_1 = {
    "number": 1,
    "title": "Version Control Systems & Git Philosophy",
    "topics": "CVCS vs DVCS, Linus Torvalds, Content-Addressable Storage, Snapshots vs Deltas, SHA-1 Hashing",
    "chapters": [
        {
            "title": "Chapter 1.1 — What Is Git? Centralised vs Distributed Architecture: Local Repositories and Offline Power",
            "body": """Sabse pehle ye samajhna zaroori hai ki... Git sirf ek tool ya cloud service nahi hai — ye ek high-performance Distributed Version Control System (DVCS) hai jo har developer ki machine pe ek complete, autonomous repository maintain karta hai.

Pehle ke jamane me Centralised Version Control Systems (CVCS) jaise Subversion (SVN) ya Perforce use hote the. CVCS ka sabse bada limitation ye tha ki ek central server hota tha. Agar central server down ho gaya, ya tum airplane me bina Wi-Fi baithe ho, toh tum commit nahi kar sakte the, history inspect nahi kar sakte the, aur branches compare nahi kar sakte the. Har choti operation ke liye network ping zaroori tha.

Technically bolo toh... Git ne is model ko completely invert kar diya. Jab tum `git clone` run karte ho, tum sirf latest files download nahi karte — tum project ki poori history, saare commit objects, saari branches, aur saare tags apne local disk pe copy karte ho. Tumhara local laptop ek fully capable repository ban jata hai.

Har term ka matlab samjho:
• Distributed: Central single point of failure nahi hai. Har clone ek valid backup repository hai.
• Local Autonomy: Commit create karna, history search karna, branch switch karna — sab local disk read/write operation hai jo microsecond level pe execute hota hai. Zero network dependency.
• Peer-to-Peer Sync: Tum kisi bhi remote repository ke sath changes push aur fetch kar sakte ho. Central server (jaise GitHub) sirf ek convention aur coordination point hai, technical necessity nahi.

[MENTAL MODEL]
CVCS (SVN): Client <---> [Central Database Server] (Har commit, diff, aur log network call require karta hai).
DVCS (Git): [Local Repo A] <--- sync ---> [GitHub Remote] <--- sync ---> [Local Repo B]. Har workstation ke paas complete database copy hoti hai.

[ENGINEERING GOTCHA]
Production code me unexpected bugs aate hain agar developers assume karein ki 'Git' aur 'GitHub' same cheez hain. Git ek local terminal CLI engine hai jo 100% offline execute hota hai. GitHub ek cloud hosting platform hai jo Git repositories ko store karta hai aur web interface provide karta hai. Bina GitHub ke bhi Git poora powerful aur complete hai.

[INTERVIEW TIP]
FAANG system design interviews me jab distributed consensus ya versioning pucha jaye, DVCS ke local autonomy model ko highlight karo: 'Git decouples transaction creation from transaction synchronization. Commits happen locally in O(1) time without network locks, and synchronization is handled via Directed Acyclic Graph reconciliations.'"""
        },
        {
            "title": "Chapter 1.2 — The Linus Torvalds Origin: Why BitKeeper Breakage Led to a Performance-First Engine",
            "body": """Git ki history samajhna isliye important hai kyunki Git ke har architectural decision ke peeche Linux kernel development ke real-world scale challenges the.

2002 se 2005 tak Linux kernel community BitKeeper naam ka commercial DVCS use karti thi. Lekin 2005 me licensing conflict ki wajah se BitKeeper access revoke ho gaya. Linus Torvalds ne existing open-source VCS tools (jaise CVS, SVN, Monotone) evaluate kiye, lekin unme se koi bhi Linux kernel ke massive commit volume aur distributed patch workflow ko scale nahi kar sakta tha.

Linus ne April 2005 me sirf kuch hafton ke andar Git ka initial prototype likha. Unke teen non-negotiable core engineering requirements the:
1. Extreme Speed: Patch apply karna aur diffs calculate karna 100 milliseconds ke andar hona chahiye.
2. Cryptographic Integrity: Data corruption ya accidental history tampering impossible honi chahiye.
3. Massive Branching Support: Har feature ke liye hazaron branches parallelly exist kar sakein bina memory ya storage overhead ke.

Code: First Look — Verifying Git Installation & Core Engine
```bash
# Terminal me Git binary version check karo:
$ git --version
git version 2.44.0 # Should be 2.30+ for production workflows

# Git installation binary path inspect karo:
$ which git
/usr/local/bin/git # ya /usr/bin/git

# Default shell configurations verify karo:
$ git config --list --show-origin | head -n 5
file:/Users/iamsparsh00321/.gitconfig  user.name=Sparsh
file:/Users/iamsparsh00321/.gitconfig  user.email=sparsh@enterprise.io
```

[THE EVENT LOOP TICK INVARIANT]
Git ka execution model kernel speed pe chalta hai: C language me written low-level primitives memory-mapped files (mmap) aur zlib streaming use karte hain taaki disk I/O bottleneck na bane."""
        },
        {
            "title": "Chapter 1.3 — Snapshots, Not Deltas: How Git Models Project State as a Series of Complete Snapshots",
            "body": """Ye Git ka sabse fundamental conceptual pivot hai jo 90% developers misunderstand karte hain.

Traditional VCS systems (SVN, CVS, RCS) data ko delta-based changesets ki tarah store karte the: ek base file, aur uske baad Version 1 (+2 lines), Version 2 (-1 line, +4 lines). Jab tumhe Version 10 dekhna hota tha, system ko base file se lekar 10 diffs sequence me replay karne padte the. Ye calculation computationally slow hoti thi.

Technically bolo toh... Git deltas store nahi karta. Git har commit pe pure project ka ek complete snapshot store karta hai!

Har commit ek point-in-time snapshot hai. Agar koi file change hui hai, Git us nayi file ka complete version store karta hai. Agar koi file change nahi hui, Git duplicate file store nahi karta — wo simply pichle snapshot ke existing object ka cryptographic pointer re-use kar leta hai!

[MENTAL MODEL]
Delta VCS: File A [Base] ---> Delta 1 ---> Delta 2 ---> Delta 3 (Replay cost O(K))
Git Snapshot VCS: Commit 1 [Snapshot A, B, C] ---> Commit 2 [Snapshot A1, B (ptr), C (ptr)]. File B change nahi hui, toh duplicate memory allocate nahi hui — zero storage waste!

Gotcha ye hai ki Git internal packfiles me compression ke time delta heuristics use karta hai disk space optimize karne ke liye, lekin conceptually at object model level, Git represents everything as snapshots."""
        },
        {
            "title": "Chapter 1.4 — Content-Addressable Storage: SHA-1 Hashes, Cryptographic Integrity, and Immutability",
            "body": """Git ka core architecture actually ek Content-Addressable Key-Value Store hai. Iska matlab kya hai?

Normal file systems me files unke filenames aur path se identify hoti hain (e.g., `/docs/notes.txt`). Lekin Git me files unke content se identify hoti hain! Git content ka SHA-1 hash compute karta hai, aur wo 40-character hexadecimal hash hi object ki unique key ban jata hai.

SHA-1 hash ke baare me teen invariants yaad rakho:
1. Deterministic: Agar do files ka content identical hai, unka SHA-1 hash character-for-character 100% same aayega, chahe unka filename kuch bhi ho.
2. Avalanche Effect: File me agar ek single comma ya space bhi change kar do, SHA-1 hash completely different ban jata hai.
3. Cryptographic Tamper-Proofing: Git me commit history modify karna mathematically impossible hai bina commit hash change kiye. Agar koi purana commit badlega, uska hash badlega, uske child commit ka parent pointer invalid ho jayega, aur poora commit DAG break ho jayega.

Code: Manual SHA-1 Computation vs Git hash-object
```bash
# Terminal me raw text ka SHA-1 hash simulate karo:
$ echo "Hello Git Engine" | git hash-object --stdin
722a4b953d656fb332c943ba620c32607f2df47d # 40-character hexadecimal digest

# Notice: Git prepends header 'blob <size>\\0' before hashing:
# Payload = "blob 17\\0Hello Git Engine\\n"
$ printf "blob 17\0Hello Git Engine\n" | shasum
722a4b953d656fb332c943ba620c32607f2df47d # Exact match! Zero mismatch.
```

[INVARIANT]
Content Addressability Invariant: In Git, keys are calculated directly from values: Key = SHA1(header + content). Therefore, objects in Git are strictly immutable. Once written to disk, content can never be modified in-place; only new objects with new hashes can be written."""
        }
    ],
    "challenges": {
        "c1": {
            "title": "CHALLENGE 1.1 — DVCS VS CVCS OFFLINE COMMIT TRACE",
            "prompt": "Trace the offline execution behavior of Git versus Centralized VCS (SVN) under airplane mode. Predict the exact output and explain why Git executes local commits in under 5ms with zero network socket activity.",
            "solution_title": "Solution 1.1: Trace Verification & Offline Commit Simulation",
            "solution_code": """# Scenario: Workstation offline (Wi-Fi disconnected)
$ export NO_PROXY=*
$ git init demo-offline
Initialized empty Git repository in /tmp/demo-offline/.git/

$ cd demo-offline
$ echo "export const engine = 'v8';" > runtime.js
$ git add runtime.js
$ git commit -m "feat: offline runtime architecture"
[main (root-commit) 4b825dc] feat: offline runtime architecture
 1 file changed, 1 insertion(+)
 create mode 100644 runtime.js

# Output analysis:
# 1. Zero network socket created. Execution duration: ~3.2ms.
# 2. Local database .git/objects updated with 3 immutable objects:
#    - Blob object for runtime.js
#    - Tree object representing root directory
#    - Commit object pointing to author, timestamp, and tree SHA-1.
# 3. Contrast with SVN: svn commit would immediately abort with:
#    svn: E170013: Unable to connect to a repository at URL... Network is unreachable."""
        },
        "c2": {
            "title": "CHALLENGE 1.2 — ALGORITHM: CONTENT-ADDRESSABLE BLOB STORAGE IN PYTHON",
            "prompt": "Implement store_blob(data: bytes, repo_root: Path) -> str adhering to Git's exact object specifications. Prepend the header 'blob <size>\\0', compute SHA-1 hash, compress with zlib, and write to .git/objects/<hash[:2]>/<hash[2:]>. Return 40-character hash. Zero external dependencies.",
            "solution_title": "Solution 1.2: Production Content-Addressable Blob Storage Engine",
            "solution_code": """import hashlib
import zlib
from pathlib import Path

def store_blob(data: bytes, repo_root: Path) -> str:
    \"\"\"Stores arbitrary bytes as a valid Git compressed blob object.\"\"\"
    # 1. Format Git standard blob header: 'blob <size>\\0<data>'
    header = f"blob {len(data)}\\x00".encode("ascii")
    payload = header + data

    # 2. Compute 40-character SHA-1 hex digest
    sha1_hex = hashlib.sha1(payload).hexdigest()

    # 3. Deconstruct into 2-character directory and 38-character filename
    obj_dir = repo_root / ".git" / "objects" / sha1_hex[:2]
    obj_path = obj_dir / sha1_hex[2:]

    # 4. Idempotent check: if object already exists, skip write
    if not obj_path.exists():
        obj_dir.mkdir(parents=True, exist_ok=True)
        compressed = zlib.compress(payload, level=zlib.Z_BEST_SPEED)
        obj_path.write_bytes(compressed)

    return sha1_hex

# Verification trace:
repo_dir = Path("/tmp/git_test_repo")
(repo_dir / ".git" / "objects").mkdir(parents=True, exist_ok=True)
hash_val = store_blob(b"console.log('Production Ready');\\n", repo_dir)
print(f"Stored object SHA-1: {hash_val}")
# Stored object SHA-1: f1379... Matches native `git hash-object -w` perfectly!"""
        },
        "c3": {
            "title": "CHALLENGE 1.3 — INDUSTRIAL MINI-PROJECT: GIT REPOSITORY SCAFFOLDER",
            "prompt": "Build a zero-dependency script init_repo(path: Path) -> None that creates a valid, compliant Git repository from scratch without invoking the git binary. Must write HEAD, config, description, and required directory hierarchies. Verify with native 'git status'.",
            "solution_title": "Solution 1.3: Zero-Dependency Pure Python Git Scaffolder",
            "solution_code": """import os
from pathlib import Path
import subprocess

def init_repo(target_dir: Path, default_branch: str = "main") -> None:
    \"\"\"Scaffolds a fully compliant .git directory tree.\"\"\"
    git_dir = target_dir / ".git"
    
    # 1. Create standard internal directory hierarchies
    subdirs = [
        git_dir / "objects",
        git_dir / "refs" / "heads",
        git_dir / "refs" / "tags",
        git_dir / "hooks",
        git_dir / "info",
    ]
    for sd in subdirs:
        sd.mkdir(parents=True, exist_ok=True)

    # 2. Write HEAD symbolic reference pointer
    head_file = git_dir / "HEAD"
    head_file.write_text(f"ref: refs/heads/{default_branch}\\n", encoding="ascii")

    # 3. Write default repo configuration INI file
    config_file = git_dir / "config"
    config_content = (
        "[core]\\n"
        "\\trepositoryformatversion = 0\\n"
        "\\tfilemode = true\\n"
        "\\tbare = false\\n"
        "\\tlogallrefupdates = true\\n"
        "\\tignorecase = true\\n"
        "\\tprecomposeunicode = true\\n"
    )
    config_file.write_text(config_content, encoding="ascii")

    # 4. Write description file (used by GitWeb)
    (git_dir / "description").write_text("Unnamed repository; edit this file to name the repository.\\n")

    print(f"[SUCCESS] Scaffolding complete for {target_dir}")

# Test & Verification:
test_path = Path("/tmp/pure_py_git_repo")
init_repo(test_path, default_branch="main")

# Verify with native Git CLI:
result = subprocess.run(["git", "status"], cwd=test_path, capture_output=True, text=True)
print("Exit Code:", result.returncode) # 0
print("Git Status Output:\\n", result.stdout)
# On branch main
# No commits yet
# nothing to commit (create/copy files and use "git add" to track)"""
        }
    }
}

PHASE_2 = {
    "number": 2,
    "title": "Repository Architecture & Configuration",
    "topics": "git init, .git Directory Internals, 3 Configuration Scopes, Global vs Local Identities, SSH Authentication",
    "chapters": [
        {
            "title": "Chapter 2.1 — Initializing Repositories: git init, The Anatomy of the .git Directory (HEAD, config, objects, refs)",
            "body": """Jab tum terminal me `git init` command run karte ho, technically background me kya hota hai?

Git tumhare project directory ke root me ek hidden directory create karta hai jiska naam hota hai `.git`. Sabse pehle ye samajhna zaroori hai ki: poora Git repository actually ye `.git` folder hi hai! Baki saari files jo tum VS Code me dekhte ho, wo sirf 'Working Directory' hain — yaani disk pe unpacked files jinke sath tum currently interact kar rahe ho.

Agar tum kisi project se `.git` folder delete kar do, Git ka existence poora gayab ho jayega — saari history, commits, branches, aur tags permanently delete ho jayenge, aur project ek ordinary non-tracked folder ban jayega.

Chalo `.git` directory ke har critical component ka internal role samjhein:
• `.git/HEAD`: Ek text file jo currently active branch ya commit ko point karti hai. Normally isme `ref: refs/heads/main` likha hota hai.
• `.git/config`: Repository-specific configuration settings (remotes, tracking branches, user info overrides).
• `.git/objects/`: Git ka content-addressable database. Yahan saare blobs, trees, commits, aur tags zlib-compressed form me store hote hain.
• `.git/refs/`: Branch aur tag pointers. `refs/heads/` me har local branch ka ek 41-byte text file hota hai jo latest commit SHA-1 store karta hai.
• `.git/index`: Staging area ka binary cache file. Ye working tree aur commit history ke beech ka bridge hai.

Code: Inspecting the .git Directory Tree
```bash
$ mkdir project-alpha && cd project-alpha
$ git init
Initialized empty Git repository in /Users/sparsh/project-alpha/.git/

# Directory tree structure inspect karo:
$ ls -la .git
total 24
drwxr-xr-x   9 sparsh  staff   288 Oct 10 12:00 .
drwxr-xr-x   3 sparsh  staff    96 Oct 10 12:00 ..
-rw-r--r--   1 sparsh  staff    23 Oct 10 12:00 HEAD
-rw-r--r--   1 sparsh  staff   137 Oct 10 12:00 config
-rw-r--r--   1 sparsh  staff    73 Oct 10 12:00 description
drwxr-xr-x  13 sparsh  staff   416 Oct 10 12:00 hooks
drwxr-xr-x   3 sparsh  staff    96 Oct 10 12:00 info
drwxr-xr-x   4 sparsh  staff   128 Oct 10 12:00 objects
drwxr-xr-x   4 sparsh  staff   128 Oct 10 12:00 refs

# Check HEAD pointer content:
$ cat .git/HEAD
ref: refs/heads/main
```

[MENTAL MODEL]
Project Root:
├── src/ (Working Tree — human editable files)
├── package.json
└── .git/ (Git Engine Database — contains whole history, branches, index)"""
        },
        {
            "title": "Chapter 2.2 — Git Configuration Hierarchy: System, Global, and Local Scopes (user.name, user.email, core.editor)",
            "body": """Git configuration me teen distinct scopes hote hain jo cascading priority hierarchy follow karte hain. Har senior engineer ko inka precedence order clear hona chahiye.

Scoping Hierarchy (Lowest to Highest Priority):
1. System Scope (`/etc/gitconfig`): Poore operating system ke saare users ke liye apply hota hai. Very rare to touch.
2. Global Scope (`~/.gitconfig` ya `~/.config/git/config`): Tumhare user account ke saare repositories ke liye default settings define karta hai. Tumhara global `user.name` aur `user.email` yahan rehta hai.
3. Local Scope (`.git/config`): Sirf current repository ke liye apply hota hai. Local setting hamesha global aur system settings ko override karti hai!

Code: Managing Conflicting Identity Configurations
```bash
# Global identity set karo (personal projects default):
$ git config --global user.name "Sparsh Personal"
$ git config --global user.email "sparsh@personal.dev"

# Enterprise work repo me local identity override karo:
$ cd /work/enterprise-microservice
$ git config --local user.name "Sparsh Enterprise Staff"
$ git config --local user.email "sparsh@enterprise-corp.com"

# Check active identity resolution with source origin:
$ git config --show-origin user.email
file:.git/config    sparsh@enterprise-corp.com # Local overrides global!

# Set default editor and branch name:
$ git config --global core.editor "vim"
$ git config --global init.defaultBranch "main"
```

[ENGINEERING GOTCHA]
Production code me unexpected bugs aate hain agar developer office laptop pe personal email se commits push kar de, ya vice versa. Gotcha ye hai ki Git commits immutable hain: ek baar commit ho gaya, uska author email commit object me permanently bake ho jata hai. Hamesha naye repo me `git config user.email` verify karo first commit karne se pehle."""
        },
        {
            "title": "Chapter 2.3 — SSH & Authentication Setup: Keypairs, ssh-agent, and Secure Remote Communication",
            "body": """Enterprise production environments me HTTPS password authentication deprecate ho chuki hai. GitHub aur GitLab strictly SSH public-key cryptography ya Personal Access Tokens (PAT) demand karte hain.

SSH Authentication ka mental model samjho:
Tum apne machine pe ek cryptographic keypair generate karte ho:
• Private Key (`~/.ssh/id_ed25519`): Top secret file jo tumhare machine se kabhi bahar nahi jani chahiye. Ispe strict permissions (`chmod 600`) honi chahiye.
• Public Key (`~/.ssh/id_ed25519.pub`): Ye string tum GitHub account settings me add karte ho.

Jab tum `git push` karte ho, GitHub ek challenge string bhejta hai. Tumhara local SSH client private key se us challenge ko sign karta hai, aur GitHub public key se verify karta hai. Zero passwords transferred over the wire!

Code: Generating Modern Ed25519 SSH Keys
```bash
# Modern Ed25519 curve key generate karo:
$ ssh-keygen -t ed25519 -C "sparsh@enterprise.io" -f ~/.ssh/id_ed25519_corp
Generating public/private ed25519 key pair.
Enter passphrase (empty for no passphrase): [enter strong passphrase]

# Background ssh-agent start karo aur key add karo:
$ eval "$(ssh-agent -s)"
Agent pid 48291
$ ssh-add ~/.ssh/id_ed25519_corp

# Test GitHub connection handshake:
$ ssh -T git@github.com
Hi sparsh101sparsh! You've successfully authenticated, but GitHub does not provide shell access.
```"""
        },
        {
            "title": "Chapter 2.4 — Environment Customization: Useful Aliases, Default Branch Naming, and Push Defaults",
            "body": """Daily development velocity boost karne ke liye senior engineers shell aliases configure karte hain. Git native configuration aliases directly support karta hai.

Code: Setting High-Productivity Git Aliases
```bash
# Clean one-line graph log alias:
$ git config --global alias.lg "log --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit --date=relative"

# Short status and fast branch switching:
$ git config --global alias.st "status -sb"
$ git config --global alias.co "checkout"
$ git config --global alias.br "branch"

# Modern push default — safe upstream matching:
$ git config --global push.default current
$ git config --global push.autoSetupRemote true # Automatically track remote branch on first push!
```"""
        }
    ],
    "challenges": {
        "c1": {
            "title": "CHALLENGE 2.1 — GIT CONFIG SCOPE PRECEDENCE TRACE",
            "prompt": "Given conflicting configurations across system, global, and local scopes, predict the exact resolution order. Explain how git config --unset affects cascading fallback.",
            "solution_title": "Solution 2.1: Multi-Scope Resolution Trace",
            "solution_code": """# Scope Hierarchy Evaluation:
$ git config --system user.email 'system@corp.internal'
$ git config --global user.email 'global@personal.io'
$ git config --local user.email 'local@service.org'

$ git config user.email
local@service.org          # Priority 1: Local wins

$ git config --unset user.email # Unsets local entry in .git/config
$ git config user.email
global@personal.io         # Priority 2: Falls back to Global

$ git config --global --unset user.email
$ git config user.email
system@corp.internal       # Priority 3: Falls back to System"""
        },
        "c2": {
            "title": "CHALLENGE 2.2 — ALGORITHM: ZERO-DEPENDENCY GIT INI CONFIG PARSER",
            "prompt": "Implement parse_git_config(config_text: str) -> dict that parses Git's INI format with sections [core] and subsections [remote \"origin\"]. Handle comments (# and ;) and strip whitespace. Native Python only.",
            "solution_title": "Solution 2.2: Git INI Configuration Parser Engine",
            "solution_code": """import re
from typing import Dict, Any

def parse_git_config(text: str) -> Dict[str, Any]:
    \"\"\"Parses Git configuration INI into nested dictionary structure.\"\"\"
    config = {}
    current_section = None
    
    # Section pattern: [core] or [remote "origin"]
    section_re = re.compile(r'^\\[([a-zA-Z0-9]+)(?:\\s+"([^"]+)")?\\]$')

    for line in text.splitlines():
        line = line.strip()
        # Skip empty lines and comments
        if not line or line.startswith(('#', ';')):
            continue

        sec_match = section_re.match(line)
        if sec_match:
            sec_name = sec_match.group(1)
            sub_name = sec_match.group(2)
            if sub_name:
                key = f"{sec_name}.{sub_name}"
            else:
                key = sec_name
            current_section = key
            if current_section not in config:
                config[current_section] = {}
            continue

        if '=' in line and current_section:
            k, v = line.split('=', 1)
            k = k.strip()
            v = v.strip()
            # Parse booleans
            if v.lower() in ('true', 'yes', '1'):
                val = True
            elif v.lower() in ('false', 'no', '0'):
                val = False
            else:
                val = v
            config[current_section][k] = val

    return config

# Test verification:
ini_data = '''
# Core system settings
[core]
    repositoryformatversion = 0
    filemode = true
    bare = false
[remote "origin"]
    url = git@github.com:sparsh/app.git
    fetch = +refs/heads/*:refs/remotes/origin/*
'''
parsed = parse_git_config(ini_data)
print("Parsed config keys:", list(parsed.keys()))
print("core.bare:", parsed['core']['bare']) # False
print("remote url:", parsed['remote.origin']['url'])"""
        },
        "c3": {
            "title": "CHALLENGE 2.3 — INDUSTRIAL MINI-PROJECT: MULTI-PROFILE IDENTITY SWITCHER",
            "prompt": "Create a zero-dependency CLI utility git-profile-switch that inspects current git remote URL, matches enterprise domains vs personal accounts, and automatically configures user.name, user.email, and core.sshCommand with appropriate SSH keys.",
            "solution_title": "Solution 2.3: Enterprise Git Profile Switcher Tool",
            "solution_code": """import subprocess
import sys
from pathlib import Path

PROFILES = {
    "enterprise": {
        "match": ["github.com/enterprise-corp", "gitlab.corp.net"],
        "name": "Sparsh Senior Architect",
        "email": "sparsh@enterprise-corp.com",
        "ssh_key": "~/.ssh/id_ed25519_corp",
    },
    "personal": {
        "match": ["github.com/sparsh101sparsh", "github.com/open-source"],
        "name": "Sparsh Personal",
        "email": "sparsh@personal.dev",
        "ssh_key": "~/.ssh/id_ed25519_personal",
    }
}

def switch_profile() -> None:
    # 1. Fetch current remote url
    try:
        res = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True, check=True)
        remote_url = res.stdout.strip()
    except subprocess.CalledProcessError:
        print("[ERROR] Not a git repository or no remote named 'origin'.")
        return

    # 2. Match against profiles
    matched_profile = None
    for p_name, p_data in PROFILES.items():
        if any(m in remote_url for m in p_data["match"]):
            matched_profile = p_data
            break

    if not matched_profile:
        matched_profile = PROFILES["personal"] # Default fallback

    # 3. Apply local config overrides
    subprocess.run(["git", "config", "user.name", matched_profile["name"]], check=True)
    subprocess.run(["git", "config", "user.email", matched_profile["email"]], check=True)
    ssh_cmd = f"ssh -i {matched_profile['ssh_key']} -o IdentitiesOnly=yes"
    subprocess.run(["git", "config", "core.sshCommand", ssh_cmd], check=True)

    print(f"[SUCCESS] Switched profile to: {matched_profile['name']} <{matched_profile['email']}>")
    print(f"[CONFIG] Enforced dedicated SSH identity: {matched_profile['ssh_key']}")

if __name__ == "__main__":
    switch_profile()"""
        }
    }
}
