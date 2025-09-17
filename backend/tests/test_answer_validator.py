"""Unit tests for answer validation module."""

import os
from lexa_app.answer_validator import (
    is_enabled,
    count_steps,
    count_citations,
    validate_answer,
    enhance_answer_with_validation,
    detect_completeness_issues,
)


class TestAnswerValidator:

    def setup_method(self):
        """Reset environment for each test."""
        os.environ.pop("LEXA_USE_ANSWER_VALIDATION", None)

    def test_disabled_by_default(self):
        """Answer validation should be disabled by default."""
        assert not is_enabled()
        result = validate_answer("Short answer", [])
        assert result["valid"]  # Should pass when disabled

    def test_enabled_via_env(self):
        """Answer validation should activate via environment flag."""
        os.environ["LEXA_USE_ANSWER_VALIDATION"] = "1"
        assert is_enabled()

    def test_count_numbered_steps(self):
        """Should count numbered steps correctly."""
        text = "1. First step\n2. Second step\n3. Third step"
        assert count_steps(text) == 3

        text_parens = "1) First step\n2) Second step"
        assert count_steps(text_parens) == 2

    def test_count_bullet_steps(self):
        """Should count bullet point steps."""
        text = "- First step\n- Second step\n- Third step"
        assert count_steps(text) == 3

        text_asterisk = "* First\n* Second"
        assert count_steps(text_asterisk) == 2

    def test_count_step_keywords(self):
        """Should count step keywords."""
        text = "First, do this. Next, do that. Finally, complete it."
        assert count_steps(text) >= 3

    def test_count_citations_valid(self):
        """Should count valid citations."""
        sources = [
            {"name": "doc1.pdf (p.1)", "url": "http://example.com/doc1.pdf"},
            {"name": "doc2.pdf (p.2)", "url": "http://example.com/doc2.pdf"},
        ]
        assert count_citations(sources) == 2

    def test_count_citations_invalid(self):
        """Should ignore invalid citations."""
        sources = [
            {"name": "doc1.pdf (p.1)", "url": "http://example.com/doc1.pdf"},
            {"name": "", "url": ""},  # Invalid
            "invalid_format",  # Invalid format
        ]
        assert count_citations(sources) == 1

    def test_detect_truncation(self):
        """Should detect truncated answers."""
        issues = detect_completeness_issues("This is an incomplete answer...")
        assert any("truncated" in issue.lower() for issue in issues)

    def test_detect_incomplete_sentences(self):
        """Should detect incomplete sentences."""
        issues = detect_completeness_issues("This answer has no ending")
        assert any("incomplete" in issue.lower() for issue in issues)

    def test_validate_procedural_answer_sufficient_steps(self):
        """Should pass validation for procedural answers with enough steps."""
        os.environ["LEXA_USE_ANSWER_VALIDATION"] = "1"

        response = "1. First step\n2. Second step\n3. Third step"
        sources = [{"name": "doc.pdf", "url": "http://example.com"}]

        result = validate_answer(response, sources, "how to create sales order")
        assert result["valid"]
        assert result["step_count"] == 3
        assert result["citation_count"] == 1

    def test_validate_procedural_answer_insufficient_steps(self):
        """Should fail validation for procedural answers with too few steps."""
        os.environ["LEXA_USE_ANSWER_VALIDATION"] = "1"

        response = "Just do this one thing."
        sources = [{"name": "doc.pdf", "url": "http://example.com"}]

        result = validate_answer(response, sources, "how to create sales order")
        assert not result["valid"]
        assert result["step_count"] < 3
        assert "at least 3 clear steps" in str(result["suggestions"])

    def test_validate_missing_citations(self):
        """Should fail validation for answers without citations."""
        os.environ["LEXA_USE_ANSWER_VALIDATION"] = "1"

        response = "1. First\n2. Second\n3. Third"
        sources = []

        result = validate_answer(response, sources, "how to convert quote")
        assert not result["valid"]
        assert result["citation_count"] == 0
        assert "source citation" in str(result["suggestions"])

    def test_enhance_answer_with_feedback(self):
        """Should enhance invalid answers with helpful feedback."""
        os.environ["LEXA_USE_ANSWER_VALIDATION"] = "1"

        response = "Short answer."
        sources = []

        enhanced = enhance_answer_with_validation(
            response, sources, "how to create order"
        )
        assert len(enhanced) > len(response)
        assert "*" in enhanced  # Should contain feedback markers

    def test_no_enhancement_for_valid_answers(self):
        """Should not enhance already valid answers."""
        os.environ["LEXA_USE_ANSWER_VALIDATION"] = "1"

        response = "1. First step\n2. Second step\n3. Third step"
        sources = [{"name": "doc.pdf", "url": "http://example.com"}]

        enhanced = enhance_answer_with_validation(
            response, sources, "how to create order"
        )
        assert enhanced == response  # No changes
