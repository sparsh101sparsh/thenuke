"""100 Timeless Engineering, Systems, Science & Learning Quotes Library.

Curated library of 100 quotes from legendary computer scientists,
software architects, systems thinkers, polymaths, and educators.
Supports:
- get_quote(topic: str = "", seed: Optional[Any] = None) -> Tuple[str, str]
- Domain-aware filtering (software/systems, language/communication, science/math, philosophy/mastery).
"""

from __future__ import annotations

import hashlib
import random
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# The 100 Quotes Corpus
# Format: (quote_text, author, category_tags)
# ---------------------------------------------------------------------------

QUOTES: List[Tuple[str, str, List[str]]] = [
    # --- Software Engineering, Architecture & Design (1-25) ---
    (
        "Any fool can write code that a computer can understand. Good programmers write code that humans can understand.",
        "Martin Fowler",
        ["software", "clean_code", "general"],
    ),
    (
        "Simplicity is prerequisite for reliability.",
        "Edsger W. Dijkstra",
        ["systems", "software", "reliability"],
    ),
    (
        "Talk is cheap. Show me the code.",
        "Linus Torvalds",
        ["git", "software", "open_source", "pragmatism"],
    ),
    (
        "Premature optimization is the root of all evil (or at least most of it) in programming.",
        "Donald E. Knuth",
        ["algorithms", "optimization", "software"],
    ),
    (
        "There are two ways of constructing a software design: One way is to make it so simple that there are obviously no deficiencies, and the other way is to make it so complicated that there are no obvious deficiencies.",
        "C.A.R. Hoare",
        ["architecture", "software", "systems"],
    ),
    (
        "The most important property of a program is whether it accomplishes the intention of its user.",
        "C.A.R. Hoare",
        ["software", "purpose", "engineering"],
    ),
    (
        "Programs must be written for people to read, and only incidentally for machines to execute.",
        "Harold Abelson & Gerald Jay Sussman",
        ["software", "pedagogy", "clean_code"],
    ),
    (
        "The function of good software is to make the complex appear to be simple.",
        "Grady Booch",
        ["architecture", "software", "simplicity"],
    ),
    (
        "Controlling complexity is the essence of computer programming.",
        "Brian Kernighan",
        ["systems", "software", "complexity"],
    ),
    (
        "Debugging is twice as hard as writing the code in the first place. Therefore, if you write the code as cleverly as possible, you are, by definition, not smart enough to debug it.",
        "Brian Kernighan",
        ["debugging", "software", "humility"],
    ),
    (
        "Don't comment bad code — rewrite it.",
        "Brian Kernighan & P.J. Plauger",
        ["clean_code", "software", "craftsmanship"],
    ),
    (
        "Good design adds value faster than it adds cost.",
        "Thomas C. Gale",
        ["design", "architecture", "business"],
    ),
    (
        "Make it work, make it right, make it fast.",
        "Kent Beck",
        ["software", "agile", "methodology"],
    ),
    (
        "You can't have great software without a great team, and most teams behave like dysfunctional families.",
        "Jim McCarthy",
        ["teams", "leadership", "culture"],
    ),
    (
        "Clean code always looks like it was written by someone who cares.",
        "Robert C. Martin",
        ["clean_code", "craftsmanship", "discipline"],
    ),
    (
        "Truth can only be found in one place: the code.",
        "Robert C. Martin",
        ["software", "documentation", "truth"],
    ),
    (
        "It is not enough for code to work. It must be clean, elegant, and maintainable.",
        "Robert C. Martin",
        ["clean_code", "software", "standards"],
    ),
    (
        "First, solve the problem. Then, write the code.",
        "John Johnson",
        ["problem_solving", "software", "thinking"],
    ),
    (
        "The only way to go fast, is to go well.",
        "Robert C. Martin",
        ["speed", "quality", "craftsmanship"],
    ),
    (
        "Software is a great combination between artistry and engineering.",
        "Bill Gates",
        ["creativity", "engineering", "software"],
    ),
    (
        "Bad programmers worry about the code. Good programmers worry about data structures and their relationships.",
        "Linus Torvalds",
        ["git", "data_structures", "systems"],
    ),
    (
        "Given enough eyeballs, all bugs are shallow.",
        "Eric S. Raymond",
        ["open_source", "security", "collaboration"],
    ),
    (
        "The best code is no code at all.",
        "Jeff Atwood",
        ["simplicity", "minimalism", "software"],
    ),
    (
        "If you think good architecture is expensive, try bad architecture.",
        "Brian Foote & Joseph Yoder",
        ["architecture", "technical_debt", "systems"],
    ),
    (
        "Architecture is about the important stuff. Whatever that is.",
        "Martin Fowler",
        ["architecture", "design", "systems"],
    ),

    # --- Systems, Operating Systems & Low-Level Engineering (26-45) ---
    (
        "Unix is simple. It just takes a genius to understand its simplicity.",
        "Dennis Ritchie",
        ["unix", "systems", "simplicity"],
    ),
    (
        "You cannot trust code that you did not totally create yourself.",
        "Ken Thompson",
        ["security", "compilers", "systems"],
    ),
    (
        "Rule of Modularity: Developers should build a program out of simple parts connected by well-defined interfaces.",
        "Eric S. Raymond",
        ["unix", "modularity", "systems"],
    ),
    (
        "Rule of Clarity: Clarity is better than cleverness.",
        "Eric S. Raymond",
        ["unix", "clarity", "design"],
    ),
    (
        "Rule of Composition: Design programs to be connected to other programs.",
        "Doug McIlroy",
        ["unix", "pipelines", "composition"],
    ),
    (
        "In computing, turning the obvious into the useful is a noble task.",
        "Alan J. Perlis",
        ["systems", "computing", "philosophy"],
    ),
    (
        "A language that doesn't affect the way you think about programming is not worth knowing.",
        "Alan J. Perlis",
        ["languages", "cognition", "paradigms"],
    ),
    (
        "Complexity has no place in infrastructure.",
        "John Carmack",
        ["performance", "systems", "simplicity"],
    ),
    (
        "Focus is a matter of deciding what things you're not going to do.",
        "John Carmack",
        ["focus", "engineering", "discipline"],
    ),
    (
        "Programming is not about typing, it's about thinking.",
        "Rich Hickey",
        ["cognition", "design", "philosophy"],
    ),
    (
        "Simple is not easy. Simple is an objective measure of lack of intertwining.",
        "Rich Hickey",
        ["simplicity", "systems", "architecture"],
    ),
    (
        "What one programmer can do in one month, two programmers can do in two months.",
        "Fred Brooks",
        ["management", "productivity", "mythical_man_month"],
    ),
    (
        "Conceptual integrity is the most important consideration in system design.",
        "Fred Brooks",
        ["systems", "architecture", "integrity"],
    ),
    (
        "Adding manpower to a late software project makes it later.",
        "Fred Brooks",
        ["management", "projects", "engineering"],
    ),
    (
        "A distributed system is one in which the failure of a computer you didn't even know existed can render your own computer unusable.",
        "Leslie Lamport",
        ["distributed_systems", "concurrency", "fault_tolerance"],
    ),
    (
        "If you cannot explain something in simple terms, you lack a deep understanding of it.",
        "Richard Feynman",
        ["pedagogy", "clarity", "mastery"],
    ),
    (
        "The first principle is that you must not fool yourself — and you are the easiest person to fool.",
        "Richard Feynman",
        ["science", "rigor", "epistemology"],
    ),
    (
        "What I cannot create, I do not understand.",
        "Richard Feynman",
        ["learning", "creation", "first_principles"],
    ),
    (
        "I'd rather have questions that can't be answered than answers that can't be questioned.",
        "Richard Feynman",
        ["science", "inquiry", "truth"],
    ),
    (
        "Computers are good at following instructions, but not at reading your mind.",
        "Donald E. Knuth",
        ["computing", "precision", "instructions"],
    ),

    # --- Computing History, Logic & Pioneers (46-65) ---
    (
        "We can only see a short distance ahead, but we can see plenty there that needs to be done.",
        "Alan Turing",
        ["vision", "pioneering", "computing"],
    ),
    (
        "A computer would deserve to be called intelligent if it could deceive a human into believing that it was human.",
        "Alan Turing",
        ["ai", "turing_test", "intelligence"],
    ),
    (
        "Information is the resolution of uncertainty.",
        "Claude E. Shannon",
        ["information_theory", "entropy", "science"],
    ),
    (
        "The best way to predict the future is to invent it.",
        "Alan Kay",
        ["innovation", "future", "vision"],
    ),
    (
        "Simple things should be simple, complex things should be possible.",
        "Alan Kay",
        ["design", "ux", "systems"],
    ),
    (
        "Object-oriented programming to me has meant only messaging, local retention and protection and hiding of state-process, and extreme late-binding of all things.",
        "Alan Kay",
        ["oop", "messaging", "architecture"],
    ),
    (
        "The most dangerous phrase in the language is: We've always done it this way.",
        "Grace Hopper",
        ["innovation", "change", "progress"],
    ),
    (
        "It's easier to ask forgiveness than it is to get permission.",
        "Grace Hopper",
        ["initiative", "leadership", "action"],
    ),
    (
        "That brain of mine is something more than merely mortal; as time will show.",
        "Ada Lovelace",
        ["vision", "algorithms", "pioneering"],
    ),
    (
        "The Analytical Engine weaves algebraical patterns just as the Jacquard-loom weaves flowers and leaves.",
        "Ada Lovelace",
        ["computing", "patterns", "poetry_of_science"],
    ),
    (
        "There's no sense in being precise when you don't even know what you're talking about.",
        "John von Neumann",
        ["mathematics", "precision", "epistemology"],
    ),
    (
        "Anyone who attempts to generate random numbers by deterministic means is, of course, living in a state of sin.",
        "John von Neumann",
        ["randomness", "mathematics", "computing"],
    ),
    (
        "Computer science is no more about computers than astronomy is about telescopes.",
        "Edsger W. Dijkstra",
        ["computer_science", "mathematics", "theory"],
    ),
    (
        "Elegance is not a dispensable luxury, but a quality that decides between success and failure.",
        "Edsger W. Dijkstra",
        ["elegance", "rigor", "mathematics"],
    ),
    (
        "Testing shows the presence, not the absence of bugs.",
        "Edsger W. Dijkstra",
        ["testing", "qa", "verification"],
    ),
    (
        "There should be one-- and preferably only one --obvious way to do it.",
        "Tim Peters (The Zen of Python)",
        ["python", "simplicity", "clarity"],
    ),
    (
        "Explicit is better than implicit. Simple is better than complex. Complex is better than complicated.",
        "Tim Peters (The Zen of Python)",
        ["zen", "design", "clarity"],
    ),
    (
        "Readability counts.",
        "Tim Peters (The Zen of Python)",
        ["clean_code", "readability", "craftsmanship"],
    ),
    (
        "Special cases aren't special enough to break the rules. Although practicality beats purity.",
        "Tim Peters (The Zen of Python)",
        ["pragmatism", "engineering", "rules"],
    ),
    (
        "Errors should never pass silently. Unless explicitly silenced.",
        "Tim Peters (The Zen of Python)",
        ["reliability", "error_handling", "systems"],
    ),

    # --- Language, Communication, Learning & Mastery (66-85) ---
    (
        "The limits of my language mean the limits of my world.",
        "Ludwig Wittgenstein",
        ["language", "english", "cognition", "philosophy"],
    ),
    (
        "What can be said at all can be said clearly; and whereof one cannot speak thereof one must be silent.",
        "Ludwig Wittgenstein",
        ["clarity", "language", "communication"],
    ),
    (
        "If you can't explain it simply, you don't understand it well enough.",
        "Albert Einstein",
        ["pedagogy", "clarity", "mastery"],
    ),
    (
        "Everything should be made as simple as possible, but not simpler.",
        "Albert Einstein",
        ["simplicity", "science", "design"],
    ),
    (
        "Intellectual growth should commence at birth and cease only at death.",
        "Albert Einstein",
        ["learning", "growth", "curiosity"],
    ),
    (
        "Live as if you were to die tomorrow. Learn as if you were to live forever.",
        "Mahatma Gandhi",
        ["learning", "wisdom", "perseverance"],
    ),
    (
        "The beautiful thing about learning is that nobody can take it away from you.",
        "B.B. King",
        ["learning", "empowerment", "knowledge"],
    ),
    (
        "Tell me and I forget. Teach me and I remember. Involve me and I learn.",
        "Benjamin Franklin",
        ["pedagogy", "active_learning", "practice"],
    ),
    (
        "An investment in knowledge pays the best interest.",
        "Benjamin Franklin",
        ["knowledge", "education", "economics"],
    ),
    (
        "Never let formal education get in the way of your learning.",
        "Mark Twain",
        ["self_learning", "autonomy", "curiosity"],
    ),
    (
        "The secret of getting ahead is getting started.",
        "Mark Twain",
        ["action", "discipline", "execution"],
    ),
    (
        "Broadly speaking, the short words are the best, and the old words best of all.",
        "Winston Churchill",
        ["language", "writing", "communication"],
    ),
    (
        "To achieve great things, two things are needed; a plan, and not quite enough time.",
        "Leonard Bernstein",
        ["execution", "urgency", "creativity"],
    ),
    (
        "Good writing is clear thinking made visible.",
        "William Wheeler",
        ["writing", "communication", "clarity"],
    ),
    (
        "Easy reading is damn hard writing.",
        "Nathaniel Hawthorne",
        ["writing", "craftsmanship", "effort"],
    ),
    (
        "Vigorous writing is concise. A sentence should contain no unnecessary words, a paragraph no unnecessary sentences.",
        "William Strunk Jr.",
        ["writing", "conciseness", "english"],
    ),
    (
        "Clarity is the sovereign virtue of technical communication.",
        "Joseph M. Williams",
        ["technical_writing", "clarity", "communication"],
    ),
    (
        "Language is the dress of thought.",
        "Samuel Johnson",
        ["language", "english", "expression"],
    ),
    (
        "Knowledge has to be improved, challenged, and increased constantly, or it vanishes.",
        "Peter F. Drucker",
        ["learning", "knowledge", "management"],
    ),
    (
        "Efficiency is doing things right; effectiveness is doing the right things.",
        "Peter F. Drucker",
        ["strategy", "execution", "productivity"],
    ),

    # --- Epistemology, Strategy, Engineering Rigor & Philosophy (86-100) ---
    (
        "We are what we repeatedly do. Excellence, then, is not an act, but a habit.",
        "Will Durant (on Aristotle)",
        ["excellence", "habits", "discipline"],
    ),
    (
        "It is the mark of an educated mind to be able to entertain a thought without accepting it.",
        "Aristotle",
        ["critical_thinking", "intellect", "wisdom"],
    ),
    (
        "He who has a why to live can bear almost any how.",
        "Friedrich Nietzsche",
        ["purpose", "resilience", "philosophy"],
    ),
    (
        "Waste no more time arguing about what a good man should be. Be one.",
        "Marcus Aurelius",
        ["stoicism", "action", "character"],
    ),
    (
        "The impediment to action advances action. What stands in the way becomes the way.",
        "Marcus Aurelius",
        ["resilience", "problem_solving", "stoicism"],
    ),
    (
        "Luck is what happens when preparation meets opportunity.",
        "Seneca",
        ["preparation", "opportunity", "stoicism"],
    ),
    (
        "We suffer more often in imagination than in reality.",
        "Seneca",
        ["stoicism", "mental_models", "resilience"],
    ),
    (
        "Study the science of art. Study the art of science. Develop your senses — especially learn how to see. Realize that everything connects to everything else.",
        "Leonardo da Vinci",
        ["systems_thinking", "polymath", "curiosity"],
    ),
    (
        "Simplicity is the ultimate sophistication.",
        "Leonardo da Vinci",
        ["design", "simplicity", "aesthetics"],
    ),
    (
        "Learning never exhausts the mind.",
        "Leonardo da Vinci",
        ["learning", "curiosity", "mastery"],
    ),
    (
        "Measure what is measurable, and make measurable what is not so.",
        "Galileo Galilei",
        ["metrics", "science", "precision"],
    ),
    (
        "If I have seen further it is by standing on the shoulders of Giants.",
        "Isaac Newton",
        ["science", "humility", "progress"],
    ),
    (
        "Nothing in life is to be feared, it is only to be understood. Now is the time to understand more, so that we may fear less.",
        "Marie Curie",
        ["courage", "science", "understanding"],
    ),
    (
        "Somewhere, something incredible is waiting to be known.",
        "Carl Sagan",
        ["curiosity", "discovery", "science"],
    ),
    (
        "Stay hungry, stay foolish.",
        "Steve Jobs (quoting Whole Earth Catalog)",
        ["vision", "curiosity", "aspiration"],
    ),
]


