"""Research Agent for thenuke multi-agent authoring system.

Responsible for:
1. Synthesizing deep low-level systems research (POSIX syscalls, C structs, RFCs).
2. Supplying technical dossiers, memory layouts, and architectural edge cases.
3. Providing enterprise postmortems and real-world disaster recovery recipes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ResearchBriefing:
    """Technical research dossier provided to Chapter Writers."""
    phase_num: int
    chapter_num: str
    systems_primitives: List[str]
    c_structs_or_specs: List[str]
    edge_cases: List[str]
    faang_interview_traps: List[str]
    diagram_spec: Optional[str] = None


class ResearchAgent:
    """Specialized Agent responsible for systems research, RFC analysis, and low-level specifications."""

    def __init__(self, topic: str = "Git"):
        self.topic = topic

    def get_briefing(self, phase_num: int, chapter_num: str) -> ResearchBriefing:
        """Returns deep technical dossier for a given chapter."""
        # Key technical dossiers for architectural chapters
        dossiers: Dict[str, ResearchBriefing] = {
            "1.4": ResearchBriefing(
                phase_num=1,
                chapter_num="1.4",
                systems_primitives=[
                    "POSIX write() with atomic fsync() before renaming loose object into .git/objects/xx/yy",
                    "zlib DEFLATE compression with RFC 1950 header",
                    "SHA-1DC (Hardened SHA-1 with collision detection) and SHA-256 object transitions",
                ],
                c_structs_or_specs=[
                    "struct object { unsigned parsed : 1; unsigned type : 3; unsigned flags : 28; struct object_id oid; }",
                    "Header format: '<type> <size>\\0<content>'",
                ],
                edge_cases=[
                    "Hash collisions and SHA-1DC mitigation in Git 2.13+",
                    "Empty blob hash: e69de29bb2d1d6434b8b29ae775ad8c2e48c5391 (git hash-object -t blob /dev/null)",
                    "Permissions stored in Tree objects: only 100644 (regular), 100755 (executable), 120000 (symlink), 040000 (tree), 160000 (submodule)",
                ],
                faang_interview_traps=[
                    "Why doesn't Git store file modification timestamps inside the commit or tree object?",
                    "How does Git ensure cryptographic immutability across the DAG without signing every single file?",
                ],
                diagram_spec="object_model",
            ),
            "2.1": ResearchBriefing(
                phase_num=2,
                chapter_num="2.1",
                systems_primitives=[
                    "lstat() syscall caching to avoid disk reads for clean files",
                    "mmap() memory mapping of .git/index for high-throughput entry traversal",
                    "Index lock file (.git/index.lock) created via O_CREAT | O_EXCL to prevent concurrent write race conditions",
                ],
                c_structs_or_specs=[
                    "struct index_header { uint32_t signature; uint32_t version; uint32_t entries; } // 'DIRC'",
                    "struct cache_entry { struct cache_time ce_ctime; struct cache_time ce_mtime; uint32_t ce_dev; uint32_t ce_ino; uint32_t ce_mode; uint32_t ce_uid; uint32_t ce_gid; uint64_t ce_size; struct object_id oid; uint16_t ce_flags; char name[]; }",
                ],
                edge_cases=[
                    "Index corruption during unexpected machine shutdown when atomic rename of index.lock fails",
                    "Smudge and clean filter transformations (CRLF vs LF, Git LFS pointer replacement)",
                ],
                faang_interview_traps=[
                    "Why is .git/index a binary file instead of human-readable JSON or YAML?",
                    "What happens to git status performance in a repository with 500,000 files when stat cache is invalidated?",
                ],
                diagram_spec="index_binary",
            ),
            "3.1": ResearchBriefing(
                phase_num=3,
                chapter_num="3.1",
                systems_primitives=[
                    "Three Trees separation: disk filesystem vs in-memory binary cache vs immutable object DAG",
                    "Inode metadata checking to optimize dirty detection",
                ],
                c_structs_or_specs=[
                    "unpack_trees_options struct managing two-way and three-way tree traversals in unpack-trees.c",
                ],
                edge_cases=[
                    "Staging partial files while unstaged edits exist simultaneously in the working tree",
                    "Index stage numbers: 0 (normal), 1 (merge base), 2 (ours / HEAD), 3 (theirs / incoming)",
                ],
                faang_interview_traps=[
                    "Differentiate exactly what is modified across the Three Trees during git add, git commit, and git checkout.",
                ],
                diagram_spec="three_trees",
            ),
            "6.1": ResearchBriefing(
                phase_num=6,
                chapter_num="6.1",
                systems_primitives=[
                    "Refs as flat files in .git/refs/heads/ containing 40 hex characters + newline (41 bytes total)",
                    "Packed refs optimization in .git/packed-refs for repositories with thousands of branches",
                ],
                c_structs_or_specs=[
                    "struct ref_store in refs.c handling loose refs, packed refs, and reference transactions",
                ],
                edge_cases=[
                    "Case-insensitive filesystems (macOS / Windows) causing collisions between feature and FEATURE branches",
                    "Branch names with slashes (feature/login) conflicting with existing flat branch names (feature)",
                ],
                faang_interview_traps=[
                    "Why is branch creation in Git an O(1) operation compared to SVN's O(N) directory copy?",
                ],
                diagram_spec="branching_dag",
            ),
            "7.1": ResearchBriefing(
                phase_num=7,
                chapter_num="7.1",
                systems_primitives=[
                    "Graph traversal using Lowest Common Ancestor (LCA) algorithms on the commit DAG",
                    "Virtual commit generation for multiple merge bases (recursive merge strategy)",
                ],
                c_structs_or_specs=[
                    "merge-ort.c (Ostensibly Recursive's Twin) introduced in Git 2.33 replacing merge-recursive.c for 10x-500x speedups",
                ],
                edge_cases=[
                    "Criss-cross merges resulting in two distinct common ancestors and synthetic virtual merge base",
                    "Renaming a file on one branch while modifying the same file on another branch",
                ],
                faang_interview_traps=[
                    "How does git merge-base find the LCA in complex DAGs with criss-cross history?",
                ],
                diagram_spec="three_way_merge",
            ),
            "7.3": ResearchBriefing(
                phase_num=7,
                chapter_num="7.3",
                systems_primitives=[
                    "Index stages 1 (base), 2 (ours), 3 (theirs) populated during merge conflict",
                    "Myers diff alignment generating <<<<<<< HEAD and >>>>>>> conflict markers",
                ],
                c_structs_or_specs=[
                    "diff3 output style displaying the Common Base chunk between ||||||| and =======",
                ],
                edge_cases=[
                    "Binary file conflicts where line-by-line markers cannot be inserted",
                    "Whitespace-only conflicts causing build failures in whitespace-sensitive languages (Python/YAML)",
                ],
                faang_interview_traps=[
                    "How does git rerere identify whether a conflict matches a previously resolved state?",
                ],
                diagram_spec="merge_conflict",
            ),
            "8.1": ResearchBriefing(
                phase_num=8,
                chapter_num="8.1",
                systems_primitives=[
                    "git-cherry-pick mechanics creating brand new commits with new author dates and commit dates",
                    "Detached HEAD state during patch replay sequence",
                ],
                c_structs_or_specs=[
                    ".git/rebase-merge/ and .git/rebase-apply/ state directories holding todo list and patch files",
                ],
                edge_cases=[
                    "Rebasing public shared branches corrupting downstream collaborator commit graphs",
                    "Git rerere auto-resolving rebase conflicts across multiple replayed commits",
                ],
                faang_interview_traps=[
                    "Explain why rebase alters commit SHA-1 hashes even if the code diff is 100% identical.",
                ],
                diagram_spec="rebase_replay",
            ),
            "8.3": ResearchBriefing(
                phase_num=8,
                chapter_num="8.3",
                systems_primitives=[
                    "Pointer relocation in .git/refs/heads/*",
                    "Cache entry unlinking vs filesystem disk unlinking",
                ],
                c_structs_or_specs=[
                    "reset.c executing tree-diff comparisons against target commit tree",
                ],
                edge_cases=[
                    "Accidental git reset --hard and salvaging uncommitted edits if git add was previously executed",
                    "Reflog expiration: default 90 days for reachable, 30 days for unreachable objects",
                ],
                faang_interview_traps=[
                    "Can you recover a file lost to git reset --hard if you never committed it, but ran git add once?",
                ],
                diagram_spec="reset_matrix",
            ),
            "9.1": ResearchBriefing(
                phase_num=9,
                chapter_num="9.1",
                systems_primitives=[
                    "Refspec syntax: +refs/heads/*:refs/remotes/origin/* (+ signifies forced update)",
                    "Smart transport protocol v2 (protocol.version=2) filtering ref advertisement",
                ],
                c_structs_or_specs=[
                    "fetch-pack.c and send-pack.c negotiating common ancestor commit sets across the network socket",
                ],
                edge_cases=[
                    "Divergent remote tracking branch when force pushes happen upstream",
                    "Atomic push (--atomic) ensuring multiple ref updates succeed or fail together",
                ],
                faang_interview_traps=[
                    "Why is git push --force-with-lease safer than git push --force?",
                ],
                diagram_spec="remote_sync",
            ),
        }

        # Default fallback briefing
        return dossiers.get(
            chapter_num,
            ResearchBriefing(
                phase_num=phase_num,
                chapter_num=chapter_num,
                systems_primitives=["POSIX filesystem calls", "Immutable DAG mechanics"],
                c_structs_or_specs=["Git core library structs in cache.h"],
                edge_cases=["Concurrent file locks", "Large working tree stat cache misses"],
                faang_interview_traps=["Explain the time and space complexity of this operation."],
                diagram_spec=None,
            ),
        )
