"""Tests for the 100 Dynamic Quotes Library."""

import pytest
from scripts.quotes.quote_library import QUOTES, get_quote


def test_quote_library_count():
    assert len(QUOTES) == 100, f"Expected exactly 100 quotes, found {len(QUOTES)}"


def test_quote_tuples_structure():
    for idx, item in enumerate(QUOTES):
        assert len(item) == 3, f"Quote at index {idx} does not have 3 elements: {item}"
        quote_text, author, categories = item
        assert isinstance(quote_text, str) and len(quote_text) > 5
        assert isinstance(author, str) and len(author) > 2
        assert isinstance(categories, list) and len(categories) > 0


def test_deterministic_seed_retrieval():
    q1, a1 = get_quote(topic="Git", seed=42)
    q2, a2 = get_quote(topic="Git", seed=42)
    assert q1 == q2
    assert a1 == a2


def test_domain_filtering():
    q_cs, a_cs = get_quote(topic="Operating Systems", seed=10)
    assert len(q_cs) > 0 and len(a_cs) > 0

    q_lang, a_lang = get_quote(topic="English Literature", seed=10)
    assert len(q_lang) > 0 and len(a_lang) > 0