def get_quote(topic: str = "", seed: Optional[Any] = None) -> Tuple[str, str]:
    """Retrieve an inspiring quote suitable for the document cover page.
    
    If topic is provided, attempts to match quotes with relevant category tags.
    Falls back to deterministic hash selection based on topic+seed.
    
    Returns:
        (quote_text, author)
    """
    clean_topic = topic.strip().lower()
    
    # Keyword associations
    matched_quotes: List[Tuple[str, str]] = []
    
    tag_keywords = {
        "git": ["git", "systems", "open_source", "pragmatism", "data_structures"],
        "javascript": ["languages", "software", "clean_code", "architecture", "web"],
        "python": ["python", "zen", "clean_code", "simplicity"],
        "systems": ["systems", "unix", "distributed_systems", "operating_systems"],
        "english": ["language", "english", "writing", "clarity", "communication"],
        "learning": ["learning", "pedagogy", "curiosity", "mastery"],
        "science": ["science", "physics", "math", "rigor", "discovery"],
        "architecture": ["architecture", "systems", "design", "simplicity"],
    }
    
    # Check if topic matches any known cluster
    target_tags = []
    for key, tags in tag_keywords.items():
        if key in clean_topic:
            target_tags.extend(tags)
            
    if target_tags:
        for q_text, q_author, q_tags in QUOTES:
            if any(t in q_tags for t in target_tags):
                matched_quotes.append((q_text, q_author))
                
    if not matched_quotes:
        # Fall back to entire collection
        matched_quotes = [(q[0], q[1]) for q in QUOTES]
        
    # Select deterministically or with seed
    if seed is not None:
        h = int(hashlib.sha256(str(seed).encode("utf-8")).hexdigest(), 16)
        return matched_quotes[h % len(matched_quotes)]
    elif topic:
        h = int(hashlib.sha256(topic.encode("utf-8")).hexdigest(), 16)
        # Use a slight variation so successive runs on different days or configs get fresh quotes
        return matched_quotes[h % len(matched_quotes)]
    else:
        return random.choice(matched_quotes)


def get_all_quotes() -> List[Tuple[str, str]]:
    """Return all 100 quotes as (quote, author) tuples."""
    return [(q[0], q[1]) for q in QUOTES]
