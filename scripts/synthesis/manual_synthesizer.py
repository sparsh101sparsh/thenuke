"""Reference Manual Synthesis Engine for thenuke skill.

Implements Milestone 3 (R3) requirements:
- 100% Roman-alphabet Hinglish prose (zero Devanagari Unicode characters).
- Dual-register cadence: conversational Roman Hinglish bridges + formal English technical terms.
- Multi-part Syllabus Index (PART I to VI) at front-matter.
- 9-Phase blueprint with appendices.
- Capitalized Bracketed Callouts: [MENTAL MODEL], [INVARIANT], [ENGINEERING GOTCHA], [INTERVIEW TIP].
- 3-part Mandatory Phase Challenges: Output Prediction, Algorithm Utility, Industrial Mini-Project.
- ES2024+ code snippets, zero npm dependencies, inline output comments, anti-toy-code policy.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Devanagari Detection — ABSOLUTE ZERO TOLERANCE
# ---------------------------------------------------------------------------

_DEVANAGARI_PATTERN = re.compile(
    r"[\u0900-\u097F\uA8E0-\uA8FF\u1CD0-\u1CFF\u0900-\u0963]"
)

_VALID_CALLOUT_LABELS = frozenset({
    "[MENTAL MODEL]",
    "[INVARIANT]",
    "[THE EVENT LOOP TICK INVARIANT]",
    "[CALL STACK MENTAL MODEL]",
    "[ENGINEERING GOTCHA]",
    "[INTERVIEW TIP]",
    "[PRODUCTION INVARIANT]",
    "[MEMORY MODEL]",
    "[PROTOTYPE CHAIN INVARIANT]",
    "[V8 INTERNALS]",
    "[FAANG SIGNAL]",
})

PHASE_CATALOG: List[Dict[str, Any]] = [
    {
        "number": 1,
        "title": "Core Foundations",
        "topics": "Variables, Scoping, Types, Coercion, Memory Layout, Execution Context",
        "chapters": [
            "1.1 — Variables & Declarations: var, let, const aur Temporal Dead Zone",
            "1.2 — Type System & Coercion: Primitive vs Reference Types aur Implicit Conversion",
            "1.3 — Execution Context & Scope Chain: Lexical Environment Record aur Scope Resolution",
            "1.4 — Memory Layout: Stack Frame vs Heap Allocation aur Garbage Collection Roots",
        ],
    },
    {
        "number": 2,
        "title": "Control Flow, Functions & Execution Engine",
        "topics": "Closures, Hoisting, Call Stack, First-Class Functions, IIFE, Higher-Order Functions",
        "chapters": [
            "2.1 — Hoisting Deep Dive: Variable vs Function Declaration Lifting",
            "2.2 — Closures & Lexical Scope: Ye memory leak nahi — ye by design hai",
            "2.3 — Call Stack Mental Model: Frame Creation, LIFO Execution, Stack Overflow",
            "2.4 — Higher-Order Functions: map, filter, reduce — Pure Functional Utilities",
            "2.5 — IIFE & Module Patterns: Encapsulation Before ES Modules",
        ],
    },
    {
        "number": 3,
        "title": "Data Structures & Functional Utilities",
        "topics": "Arrays, Maps, Sets, WeakMap, WeakSet, Iterators, Generators, Symbols",
        "chapters": [
            "3.1 — Array Internals: Dense vs Sparse Arrays, Change-by-Copy Methods (ES2024+)",
            "3.2 — Map & Set: Hash Table Internals vs Object Keys aur Iteration Order",
            "3.3 — WeakMap & WeakRef: Controlled Memory Pressure aur Garbage Collection Integration",
            "3.4 — Iterators & Generators: Lazy Evaluation Protocol aur Custom Iterables",
            "3.5 — Symbol & Well-Known Symbols: [Symbol.iterator], [Symbol.toPrimitive]",
        ],
    },
    {
        "number": 4,
        "title": "Object Models & Prototypes",
        "topics": "Prototype Chain, Object.create, Classes (ES2022+), Private Fields, Mixins",
        "chapters": [
            "4.1 — Prototype Chain: [[Prototype]] Internal Slot aur Property Lookup Walk",
            "4.2 — Object.create & Differential Inheritance: Bina Constructor ke Inheritance",
            "4.3 — ES2022+ Class Syntax: Private Fields (#), Static Blocks, Auto-Accessors",
            "4.4 — Mixins & Composition: Horizontal Code Reuse Without Inheritance Tax",
            "4.5 — Reflection & Descriptors: Object.defineProperty, getOwnPropertyDescriptor",
        ],
    },
    {
        "number": 5,
        "title": "Asynchronous Concurrency & Event Loop",
        "topics": "Event Loop, Microtask Queue, Macrotask Queue, Promises, async/await, AbortController",
        "chapters": [
            "5.1 — Event Loop Architecture: Call Stack, Microtask Queue, Task Queue Pipeline",
            "5.2 — Promises: Specification-Level Behaviour, Chaining, Error Propagation",
            "5.3 — async/await: Syntactic Sugar Over Generators aur Promise Internals",
            "5.4 — Microtask Draining: queueMicrotask, MutationObserver, Promise.resolve Ordering",
            "5.5 — Concurrency Primitives: AbortController, Promise.allSettled, Promise.withResolvers (ES2024+)",
            "5.6 — Worker Threads & SharedArrayBuffer: True Parallelism aur Atomics",
        ],
    },
    {
        "number": 6,
        "title": "Browser DOM & Event Pipelines",
        "topics": "DOM Tree, Event Delegation, Capture vs Bubble, Custom Events, IntersectionObserver",
        "chapters": [
            "6.1 — DOM Tree Model: Node Hierarchy, Render Tree, Critical Rendering Path",
            "6.2 — Event Propagation: Capture Phase, Target Phase, Bubble Phase",
            "6.3 — Event Delegation: Performance-Optimal Listener Strategy for Dynamic Lists",
            "6.4 — Custom Events & Eventing Patterns: EventTarget ye nahi ki sirf DOM pe",
            "6.5 — Browser Performance APIs: IntersectionObserver, ResizeObserver, Performance Timeline",
        ],
    },
    {
        "number": 7,
        "title": "Advanced Metaprogramming & Performance",
        "topics": "Proxy, Reflect, Symbol.hasInstance, TurboFan JIT, Monomorphic Dispatch, V8 Optimization",
        "chapters": [
            "7.1 — Proxy & Reflect: Intercepting Object Operations at Runtime",
            "7.2 — V8 Ignition & TurboFan: Bytecode Interpretation aur JIT Optimization Pipeline",
            "7.3 — Monomorphic vs Megamorphic Dispatch: Hidden Classes aur Inline Cache Hits",
            "7.4 — Memory Profiling: Chrome DevTools Heap Snapshots aur Allocation Timelines",
            "7.5 — Code Optimization Patterns: De-opt Triggers, Hot Functions, Escape Analysis",
        ],
    },
    {
        "number": 8,
        "title": "System Internals & Backend Architecture",
        "topics": "Node.js Event Loop, libuv, Streams, Cluster, Worker Threads, HTTP/2, Security",
        "chapters": [
            "8.1 — Node.js Event Loop: libuv Phase Architecture (timers, I/O, idle, poll, check, close)",
            "8.2 — Streams API: Readable, Writable, Transform — Backpressure aur Piping",
            "8.3 — Cluster & Child Processes: Multi-Core CPU Utilization Without Shared State",
            "8.4 — HTTP/2 Multiplexing: Header Compression, Server Push, Stream Prioritization",
            "8.5 — OWASP Top 10 in Node.js: Injection, XSS, CSRF, Supply Chain Attacks",
        ],
    },
    {
        "number": 9,
        "title": "Production Capstone Project",
        "topics": "Zero-dependency CLI Engine, In-Memory Rate Limiter, LRU Cache, HTTP Router, Mini Test Runner",
        "chapters": [
            "9.1 — Zero-Dependency HTTP Router: Trie-Based Path Matching with Parameter Extraction",
            "9.2 — In-Memory LRU Cache: Doubly Linked List + HashMap in O(1)",
            "9.3 — Token Bucket Rate Limiter: Production-Grade Request Throttling",
            "9.4 — Composable Middleware Pipeline: koa-style compose() in 10 Lines",
            "9.5 — Mini Test Runner: TAP-Compatible with Async Support aur Diff Output",
        ],
    },
]

APPENDICES: List[Dict[str, str]] = [
    {"title": "Appendix A — V8 Engine Deep Dive", "scope": "Ignition Bytecode, TurboFan JIT, Garbage Collection Phases, Object Layout"},
    {"title": "Appendix B — OWASP Security Gauntlet", "scope": "Top 10 Vulnerabilities, Mitigations, Secure Defaults, CSP Headers"},
    {"title": "Appendix C — Machine Coding Gauntlet", "scope": "30 FAANG-Style System Design Coding Problems with Constraints & Solutions"},
]


GIT_PHASE_CATALOG: List[Dict[str, Any]] = [
    {
        "number": 1,
        "title": "Version Control Systems & Git Philosophy",
        "topics": "CVCS vs DVCS, Linus Torvalds, Content-Addressable Storage, Snapshots vs Deltas",
        "chapters": [
            "1.1 — What Is Git? Centralised vs Distributed Architecture: Local Repositories and Offline Power",
            "1.2 — The Linus Torvalds Origin: Why BitKeeper Breakage Led to a Performance-First Engine",
            "1.3 — Snapshots, Not Deltas: How Git Models Project State as a Series of Complete Snapshots",
            "1.4 — Content-Addressable Storage: SHA-1 Hashes, Cryptographic Integrity, and Immutability",
        ],
    },
    {
        "number": 2,
        "title": "Repository Architecture & Configuration",
        "topics": "git init, .git Directory Internals, 3 Configuration Scopes, Global vs Local Identities",
        "chapters": [
            "2.1 — Initializing Repositories: git init, The Anatomy of the .git Directory (HEAD, config, objects, refs)",
            "2.2 — Git Configuration Hierarchy: System, Global, and Local Scopes (user.name, user.email, core.editor)",
            "2.3 — SSH & Authentication Setup: Keypairs, ssh-agent, and Secure Remote Communication",
            "2.4 — Environment Customization: Useful Aliases, Default Branch Naming, and Push Defaults",
        ],
    },
    {
        "number": 3,
        "title": "The Three Trees & Core Lifecycle",
        "topics": "Working Directory, Staging Area (Index), Repository (HEAD), git add, git commit, git status",
        "chapters": [
            "3.1 — The Three Trees Mental Model: Working Tree, Index/Staging Area, and HEAD Commit",
            "3.2 — Staging Files: git add Deep Dive, Tracking New vs Modified Files, Staging Partial Hunks",
            "3.3 — Atomic Commits: git commit, Commit Messages as Historical Documentation, Conventional Commits",
            "3.4 — Inspecting State: git status Invariants, Untracked vs Tracked, Changes Staged for Commit",
        ],
    },
    {
        "number": 4,
        "title": "File Tracking, Ignoring & Tree Cleanliness",
        "topics": ".gitignore Rules, Pattern Syntax, Untracking Cached Files, .gitkeep Conventions",
        "chapters": [
            "4.1 — Ignoring Files: .gitignore Syntax, Wildcards, Negation (!), and Directory Anchoring",
            "4.2 — Untracking Already Committed Files: git rm --cached and Clearing the Index Cache",
            "4.3 — Tracking Empty Directories: The .gitkeep Convention vs Git's Inability to Track Empty Trees",
            "4.4 — Cleaning the Working Tree: git clean Flags (-n dry run, -fd), Safeguards Against Data Loss",
        ],
    },
    {
        "number": 5,
        "title": "History Inspection & Diffing Engine",
        "topics": "git log Formatting, Revision Walk, Commit Ranges, git diff Engine, git show",
        "chapters": [
            "5.1 — Navigating History: git log Flags (--oneline, --graph, --decorate, --stat, -p)",
            "5.2 — Inspecting Diffs: git diff (Working Tree vs Index) vs git diff --staged (Index vs HEAD)",
            "5.3 — Comparing Branches and Commits: Double-Dot (..) vs Triple-Dot (...) Range Semantics",
            "5.4 — Single Object Inspection: git show, Examining Specific Blobs and Commits via SHA-1",
        ],
    },
    {
        "number": 6,
        "title": "Branching & Pointer Mechanics",
        "topics": "Branch as a 41-Byte Pointer, git branch, git checkout, git switch, Detached HEAD State",
        "chapters": [
            "6.1 — Branch Architecture: Why Git Branches Are Cheap 41-Byte SHA-1 Pointer Files in refs/heads/",
            "6.2 — Branch Creation & Switching: git branch vs git switch vs git checkout (-b)",
            "6.3 — The Detached HEAD State: What Happens When HEAD Points to a Commit Instead of a Branch Ref",
            "6.4 — Deleting and Renaming Branches: Safe Delete (-d) vs Force Delete (-D), Upstream Tracking",
        ],
    },
    {
        "number": 7,
        "title": "Merging Strategies & Conflict Resolution",
        "topics": "Fast-Forward Merge, Three-Way Merge, Common Ancestor (Merge Base), Conflict Markers, Resolution",
        "chapters": [
            "7.1 — Fast-Forward Merges: Linear History Extension When No Divergence Exists",
            "7.2 — Three-Way Merges: Recursive/Ort Strategy, Merge Commits with Two Parents, Finding the Merge Base",
            "7.3 — Merge Conflict Anatomy: Understanding Conflict Markers (<<<<<<<, =======, >>>>>>>)",
            "7.4 — Conflict Resolution Workflow: Editing Markers, git add to Mark Resolved, git merge --abort",
        ],
    },
    {
        "number": 8,
        "title": "Advanced Working Tree Manipulation & Stashing",
        "topics": "git stash Stack, Stash Internals, git restore, Lightweight vs Annotated Tags",
        "chapters": [
            "8.1 — Stashing Uncommitted Changes: git stash push, git stash pop vs apply, Inspecting the Stash Stack",
            "8.2 — Stashing Untracked Files (-u) and Stash Branching: Safely Context-Switching in Mid-Feature",
            "8.3 — Undoing Changes in the Modern Era: git restore (--staged vs working tree) vs Legacy git checkout",
            "8.4 — Git Tags & Semantic Releases: Lightweight Tags vs Annotated Tags (git tag -a -m), GPG Signing",
        ],
    },
    {
        "number": 9,
        "title": "History Rewriting, Rebase & Distributed Workflows",
        "topics": "git rebase, Interactive Rebase (-i), Golden Rule of Rebasing, Remote Workflows, Pull Requests",
        "chapters": [
            "9.1 — Git Rebase Fundamentals: Replaying Commits Onto a New Base, Linearizing Commit History",
            "9.2 — Interactive Rebase (git rebase -i): Squashing, Fixups, Rewording, and Dropping Commits",
            "9.3 — The Golden Rule of Rebasing: Never Rebase Commits That Have Been Pushed to Public Remotes",
            "9.4 — Remote Operations: git remote, git fetch vs git pull (--rebase), git push (--force-with-lease)",
            "9.5 — Enterprise Collaborative Workflows: GitHub Flow vs Trunk-Based Development vs Gitflow",
        ],
    },
]

GIT_APPENDICES: List[Dict[str, str]] = [
    {
        "title": "Appendix A — Git Plumbing & Object Database Internals",
        "scope": "The 4 Object Types (Blobs, Trees, Commits, Annotated Tags), zlib Compression, git cat-file, Packed Refs",
    },
    {
        "title": "Appendix B — The Catastrophe Recovery Gauntlet",
        "scope": "git reflog Navigation, Recovering Deleted Branches, Dangling Commits Recovery, git fsck Integrity Verification",
    },
    {
        "title": "Appendix C — 30 FAANG Version Control Machine Coding & Scenario Questions",
        "scope": "Design a Distributed Version Control System, Implement Commit DAG Topological Sort, Resolve Multi-Way Divergence",
    },
]

ROMAN_HINGLISH_BRIDGES = [
    "Technically bolo toh...",
    "Har term ka matlab samjho:",
    "Ye sunke lagta hai ki...",
    "Sabse pehle ye samajhna zaroori hai ki...",
    "Gotcha ye hai ki...",
    "Pehle aisa hota tha, ab...",
    "Bas — tumhara code ready hai.",
    "Production code me unexpected bugs aate hain agar...",
    "Ek important baat ye hai ki...",
    "Ye concept seedha interview me aata hai:",
    "Real-world applications me...",
    "Engine level pe kya hota hai:",
]


# ---------------------------------------------------------------------------
# Core Data Structures
# ---------------------------------------------------------------------------

@dataclass
class PhaseChallenge:
    """3-part mandatory end-of-phase drill specification."""
    phase_number: int
    challenge_1_title: str
    challenge_1_prompt: str
    challenge_2_title: str
    challenge_2_prompt: str
    challenge_3_title: str
    challenge_3_prompt: str


@dataclass
class SynthesisConfig:
    """Configuration driving the manual synthesis process."""
    topic: str = "JavaScript"
    level_of_detail: str = "senior_architect"  # foundations | resource_parity | senior_architect
    visual_threshold: str = "strict_need_based"  # strict_need_based | balanced | diagram_dense
    audience_focus: str = "faang_interview"  # faang_interview | production_engineering | academic_foundations
    phases_to_include: List[int] = field(default_factory=lambda: list(range(1, 10)))
    include_appendices: bool = True
    output_dir: Optional[str] = None


@dataclass
class SynthesizedChapter:
    """A single chapter of synthesized content."""
    phase_number: int
    chapter_index: int
    title: str
    body_markdown: str
    callouts: List[str] = field(default_factory=list)
    code_blocks: List[str] = field(default_factory=list)


@dataclass
class SynthesizedPhase:
    """A complete phase with all chapters and end-of-phase challenges."""
    number: int
    title: str
    topics: str
    chapters: List[SynthesizedChapter]
    challenge: PhaseChallenge


@dataclass
class SynthesizedManual:
    """Complete synthesized reference manual."""
    topic: str
    generated_at: str
    syllabus_index: str
    phases: List[SynthesizedPhase]
    appendix_index: str
    config: SynthesisConfig


# ---------------------------------------------------------------------------
# Devanagari Validator
# ---------------------------------------------------------------------------

def validate_zero_devanagari(text: str) -> List[str]:
    """Return list of Devanagari characters found in text. Empty = compliant."""
    violations: List[str] = []
    for match in _DEVANAGARI_PATTERN.finditer(text):
        violations.append(
            f"Devanagari char U+{ord(match.group()):04X} '{match.group()}' at position {match.start()}"
        )
    return violations


def assert_zero_devanagari(text: str, context: str = "") -> None:
    """Raise ValueError if any Devanagari characters found."""
    violations = validate_zero_devanagari(text)
    if violations:
        preview = "\n  ".join(violations[:5])
        raise ValueError(
            f"DEVANAGARI VIOLATION in {context or 'text'} — {len(violations)} occurrence(s):\n  {preview}"
        )


# ---------------------------------------------------------------------------
# Syllabus Index Generator
# ---------------------------------------------------------------------------

def generate_syllabus_index(phases: Sequence[Dict[str, Any]], appendices: Sequence[Dict[str, str]], topic_name: str = "JavaScript") -> str:
    """Generate the front-matter multi-part syllabus index."""
    parts: List[str] = []
    parts.append("=" * 80)
    parts.append("DETAILED SYLLABUS & TABLE OF CONTENTS")
    # topic_name embedded here so Devanagari in topic gets caught by assert_zero_devanagari
    parts.append(f"{topic_name}: The Complete Reference Manual — Architecture & Core Internals")
    parts.append("=" * 80)
    parts.append("")

    # Group phases into 3 parts of 3 phases each
    part_labels = ["PART I", "PART II", "PART III", "PART IV", "PART V", "PART VI"]
    for part_idx, phase_group_start in enumerate(range(0, len(phases), 3)):
        group = phases[phase_group_start : phase_group_start + 3]
        if not group:
            break
        part_label = part_labels[part_idx] if part_idx < len(part_labels) else f"PART {part_idx + 1}"
        parts.append(f"{part_label}")
        parts.append("-" * 40)
        for phase in group:
            parts.append(f"  Phase {phase['number']}: {phase['title']}")
            parts.append(f"    Topics: {phase['topics']}")
            for ch in phase.get("chapters", []):
                parts.append(f"      Chapter {ch}")
            parts.append(f"    Phase {phase['number']} End Challenges:")
            parts.append(f"      Challenge 1: Output Prediction & Trace Drill")
            parts.append(f"      Challenge 2: Algorithm / Core Utility Implementation")
            parts.append(f"      Challenge 3: Industrial Mini-Project / System Component")
            parts.append("")
        parts.append("")

    if appendices:
        parts.append("APPENDICES")
        parts.append("-" * 40)
        for app in appendices:
            parts.append(f"  {app['title']}")
            parts.append(f"    Scope: {app['scope']}")
        parts.append("")

    result = "\n".join(parts)
    assert_zero_devanagari(result, context="syllabus_index")
    return result


# ---------------------------------------------------------------------------
# Phase Challenge Generator
# ---------------------------------------------------------------------------

_PHASE_CHALLENGES: Dict[int, PhaseChallenge] = {
    1: PhaseChallenge(
        phase_number=1,
        challenge_1_title="Output Prediction: Hoisting & TDZ Trace",
        challenge_1_prompt=(
            "Predict the exact console output and thrown errors for the following execution snippet.\n"
            "Annotate each line with its runtime evaluation result.\n\n"
            "```javascript\n"
            "console.log(typeof notDeclared);        // ?\n"
            "console.log(typeof letBinding);         // ?\n"
            "let letBinding = 'initialized';\n"
            "var varBinding = 'hoisted';\n"
            "function outer() {\n"
            "  console.log(varBinding);              // ?\n"
            "  var varBinding = 'shadowed';\n"
            "  console.log(varBinding);              // ?\n"
            "  (() => console.log(letBinding))();    // ?\n"
            "}\n"
            "outer();\n"
            "```\n\n"
            "Constraints: No execution allowed. Trace static analysis through V8 Ignition's variable binding phase."
        ),
        challenge_2_title="Algorithm: Zero-Dependency Deep Clone",
        challenge_2_prompt=(
            "Implement a production-grade `deepClone(value)` function with the following constraints:\n"
            "- Handle: primitives, Date, RegExp, Map, Set, Array, plain Object, circular references.\n"
            "- Zero npm dependencies. Native ES2024+ APIs only.\n"
            "- Time complexity: O(n) where n = total node count. Space: O(n) for cycle detection.\n"
            "- Must not use `JSON.parse(JSON.stringify())` (loses Date, RegExp, Map, Set, undefined).\n"
            "- Include inline output comments demonstrating correctness on circular graphs."
        ),
        challenge_3_title="Industrial Mini-Project: In-Memory Configuration Store",
        challenge_3_prompt=(
            "Build a zero-dependency, type-safe in-memory Configuration Store with the following API:\n"
            "- `ConfigStore.create(schema)` — factory accepting a JSON Schema-like descriptor.\n"
            "- `store.set(key, value)` — validates type against schema, throws on mismatch.\n"
            "- `store.get(key)` — returns typed value with default fallback.\n"
            "- `store.watch(key, callback)` — reactive subscription (synchronous notification).\n"
            "- `store.snapshot()` — returns an immutable deep-frozen copy of all config.\n"
            "Deliver a complete implementation with inline output annotations and 0 external imports."
        ),
    ),
    2: PhaseChallenge(
        phase_number=2,
        challenge_1_title="Output Prediction: Closure & IIFE Trace",
        challenge_1_prompt=(
            "Predict the exact output. Trace each closure's captured Lexical Environment Record.\n\n"
            "```javascript\n"
            "const counters = [];\n"
            "for (var i = 0; i < 3; i++) {\n"
            "  counters.push(() => i);\n"
            "}\n"
            "console.log(counters.map(fn => fn())); // ?\n"
            "\n"
            "const correctCounters = [];\n"
            "for (let j = 0; j < 3; j++) {\n"
            "  correctCounters.push(() => j);\n"
            "}\n"
            "console.log(correctCounters.map(fn => fn())); // ?\n"
            "```\n\n"
            "Explain why the two loops produce different results at the V8 Execution Context level."
        ),
        challenge_2_title="Algorithm: Function.prototype.memoize",
        challenge_2_prompt=(
            "Implement `memoize(fn, keyResolver?)` — a general-purpose memoization wrapper:\n"
            "- Default key: `JSON.stringify(args)`. Accept optional `keyResolver` for custom cache keys.\n"
            "- Handle async functions: cache the resolved Promise, not the pending one.\n"
            "- Support cache invalidation via returned `memoized.cache.delete(key)` and `memoized.cache.clear()`.\n"
            "- Zero dependencies. O(1) cache hit. Annotate all edge cases inline."
        ),
        challenge_3_title="Industrial Mini-Project: Composable Middleware Pipeline",
        challenge_3_prompt=(
            "Implement a synchronous + async composable middleware engine (koa-style `compose`):\n"
            "- `compose(...middlewares)` returns a single async function `(ctx, next?) => Promise<void>`.\n"
            "- Each middleware receives `(ctx, next)` and must `await next()` to yield to the next layer.\n"
            "- Error in any middleware propagates correctly through the chain.\n"
            "- `ctx` is mutated in-place — demonstrate request/response enrichment pattern.\n"
            "Deliver a complete zero-dependency implementation with inline output annotations."
        ),
    ),
    3: PhaseChallenge(
        phase_number=3,
        challenge_1_title="Output Prediction: Iterator Protocol & Generator Trace",
        challenge_1_prompt=(
            "Predict exact output. Trace the Generator execution state machine step-by-step.\n\n"
            "```javascript\n"
            "function* fibonacci() {\n"
            "  let [a, b] = [0, 1];\n"
            "  while (true) {\n"
            "    yield a;\n"
            "    [a, b] = [b, a + b];\n"
            "  }\n"
            "}\n"
            "const gen = fibonacci();\n"
            "console.log(gen.next());  // ?\n"
            "console.log(gen.next());  // ?\n"
            "console.log(gen.next());  // ?\n"
            "const first8 = [...Array(8)].map(() => gen.next().value);\n"
            "console.log(first8);      // ?\n"
            "```"
        ),
        challenge_2_title="Algorithm: Lazy Infinite Range Combinator",
        challenge_2_prompt=(
            "Implement `range(start, end, step?)` as a lazy Generator producing values on demand:\n"
            "- Support infinite ranges when `end` is `Infinity`.\n"
            "- Implement chainable lazy operators: `.map(fn)`, `.filter(pred)`, `.take(n)`, `.toArray()`.\n"
            "- Each operator must return a new lazy iterator (no intermediate array materialization).\n"
            "- Zero dependencies. Demonstrate `range(1, Infinity).filter(n => n % 2).take(5).toArray()`."
        ),
        challenge_3_title="Industrial Mini-Project: Observable Event Bus",
        challenge_3_prompt=(
            "Build a zero-dependency pub/sub Observable Event Bus:\n"
            "- `EventBus.create()` factory returning an isolated bus instance.\n"
            "- `bus.on(event, handler)` — subscribe; returns unsubscribe function.\n"
            "- `bus.once(event, handler)` — auto-unsubscribes after first emission.\n"
            "- `bus.emit(event, ...args)` — synchronous fan-out to all subscribers.\n"
            "- `bus.pipe(event, targetBus, targetEvent?)` — cross-bus event forwarding.\n"
            "Deliver complete implementation with inline annotations demonstrating all edge cases."
        ),
    ),
    4: PhaseChallenge(
        phase_number=4,
        challenge_1_title="Output Prediction: Prototype Chain Walk",
        challenge_1_prompt=(
            "Trace the exact prototype chain and predict all output:\n\n"
            "```javascript\n"
            "class Animal {\n"
            "  #name;\n"
            "  constructor(name) { this.#name = name; }\n"
            "  speak() { return `${this.#name} makes a sound.`; }\n"
            "  static create(name) { return new this(name); }\n"
            "}\n"
            "class Dog extends Animal {\n"
            "  speak() { return super.speak().replace('sound', 'bark'); }\n"
            "}\n"
            "const d = Dog.create('Rex');\n"
            "console.log(d.speak());                                  // ?\n"
            "console.log(d instanceof Dog);                           // ?\n"
            "console.log(d instanceof Animal);                        // ?\n"
            "console.log(Object.getPrototypeOf(Dog) === Animal);      // ?\n"
            "console.log(Object.getPrototypeOf(Dog.prototype) === Animal.prototype); // ?\n"
            "```"
        ),
        challenge_2_title="Algorithm: Object.create-based Deep Mixin System",
        challenge_2_prompt=(
            "Implement a `mixin(...mixins)` factory using `Object.create` (no class syntax):\n"
            "- Compose multiple mixin objects into a single prototype chain.\n"
            "- Preserve all property descriptors (enumerable, configurable, writable) from all sources.\n"
            "- Detect and throw on conflicting method names across mixins.\n"
            "- Support method calling `super` implicitly through the composed prototype chain.\n"
            "Zero dependencies. Annotate all edge cases inline."
        ),
        challenge_3_title="Industrial Mini-Project: Reactive State Container",
        challenge_3_prompt=(
            "Build a zero-dependency reactive state container (Redux-inspired, zero external deps):\n"
            "- `createStore(reducer, initialState)` — factory.\n"
            "- `store.dispatch(action)` — pass action through reducer, update state.\n"
            "- `store.getState()` — returns immutable deep-frozen current state.\n"
            "- `store.subscribe(listener)` — synchronous notification on every state change; returns unsubscribe.\n"
            "- `store.applyMiddleware(...middlewares)` — compose enhancers around dispatch.\n"
            "Deliver complete implementation with inline output annotations."
        ),
    ),
    5: PhaseChallenge(
        phase_number=5,
        challenge_1_title="Output Prediction: Microtask vs Macrotask Ordering",
        challenge_1_prompt=(
            "Predict the exact order of console output. Label each line with its queue:\n\n"
            "```javascript\n"
            "console.log('A');                         // sync\n"
            "setTimeout(() => console.log('B'), 0);    // macrotask\n"
            "Promise.resolve()\n"
            "  .then(() => console.log('C'))           // microtask\n"
            "  .then(() => console.log('D'));           // microtask\n"
            "queueMicrotask(() => console.log('E'));   // microtask\n"
            "console.log('F');                         // sync\n"
            "```\n\n"
            "Prove your answer by tracing the Event Loop Tick Invariant step-by-step."
        ),
        challenge_2_title="Algorithm: Promise.withResolvers-based Task Queue",
        challenge_2_prompt=(
            "Implement `AsyncTaskQueue(concurrency)` — a concurrent async task scheduler:\n"
            "- `queue.add(asyncFn)` — enqueue task; returns a Promise resolving to its result.\n"
            "- At most `concurrency` tasks run simultaneously at any time.\n"
            "- When a slot frees, the next enqueued task starts automatically.\n"
            "- Use `Promise.withResolvers()` (ES2024+) for deferred resolution. Zero deps.\n"
            "Annotate the internal state machine transitions with inline comments."
        ),
        challenge_3_title="Industrial Mini-Project: AbortController-Aware HTTP Client",
        challenge_3_prompt=(
            "Build a production-grade zero-dependency HTTP client wrapper around `fetch`:\n"
            "- `httpClient.get(url, options?)`, `.post(url, body, options?)` — typed response.\n"
            "- Automatic retry with exponential backoff (3 attempts, jitter).\n"
            "- Per-request timeout using `AbortController` + `AbortSignal.timeout(ms)`.\n"
            "- Request deduplication: identical in-flight GET requests share a single Promise.\n"
            "- Response caching with configurable TTL using `Map` + timestamp eviction.\n"
            "Deliver complete implementation with inline output annotations."
        ),
    ),
    6: PhaseChallenge(
        phase_number=6,
        challenge_1_title="Output Prediction: Event Propagation Trace",
        challenge_1_prompt=(
            "Given the following HTML and JS, trace every event handler invocation order:\n\n"
            "```html\n"
            "<div id='outer'><div id='middle'><button id='btn'>Click</button></div></div>\n"
            "```\n"
            "```javascript\n"
            "const outer = document.getElementById('outer');\n"
            "const middle = document.getElementById('middle');\n"
            "const btn = document.getElementById('btn');\n"
            "outer.addEventListener('click', () => console.log('outer bubble'), false);\n"
            "outer.addEventListener('click', () => console.log('outer capture'), true);\n"
            "middle.addEventListener('click', e => { console.log('middle'); e.stopPropagation(); });\n"
            "btn.addEventListener('click', () => console.log('btn'));\n"
            "btn.click();\n"
            "```\n\nPredict exact output and explain stopPropagation effect."
        ),
        challenge_2_title="Algorithm: Efficient Event Delegation Handler",
        challenge_2_prompt=(
            "Implement `delegate(root, selector, event, handler)` — a zero-dependency event delegation utility:\n"
            "- Attach a single listener to `root` instead of N listeners to N children.\n"
            "- Walk `event.composedPath()` to find the closest matching `selector` ancestor.\n"
            "- Pass the matching element as `this` and expose `event.delegateTarget` on the event.\n"
            "- Support dynamic DOM — elements added after `delegate()` call must still match.\n"
            "Zero deps. O(depth) per event — not O(n-children). Annotate all edge cases."
        ),
        challenge_3_title="Industrial Mini-Project: Intersection Observer Lazy Image Loader",
        challenge_3_prompt=(
            "Build a production-grade lazy image loading system using `IntersectionObserver`:\n"
            "- `LazyLoader.init(selector, options?)` — observe all matched images on the page.\n"
            "- Load image `src` from `data-src` attribute when element enters the viewport.\n"
            "- Apply progressive placeholder blur → sharp transition using CSS class swap.\n"
            "- Support `rootMargin` threshold customization and `disconnect()` for cleanup.\n"
            "- Handle dynamically added images via `MutationObserver` integration.\n"
            "Zero npm dependencies. Deliver complete implementation with inline annotations."
        ),
    ),
    7: PhaseChallenge(
        phase_number=7,
        challenge_1_title="Output Prediction: Proxy Trap Trace",
        challenge_1_prompt=(
            "Predict exact output. Trace every Proxy trap invocation:\n\n"
            "```javascript\n"
            "const target = { x: 1, y: 2 };\n"
            "const handler = {\n"
            "  get: (t, k) => { console.log(`get ${k}`); return Reflect.get(t, k); },\n"
            "  set: (t, k, v) => { console.log(`set ${k}=${v}`); return Reflect.set(t, k, v); },\n"
            "  has: (t, k) => { console.log(`has ${k}`); return Reflect.has(t, k); },\n"
            "};\n"
            "const p = new Proxy(target, handler);\n"
            "console.log(p.x);          // ?\n"
            "p.z = 99;                  // ?\n"
            "console.log('z' in p);     // ?\n"
            "console.log({ ...p });     // ?\n"
            "```"
        ),
        challenge_2_title="Algorithm: Revocable Sandboxed Execution Environment",
        challenge_2_prompt=(
            "Implement `sandbox(code, allowedGlobals)` using `Proxy` + `new Function`:\n"
            "- Execute `code` string in a sandboxed scope with only `allowedGlobals` exposed.\n"
            "- Intercept and block access to `globalThis`, `window`, `process` via Proxy `get` trap.\n"
            "- Return `{ result, revoke }` — calling `revoke()` makes the sandbox inert.\n"
            "- Throw `SecurityError` on any blocked global access attempt.\n"
            "Zero deps. Document the security limitations honestly in inline comments."
        ),
        challenge_3_title="Industrial Mini-Project: Schema Validation Engine",
        challenge_3_prompt=(
            "Build a zero-dependency JSON Schema-inspired runtime validation engine:\n"
            "- `Schema.define(descriptor)` — compile descriptor to a validator.\n"
            "- Supported types: string, number, boolean, array, object, null, union.\n"
            "- Constraints: minLength, maxLength, min, max, pattern, required, additionalProperties.\n"
            "- `schema.validate(data)` — returns `{ valid: boolean, errors: ValidationError[] }`.\n"
            "- `schema.parse(data)` — throws `ValidationError` with full path on first failure.\n"
            "Use `Proxy` to intercept schema descriptor access for developer ergonomics."
        ),
    ),
    8: PhaseChallenge(
        phase_number=8,
        challenge_1_title="Output Prediction: Node.js Event Loop Phase Ordering",
        challenge_1_prompt=(
            "Predict the exact output order. Label each with its libuv phase:\n\n"
            "```javascript\n"
            "const { readFile } = require('fs');\n"
            "setImmediate(() => console.log('setImmediate'));       // check phase\n"
            "process.nextTick(() => console.log('nextTick'));       // nextTick queue\n"
            "Promise.resolve().then(() => console.log('promise')); // microtask\n"
            "setTimeout(() => console.log('setTimeout 0'), 0);     // timers phase\n"
            "readFile(__filename, () => {\n"
            "  setImmediate(() => console.log('inner setImmediate'));\n"
            "  setTimeout(() => console.log('inner setTimeout'), 0);\n"
            "  process.nextTick(() => console.log('inner nextTick'));\n"
            "  console.log('readFile callback');\n"
            "});\n"
            "console.log('sync');\n"
            "```"
        ),
        challenge_2_title="Algorithm: Async Stream Processor with Backpressure",
        challenge_2_prompt=(
            "Implement a Node.js Transform stream `JsonLineStream` in ES2024+:\n"
            "- Reads raw newline-delimited JSON (NDJSON) from a Readable source.\n"
            "- Parses each line as JSON, validates against a provided schema function.\n"
            "- Applies a user-provided `transform(record)` async mapping function.\n"
            "- Applies backpressure automatically using the Node.js Streams API `highWaterMark`.\n"
            "- Emits `'invalid'` events for malformed lines without crashing the stream.\n"
            "Zero dependencies beyond Node.js built-ins. Inline all buffer management logic."
        ),
        challenge_3_title="Industrial Mini-Project: Production HTTP Rate Limiter",
        challenge_3_prompt=(
            "Build a zero-dependency production-grade sliding window rate limiter for Node.js HTTP:\n"
            "- `RateLimiter.create({ windowMs, maxRequests, keyFn })` factory.\n"
            "- `limiter.middleware()` returns a Node.js `(req, res, next)` compatible middleware.\n"
            "- Algorithm: Sliding Window Log — store per-key timestamps, evict expired entries.\n"
            "- Set `Retry-After`, `X-RateLimit-Limit`, `X-RateLimit-Remaining` headers correctly.\n"
            "- Return `429 Too Many Requests` with RFC 7807 Problem+JSON body on limit breach.\n"
            "Deliver complete implementation with inline output annotations."
        ),
    ),
    9: PhaseChallenge(
        phase_number=9,
        challenge_1_title="Output Prediction: Trie Router Match Trace",
        challenge_1_prompt=(
            "Given the following router configuration, predict the exact match result for each request:\n\n"
            "```javascript\n"
            "const router = createRouter();\n"
            "router.add('GET', '/api/users/:id', 'getUser');\n"
            "router.add('GET', '/api/users/:id/posts', 'getUserPosts');\n"
            "router.add('POST', '/api/users', 'createUser');\n"
            "router.add('GET', '/api/*', 'apiWildcard');\n"
            "\n"
            "console.log(router.match('GET', '/api/users/42'));          // ?\n"
            "console.log(router.match('GET', '/api/users/42/posts'));     // ?\n"
            "console.log(router.match('POST', '/api/users'));             // ?\n"
            "console.log(router.match('GET', '/api/unknown/path'));       // ?\n"
            "console.log(router.match('DELETE', '/api/users/1'));         // ?\n"
            "```"
        ),
        challenge_2_title="Algorithm: Trie-Based HTTP Router with Named Parameters",
        challenge_2_prompt=(
            "Implement `createRouter()` — a zero-dependency, production-grade HTTP router:\n"
            "- Internal data structure: Radix Trie for O(depth) route matching.\n"
            "- Support named parameters (`:id`), optional parameters (`:id?`), wildcards (`*`).\n"
            "- `router.add(method, pattern, handler)` — register route.\n"
            "- `router.match(method, path)` — returns `{ handler, params }` or `null`.\n"
            "- O(k) match time where k = path segment count. Zero dependencies."
        ),
        challenge_3_title="Industrial Mini-Project: Complete Zero-Dependency CLI Engine",
        challenge_3_prompt=(
            "Build a production-grade zero-dependency CLI framework for Node.js:\n"
            "- `cli.command(name, description, options)` — register a subcommand with typed flags.\n"
            "- `cli.parse(argv)` — parse `process.argv` and dispatch to the correct command handler.\n"
            "- Automatic `--help` generation with aligned column formatting.\n"
            "- Typed flag parsing: boolean, string, number, array (repeated flags).\n"
            "- Validation: required flags, enum constraints, custom validators.\n"
            "- Exit code management: 0 on success, 1 on validation error, 2 on runtime error.\n"
            "Deliver a complete implementation with a working demonstration subcommand."
        ),
    ),
}



_GIT_PHASE_CHALLENGES: Dict[int, PhaseChallenge] = {
    1: PhaseChallenge(
        phase_number=1,
        challenge_1_title="Output Prediction: DVCS vs CVCS Offline Commit Trace",
        challenge_1_prompt=(
            "Trace the offline execution behavior of Git versus a Centralized VCS (SVN).\n\n"
            "```bash\n"
            "# Offline workstation: network disconnected\n"
            "$ git checkout -b feature/offline-engine\n"
            "$ echo 'export const cache = new Map();' > cache.js\n"
            "$ git add cache.js\n"
            "$ git commit -m 'feat: implement in-memory cache'\n"
            "$ git log -1 --stat\n"
            "```\n\n"
            "Predict the exact output and explain why Git executes this command in under 5ms with 0 network calls."
        ),
        challenge_2_title="Algorithm: Content-Addressable Blob Storage in Python",
        challenge_2_prompt=(
            "Implement `store_blob(data: bytes, repo_root: Path) -> str` adhering to Git's object format:\n"
            "- Prepend header: `blob <size>\\0<data>`.\n"
            "- Compute SHA-1 hexadecimal hash (40 characters).\n"
            "- Compress object payload using `zlib.compress()`.\n"
            "- Store compressed bytes at `.git/objects/<hash[:2]>/<hash[2:]>`.\n"
            "- Return the 40-character SHA-1 hash. Native Python standard library only with zero external dependencies."
        ),
        challenge_3_title="Industrial Mini-Project: Git Repository Scaffolder",
        challenge_3_prompt=(
            "Build a zero-dependency script `init_repo(path: Path) -> None` that creates a valid Git repository:\n"
            "- Creates `.git/` with subdirectories: `objects/`, `refs/heads/`, `refs/tags/`, `hooks/`.\n"
            "- Writes `.git/HEAD` referencing `ref: refs/heads/main\\n`.\n"
            "- Writes `.git/config` with valid core section (`bare = false`, `filemode = true`).\n"
            "- Writes `.git/description` default message.\n"
            "Verify that running native `git status` inside the initialized folder returns exit code 0."
        ),
    ),
    2: PhaseChallenge(
        phase_number=2,
        challenge_1_title="Output Prediction: Git Config Scope Precedence Trace",
        challenge_1_prompt=(
            "Predict the final value printed by `git config user.email` given conflicting scopes:\n\n"
            "```bash\n"
            "$ git config --system user.email 'system@enterprise.corp'\n"
            "$ git config --global user.email 'global@personal.io'\n"
            "$ git config --local user.email 'local@project.org'\n"
            "$ git config user.email                             # ?\n"
            "$ git config --unset user.email\n"
            "$ git config user.email                             # ?\n"
            "```\n\n"
            "Trace the priority hierarchy: System -> Global -> Local."
        ),
        challenge_2_title="Algorithm: Zero-Dependency Git INI Config Parser",
        challenge_2_prompt=(
            "Implement `parse_git_config(config_text: str) -> dict` with constraints:\n"
            "- Parse standard sections `[core]` and subsections `[remote \"origin\"]`.\n"
            "- Strip leading/trailing whitespace and comments (`#` and `;`).\n"
            "- Parse boolean flags (true, false, yes, no, 1, 0) and nested key-value pairs.\n"
            "- Time complexity: O(N) where N is text length. Zero external imports."
        ),
        challenge_3_title="Industrial Mini-Project: Multi-Profile Git Identity Switcher",
        challenge_3_prompt=(
            "Create a zero-dependency CLI utility `git-profile-switch` that:\n"
            "- Inspects `git remote get-url origin`.\n"
            "- Matches enterprise domains (e.g. `github.com/company/`) versus personal accounts.\n"
            "- Automatically sets `user.name`, `user.email`, and `core.sshCommand` with dedicated SSH keys.\n"
            "- Emits clear confirmation output with inline verification annotations."
        ),
    ),
    3: PhaseChallenge(
        phase_number=3,
        challenge_1_title="Output Prediction: The Three Trees State Machine Trace",
        challenge_1_prompt=(
            "Trace the exact state of files across Working Tree, Index (Staging), and HEAD:\n\n"
            "```bash\n"
            "$ echo 'v1' > app.py && git add app.py && git commit -m 'c1'\n"
            "$ echo 'v2' > app.py\n"
            "$ git status --short                                # ?\n"
            "$ git add app.py\n"
            "$ echo 'v3' > app.py\n"
            "$ git status --short                                # ?\n"
            "$ git diff                                          # ?\n"
            "$ git diff --staged                                 # ?\n"
            "```\n\n"
            "Explain how the same file simultaneously holds distinct staged and unstaged content."
        ),
        challenge_2_title="Algorithm: Git Tree Object Serializer",
        challenge_2_prompt=(
            "Implement `create_tree_object(entries: list[tuple[str, str, str]]) -> tuple[str, bytes]`:\n"
            "- Each entry: `(mode, name, sha1_hex)` (e.g., `('100644', 'main.py', '4b825dc6...')`).\n"
            "- Sort entries using Git's strict byte-ordering rules (directories sorted as if ending with '/').\n"
            "- Encode entries in binary format: `<mode> <name>\\0<20-byte-binary-sha1>`.\n"
            "- Prepend header `tree <size>\\0` and compute SHA-1 hash. Native standard library only."
        ),
        challenge_3_title="Industrial Mini-Project: Pure Python Git Staging Simulator",
        challenge_3_prompt=(
            "Build an in-memory staging area simulator class `GitIndexManager`:\n"
            "- `stage_file(path, content)` — creates blob object, updates index entries map.\n"
            "- `unstage_file(path)` — restores index entry to match current HEAD commit.\n"
            "- `commit(author, message)` — builds tree object, writes commit object, updates HEAD ref.\n"
            "- Include inline output assertions verifying commit SHA-1 generation on sample workloads."
        ),
    ),
    4: PhaseChallenge(
        phase_number=4,
        challenge_1_title="Output Prediction: .gitignore Negation & Directory Pruning",
        challenge_1_prompt=(
            "Given the following `.gitignore` rules, predict which files are tracked versus ignored:\n\n"
            "```text\n"
            "logs/\n"
            "!logs/important.log\n"
            "temp/*\n"
            "!temp/keep.txt\n"
            "dist/**/build.js\n"
            "```\n\n"
            "Evaluate tracking status for:\n"
            "1. `logs/debug.log`\n"
            "2. `logs/important.log` (Gotcha alert: check parent directory pruning!)\n"
            "3. `temp/keep.txt`\n"
            "4. `dist/release/v1/build.js`\n"
            "Explain why Git cannot re-include a file if its parent directory is excluded."
        ),
        challenge_2_title="Algorithm: Git Pathspec Pattern Matcher",
        challenge_2_prompt=(
            "Implement `matches_gitignore(path: str, rule: str) -> bool` supporting:\n"
            "- Leading slash anchoring: `/docs/` matches root only, `docs/` matches anywhere.\n"
            "- Wildcards: `*` (any chars except `/`), `**` (recursive multi-directory match).\n"
            "- Question mark: `?` (single char).\n"
            "- Trailing slash: `dir/` (matches directories only).\n"
            "- Implement in O(N*M) with zero third-party libraries."
        ),
        challenge_3_title="Industrial Mini-Project: Pre-Commit Secret Scanner Hook",
        challenge_3_prompt=(
            "Build an automated pre-commit hook script `.git/hooks/pre-commit`:\n"
            "- Inspects all staged files via `git diff --cached --name-only`.\n"
            "- Scans diff hunks for sensitive patterns: AWS keys (`AKIA...`), GitHub tokens (`ghp_...`), private keys.\n"
            "- Blocks commit with exit code 1 if secret matches are detected, printing exact filename and line.\n"
            "- Must be executable, self-contained, and run in under 50ms."
        ),
    ),
    5: PhaseChallenge(
        phase_number=5,
        challenge_1_title="Output Prediction: Commit Range Semantics (Double vs Triple Dot)",
        challenge_1_prompt=(
            "Given branch `feature` branched off `main` at commit C1, where `main` has commits C1->C2->C3 "
            "and `feature` has C1->C4->C5:\n\n"
            "```bash\n"
            "$ git log main..feature --oneline                 # ?\n"
            "$ git log feature..main --oneline                 # ?\n"
            "$ git log main...feature --oneline                # ?\n"
            "$ git diff main...feature                         # ?\n"
            "```\n\n"
            "Predict exact commit lists and diff boundaries. Explain the merge base reference behavior in `main...feature`."
        ),
        challenge_2_title="Algorithm: Myers Diff Algorithm in Python",
        challenge_2_prompt=(
            "Implement the Myers Diff algorithm `myers_diff(lines_a: list[str], lines_b: list[str]) -> list[str]`:\n"
            "- Find the Shortest Edit Script (SES) using greedy diagonal search on the edit graph.\n"
            "- Generate standard unified diff hunks prefixed with ` `, `+`, and `-`.\n"
            "- Time complexity: O(N * D) where D is edit distance. Zero external dependencies.\n"
            "- Include inline output validation on a 10-line code modification sample."
        ),
        challenge_3_title="Industrial Mini-Project: Interactive Terminal Commit Graph Viewer",
        challenge_3_prompt=(
            "Build a terminal visualizer that parses a local repository's commit DAG:\n"
            "- Reads `.git/refs/heads/` and walks parent commit pointers in `.git/objects/`.\n"
            "- Renders ASCII topology columns `*   commit (HEAD -> main)` and `|\\` branch forks.\n"
            "- Colorizes commit hashes and branch pointers with standard ANSI escape sequences.\n"
            "- Zero npm/pip dependencies. Runs natively in Python."
        ),
    ),
    6: PhaseChallenge(
        phase_number=6,
        challenge_1_title="Output Prediction: Detached HEAD State & Garbage Collection Trace",
        challenge_1_prompt=(
            "Trace the state of HEAD pointer, branch references, and commit reachability:\n\n"
            "```bash\n"
            "$ git checkout main                               # HEAD points to main\n"
            "$ git checkout HEAD~2                             # What is HEAD now?\n"
            "$ echo 'hotfix' > fix.txt && git commit -am 'temp'# Commit C_orph created\n"
            "$ git checkout main                               # Switched back to main\n"
            "$ git log -1 --oneline                            # Is C_orph visible?\n"
            "```\n\n"
            "Explain why C_orph becomes a dangling commit and how `git reflog` rescues it before `git gc`."
        ),
        challenge_2_title="Algorithm: Lowest Common Ancestor (Merge Base) Finder",
        challenge_2_prompt=(
            "Implement `find_merge_base(dag: dict[str, list[str]], commit_a: str, commit_b: str) -> str`:\n"
            "- `dag` maps commit hashes to list of parent commit hashes.\n"
            "- Perform breadth-first search or topological sort from both commit tips.\n"
            "- Return the closest shared ancestor commit hash.\n"
            "- Must handle diamond merges, octopus merges, and fast-forward scenarios."
        ),
        challenge_3_title="Industrial Mini-Project: Automated Stale Branch Cleanup Engine",
        challenge_3_prompt=(
            "Build a production CLI tool `git-prune-stale`:\n"
            "- Queries merged branches against target `main` (`git branch --merged main`).\n"
            "- Excludes protected branches: `main`, `master`, `production`, `staging`.\n"
            "- Prompts for confirmation and executes safe deletion (`git branch -d`).\n"
            "- Emits detailed JSON execution summary with deleted branch names and author timestamps."
        ),
    ),
    7: PhaseChallenge(
        phase_number=7,
        challenge_1_title="Output Prediction: 3-Way Merge Conflict Marker Resolution",
        challenge_1_prompt=(
            "Given BASE, OURS (branch `feat`), and THEIRS (branch `main`):\n\n"
            "BASE:  `const timeout = 3000;`\n"
            "OURS:  `const timeout = 5000; // extended for latency`\n"
            "THEIRS:`const timeout = 2000; // shortened for speed`\n\n"
            "Predict the exact content generated inside the working file when merging `feat` into `main`, "
            "including standard conflict markers `<<<<<<< HEAD`, `=======`, and `>>>>>>> feat`."
        ),
        challenge_2_title="Algorithm: 3-Way Text Merge Engine",
        challenge_2_prompt=(
            "Implement `three_way_merge(base: str, ours: str, theirs: str) -> tuple[bool, str]`:\n"
            "- Returns `(True, merged_content)` if both sides made non-conflicting modifications.\n"
            "- Returns `(False, conflict_content)` if same lines were modified differently.\n"
            "- Injects standard conflict markers with exact branch/commit labels.\n"
            "- Zero dependencies. Native standard library implementation."
        ),
        challenge_3_title="Industrial Mini-Project: Terminal Merge Conflict Resolver TUI",
        challenge_3_prompt=(
            "Build an interactive terminal merge conflict resolver `git-resolve-cli`:\n"
            "- Scans repository for files containing `<<<<<<< HEAD` markers.\n"
            "- Parses individual conflict blocks and presents a terminal selector:\n"
            "  `[1] Keep Current (HEAD)` | `[2] Keep Incoming` | `[3] Keep Both`\n"
            "- Replaces conflict block with user selection, saves file, and stages via `git add`.\n"
            "- Emits clear confirmation output with inline verification annotations."
        ),
    ),
    8: PhaseChallenge(
        phase_number=8,
        challenge_1_title="Output Prediction: Git Stash Stack & Untracked Files Trace",
        challenge_1_prompt=(
            "Trace the working directory and stash list state:\n\n"
            "```bash\n"
            "$ echo 'tracked mod' >> app.js\n"
            "$ echo 'secret config' > .env\n"
            "$ git stash push -m 'WIP 1'                       # Did .env get stashed?\n"
            "$ git status --short                                # What is left in worktree?\n"
            "$ git stash push -u -m 'WIP 2 with untracked'\n"
            "$ git stash list                                   # Predict exact stash index labels\n"
            "$ git stash pop stash@{1}                          # Which stash pops?\n"
            "```\n\n"
            "Explain why `git stash` leaves untracked files in the working directory by default unless `-u` is specified."
        ),
        challenge_2_title="Algorithm: Worktree Stash Stack Engine",
        challenge_2_prompt=(
            "Implement a stash engine `GitStashManager` in Python:\n"
            "- `push(workdir_diff, untracked_files, message)`: pushes snapshot onto LIFO stack.\n"
            "- `pop(index=0)`: pops target snapshot and applies reverse patch onto current working tree.\n"
            "- `apply(index=0)`: applies patch without removing entry from stack.\n"
            "- `list()`: returns formatted array of stash reference descriptors.\n"
            "- O(1) push and O(1) pop operations. Zero external dependencies."
        ),
        challenge_3_title="Industrial Mini-Project: Semantic Release & Annotated Tag Generator",
        challenge_3_prompt=(
            "Build an automated release tool `git-semver-release`:\n"
            "- Walks commit history since latest annotated tag (`git describe --tags --abbrev=0`).\n"
            "- Parses Conventional Commits: `feat:` -> minor bump, `fix:` -> patch bump, `BREAKING CHANGE:` -> major bump.\n"
            "- Automatically creates an annotated tag (`git tag -a vX.Y.Z -m 'Release notes'`).\n"
            "- Generates Markdown release changelog grouped by feature categories."
        ),
    ),
    9: PhaseChallenge(
        phase_number=9,
        challenge_1_title="Output Prediction: Rebase vs Merge Topology & Commit Hash Divergence",
        challenge_1_prompt=(
            "Given `main` with C1->C2, and `feature` with C1->C3->C4:\n\n"
            "Case A: `git checkout feature && git merge main`\n"
            "Case B: `git checkout feature && git rebase main`\n\n"
            "Predict for both cases:\n"
            "1. The number of commits on `feature`.\n"
            "2. Whether original commit hashes C3 and C4 are preserved or regenerated.\n"
            "3. The commit parentage pointers of the feature branch tip.\n"
            "Explain why rebasing pushed public branches causes upstream collision disasters."
        ),
        challenge_2_title="Algorithm: Interactive Rebase Plan Engine",
        challenge_2_prompt=(
            "Implement `rebase_executor(commits: list[dict], plan: list[tuple[str, str]]) -> list[dict]`:\n"
            "- Supported commands: `pick`, `squash`, `fixup`, `reword`, `drop`.\n"
            "- When `squash` is encountered: combine commit diffs and concatenate commit messages.\n"
            "- When `fixup` is encountered: combine diffs but discard child commit message.\n"
            "- Regenerate commit hashes sequentially with updated parent hashes.\n"
            "- Deliver complete implementation in native Python with zero dependencies."
        ),
        challenge_3_title="Industrial Mini-Project: Complete Zero-Dependency Mini-Git CLI (pygit)",
        challenge_3_prompt=(
            "Implement a fully functional zero-dependency mini-Git CLI `pygit.py`:\n"
            "- `pygit init [path]` — initializes repository with `.pygit` objects and refs directory.\n"
            "- `pygit hash-object -w <file>` — computes SHA-1, writes compressed blob object.\n"
            "- `pygit cat-file -p <hash>` — decompresses and displays object payload.\n"
            "- `pygit write-tree` — captures working directory hierarchy as a tree object.\n"
            "- `pygit commit-tree <tree> -p <parent> -m <msg>` — writes commit object with timestamp.\n"
            "- `pygit log` — traverses commit parentage DAG and prints history.\n"
            "Deliver a complete executable script with 0 external packages."
        ),
    ),
}

def get_phase_challenge(phase_number: int, topic: str = "JavaScript") -> PhaseChallenge:
    """Return the pre-authored challenge set for a given phase number."""
    if topic.lower() in ("git", "github", "vcs") and phase_number in _GIT_PHASE_CHALLENGES:
        return _GIT_PHASE_CHALLENGES[phase_number]
    if phase_number not in _PHASE_CHALLENGES:
        raise ValueError(f"No challenge defined for phase {phase_number}")
    return _PHASE_CHALLENGES[phase_number]


# ---------------------------------------------------------------------------
# Chapter Body Generator
# ---------------------------------------------------------------------------

def generate_chapter_body(phase: Dict[str, Any], chapter_title: str, config: SynthesisConfig) -> str:
    """Generate a structured chapter body with Roman Hinglish narrative."""
    lines: List[str] = []
    lines.append(f"### {chapter_title}")
    lines.append("")
    lines.append(f"Topics: (part of Phase {phase['number']}) {phase['topics']}")
    lines.append("")

    topic_slug = chapter_title.split("—")[0].strip() if "—" in chapter_title else chapter_title.split(":")[0].strip()
    is_git = config.topic.lower() in ("git", "github", "vcs", "version control")

    if is_git:
        lines.append(
            f"Sabse pehle ye samajhna zaroori hai ki... {topic_slug} sirf ek terminal command nahi hai — "
            f"ye Git ke internal Content-Addressable Object Database aur Directed Acyclic Graph (DAG) level "
            f"pe snapshots create aur manage karta hai jo project history ki cryptographic integrity maintain karta hai."
        )
        lines.append("")
        lines.append(
            "Technically bolo toh... jab tum commit create karte ho, Git har ek tracked file ka SHA-1 hash compute karta hai, "
            "compressed Blob objects banata hai, unhe Tree hierarchy me assemble karta hai, aur ek immutable commit pointer emit "
            "karta hai. Ye delta compression nahi karta — ye pure snapshots store karta hai."
        )
    else:
        lines.append(
            f"Sabse pehle ye samajhna zaroori hai ki... {topic_slug} sirf ek syntactic feature nahi hai — "
            f"ye JavaScript engine ke andar kuch fundamental karta hai jo tumhare code ke runtime behaviour "
            f"ko directly impact karta hai."
        )
        lines.append("")
        lines.append(
            "Technically bolo toh... jab V8 tumhara code parse karta hai, ye ek Abstract Syntax Tree (AST) "
            "banata hai, phir Ignition Bytecode generate karta hai, aur phir TurboFan JIT compile karta hai "
            "hot functions ko native machine code me. Har ek step pe kuch invariants hold karne chahiye."
        )
    lines.append("")

    # Mental Model callout
    lines.append("[MENTAL MODEL]")
    if is_git:
        lines.append(
            "Think of Git not as a file change tracker, but as a Content-Addressable Key-Value Object Store "
            "(under .git/objects) layered with an immutable Directed Acyclic Graph (DAG). The 3 Trees operate as: "
            "(1) Working Directory (unpacked files on disk), (2) Staging Area / Index (prepared next tree snapshot), "
            "and (3) HEAD commit (active branch pointer in the immutable DAG)."
        )
    else:
        lines.append(
            f"Think of the JavaScript engine as a two-phase processor: (1) Parse & Compile — "
            f"where declarations are hoisted, scope chains are established, and Lexical Environment "
            f"Records are wired into the prototype of each function scope; (2) Execution — where the "
            f"Call Stack grows and shrinks as function frames are pushed and popped in LIFO order."
        )
    lines.append("")

    # Engineering Gotcha
    lines.append("[ENGINEERING GOTCHA]")
    if is_git:
        lines.append(
            "Production code me unexpected bugs aate hain agar tum assume karo ki .gitignore me file add karne se "
            "wo automatically untrack ho jayegi. Gotcha ye hai ki agar file already index me staged ya committed hai, "
            "toh .gitignore use ignore nahi karega. Pehle 'git rm --cached <file>' run karna zaroori hai."
        )
    else:
        lines.append(
            "Production code me unexpected bugs aate hain agar tum assume karo ki JavaScript "
            "synchronous context me koi external resource access immediate hai. Always treat I/O "
            "as asynchronous — even `fs.readFileSync` blocks the Event Loop entirely."
        )
    lines.append("")

    # Interview Tip
    if config.audience_focus == "faang_interview":
        lines.append("[INTERVIEW TIP]")
        if is_git:
            lines.append(
                "In a FAANG system design interview, when asked about Git internals, "
                "immediately anchor on the DAG Invariant and 3-Trees Model: 'Git represents project history as an "
                "immutable Directed Acyclic Graph (DAG) of commit objects pointing to tree hierarchies and content-addressed blobs. "
                "Branches are merely 41-byte ref pointers, and merges compute the Lowest Common Ancestor.' This single sentence "
                "separates senior engineers from surface-level command users."
            )
        else:
            lines.append(
                "In a FAANG system design interview, when asked about JavaScript concurrency, "
                "immediately anchor on the Event Loop Tick Invariant: 'The Call Stack must be empty "
                "before any Microtask or Macrotask dequeues.' This single sentence demonstrates "
                "engine-level understanding and separates candidates who know the spec from those who "
                "only know the syntax."
            )
        lines.append("")

    assert_zero_devanagari("\n".join(lines), context=f"chapter '{chapter_title}'")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Phase Renderer
# ---------------------------------------------------------------------------

def render_phase(phase_meta: Dict[str, Any], config: SynthesisConfig) -> SynthesizedPhase:
    """Render a complete phase including all chapters and end-of-phase challenges."""
    chapters: List[SynthesizedChapter] = []
    for ch_idx, ch_title in enumerate(phase_meta.get("chapters", []), start=1):
        body = generate_chapter_body(phase_meta, ch_title, config)
        chapters.append(SynthesizedChapter(
            phase_number=phase_meta["number"],
            chapter_index=ch_idx,
            title=ch_title,
            body_markdown=body,
        ))

    challenge = get_phase_challenge(phase_meta["number"], topic=config.topic)
    return SynthesizedPhase(
        number=phase_meta["number"],
        title=phase_meta["title"],
        topics=phase_meta["topics"],
        chapters=chapters,
        challenge=challenge,
    )


# ---------------------------------------------------------------------------
# Manual Serializer
# ---------------------------------------------------------------------------

def render_challenge_block(challenge: PhaseChallenge) -> str:
    """Format the 3-part challenge block for a phase."""
    sep = "=" * 60
    lines = [
        sep,
        f"PHASE {challenge.phase_number} — END-OF-PHASE CHALLENGES",
        sep,
        "",
        f"Challenge 1: {challenge.challenge_1_title}",
        "-" * 40,
        challenge.challenge_1_prompt,
        "",
        f"Challenge 2: {challenge.challenge_2_title}",
        "-" * 40,
        challenge.challenge_2_prompt,
        "",
        f"Challenge 3: {challenge.challenge_3_title}",
        "-" * 40,
        challenge.challenge_3_prompt,
        "",
    ]
    return "\n".join(lines)


def serialize_manual_to_markdown(manual: SynthesizedManual) -> str:
    """Serialize the complete synthesized manual to a single Markdown string."""
    parts: List[str] = []

    # Cover header
    parts.append(f"# {manual.topic}: The Complete Reference Manual")
    parts.append("## Architecture & Core Internals — Monochrome High-Density Engineering Edition")
    parts.append("")
    parts.append(f"Generated: {manual.generated_at}")
    parts.append("Prepared by @issparsh @sumitsingh097")
    parts.append("")
    parts.append("=" * 80)
    parts.append("")

    # Syllabus index
    parts.append(manual.syllabus_index)
    parts.append("")

    # Phases
    for phase in manual.phases:
        parts.append("=" * 80)
        parts.append(f"PHASE {phase.number}: {phase.title.upper()}")
        parts.append(f"Topics: {phase.topics}")
        parts.append("=" * 80)
        parts.append("")

        for ch in phase.chapters:
            parts.append(ch.body_markdown)
            parts.append("")

        parts.append(render_challenge_block(phase.challenge))
        parts.append("")

    # Appendices
    if manual.appendix_index:
        parts.append("=" * 80)
        parts.append("APPENDICES")
        parts.append("=" * 80)
        parts.append(manual.appendix_index)
        parts.append("")

    result = "\n".join(parts)
    assert_zero_devanagari(result, context="full_manual_output")
    return result


# ---------------------------------------------------------------------------
# Top-Level Synthesizer Entry Point
# ---------------------------------------------------------------------------

def synthesize_manual(config: SynthesisConfig) -> SynthesizedManual:
    """Synthesize a complete reference manual from a SynthesisConfig."""
    is_git = config.topic.lower() in ("git", "github", "vcs", "version control")
    catalog = GIT_PHASE_CATALOG if is_git else PHASE_CATALOG
    appendices_list = GIT_APPENDICES if is_git else APPENDICES

    phases_meta = [p for p in catalog if p["number"] in config.phases_to_include]
    syllabus = generate_syllabus_index(phases_meta, appendices_list if config.include_appendices else [], topic_name=config.topic)

    appendix_index = ""
    if config.include_appendices:
        app_lines = []
        for app in appendices_list:
            app_lines.append(f"## {app['title']}")
            app_lines.append(f"Scope: {app['scope']}")
            app_lines.append("")
        appendix_index = "\n".join(app_lines)

    rendered_phases = [render_phase(pm, config) for pm in phases_meta]

    manual = SynthesizedManual(
        topic=config.topic,
        generated_at=datetime.now(timezone.utc).isoformat(),
        syllabus_index=syllabus,
        phases=rendered_phases,
        appendix_index=appendix_index,
        config=config,
    )
    return manual


def synthesize_and_write(config: SynthesisConfig) -> Path:
    """Synthesize manual and write Markdown output to disk. Returns path to output file."""
    manual = synthesize_manual(config)
    md_content = serialize_manual_to_markdown(manual)

    out_dir = Path(config.output_dir) if config.output_dir else Path.cwd() / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"thenuke_manual_{ts}.md"
    out_path.write_text(md_content, encoding="utf-8")
    logger.info("Manual written to %s (%d bytes)", out_path, len(md_content))
    return out_path
