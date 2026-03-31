"""
Tests for the RAG pipeline.
These tests call the Anthropic API — network required.
"""

import pytest


def test_answer_returns_dict():
    """answer_question() must return a dict with 'answer' and 'sources' keys."""
    from rag.query import answer_question
    result = answer_question("What are the available pricing tiers?")

    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert "answer"  in result, "Missing 'answer' key"
    assert "sources" in result, "Missing 'sources' key"
    assert isinstance(result["answer"],  str)  and len(result["answer"])  > 0
    assert isinstance(result["sources"], list) and len(result["sources"]) > 0


def test_out_of_scope_question():
    """Out-of-scope questions must not hallucinate — response must signal no knowledge."""
    from rag.query import answer_question
    result = answer_question("What is the population of Brazil?")
    answer_lower = result["answer"].lower()

    refusal_phrases = ["don't have", "do not have", "not in", "i don't know", "no information"]
    assert any(phrase in answer_lower for phrase in refusal_phrases), (
        f"Expected a refusal response for out-of-scope question, got: {result['answer']}"
    )
