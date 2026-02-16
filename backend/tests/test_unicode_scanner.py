"""Tests for the Unicode scanner service."""

from app.services.unicode_scanner import scan, clean


class TestScan:
    def test_clean_text_no_findings(self):
        result = scan("Hello, world! This is plain ASCII text.")
        assert result.has_invisible_chars is False
        assert result.total_invisible_count == 0
        assert result.findings == []
        assert result.context["likely_source"] == "none"

    def test_empty_text(self):
        result = scan("")
        assert result.has_invisible_chars is False
        assert result.total_invisible_count == 0
        assert result.char_count == 0

    def test_detects_zero_width_space(self):
        text = "Hello\u200Bworld"
        result = scan(text)
        assert result.has_invisible_chars is True
        assert result.total_invisible_count == 1
        assert len(result.findings) == 1
        assert result.findings[0].char == "U+200B"
        assert result.findings[0].name == "ZERO WIDTH SPACE"
        assert result.findings[0].category == "zero-width"
        assert result.findings[0].threat_level == "high"
        assert result.findings[0].count == 1
        assert result.findings[0].positions == [5]

    def test_detects_multiple_zero_width_chars(self):
        text = "a\u200Bb\u200Cc\u200D"
        result = scan(text)
        assert result.total_invisible_count == 3
        assert len(result.findings) == 3
        assert result.categories["zero-width"] == 3

    def test_detects_bom(self):
        text = "\uFEFFHello world"
        result = scan(text)
        assert result.has_invisible_chars is True
        assert result.findings[0].char == "U+FEFF"
        assert result.findings[0].threat_level == "high"

    def test_detects_bidi_marks(self):
        text = "Hello\u200Eworld\u200F"
        result = scan(text)
        assert result.total_invisible_count == 2
        assert result.categories["bidi"] == 2
        # No zero-width chars, so likely_source should be copy_paste
        assert result.context["likely_source"] == "copy_paste"

    def test_detects_unusual_whitespace(self):
        text = "Hello\u2003world"  # em space
        result = scan(text)
        assert result.has_invisible_chars is True
        assert result.categories["whitespace"] == 1

    def test_detects_deprecated_formatting(self):
        text = "test\u206Atext"
        result = scan(text)
        assert result.has_invisible_chars is True
        assert result.categories["deprecated"] == 1

    def test_findings_sorted_by_threat_level(self):
        # Mix of high, medium, low threat chars
        text = "\u200B\u200E\u2003"  # high, medium, low
        result = scan(text)
        assert result.findings[0].threat_level == "high"
        assert result.findings[1].threat_level == "medium"
        assert result.findings[2].threat_level == "low"

    def test_multiple_same_char_counted(self):
        text = "a\u200Bb\u200Bc\u200B"
        result = scan(text)
        assert result.total_invisible_count == 3
        assert len(result.findings) == 1  # One finding type
        assert result.findings[0].count == 3
        assert result.findings[0].positions == [1, 3, 5]

    def test_positions_capped_at_50(self):
        text = "\u200B" * 100
        result = scan(text)
        assert result.findings[0].count == 100
        assert len(result.findings[0].positions) == 50

    def test_smart_chars_not_included_by_default(self):
        text = '\u201CHello\u201D'
        result = scan(text)
        assert result.smart_chars is None

    def test_smart_chars_detected_when_enabled(self):
        text = '\u201CHello,\u201D she said \u2014 loudly.'
        result = scan(text, include_smart_chars=True)
        assert result.smart_chars is not None
        assert len(result.smart_chars) == 3  # left quote, right quote, em-dash
        names = {s.name for s in result.smart_chars}
        assert "LEFT DOUBLE QUOTATION MARK" in names
        assert "RIGHT DOUBLE QUOTATION MARK" in names
        assert "EM DASH" in names

    def test_smart_chars_empty_list_when_none_found(self):
        result = scan("Hello world", include_smart_chars=True)
        assert result.smart_chars == []

    def test_context_tokenizer_artifact_when_zero_width(self):
        result = scan("text\u200Bhere")
        assert result.context["likely_source"] == "tokenizer_artifact"

    def test_context_formatting_for_whitespace_only(self):
        result = scan("text\u2003here")
        assert result.context["likely_source"] == "formatting"

    def test_text_with_only_invisible_chars(self):
        text = "\u200B\u200C\u200D"
        result = scan(text)
        assert result.has_invisible_chars is True
        assert result.total_invisible_count == 3
        assert result.char_count == 3

    def test_unicode_text_without_invisible_chars(self):
        # Normal unicode (accented chars, CJK, emoji) should NOT be flagged
        text = "Caf\u00e9 \u4e16\u754c Hello"
        result = scan(text)
        assert result.has_invisible_chars is False


class TestClean:
    def test_clean_already_clean_text(self):
        text = "Hello, world!"
        result = clean(text)
        assert result.cleaned_text == text
        assert result.chars_removed == 0
        assert result.original_length == result.cleaned_length

    def test_clean_empty_text(self):
        result = clean("")
        assert result.cleaned_text == ""
        assert result.chars_removed == 0

    def test_removes_zero_width_space(self):
        text = "Hello\u200Bworld"
        result = clean(text)
        assert result.cleaned_text == "Helloworld"
        assert result.chars_removed == 1
        assert result.original_length == 11
        assert result.cleaned_length == 10
        assert len(result.removals) == 1
        assert result.removals[0]["char"] == "U+200B"

    def test_removes_multiple_invisible_chars(self):
        text = "\uFEFFHello\u200B \u200Cworld\u200D"
        result = clean(text)
        assert result.cleaned_text == "Hello world"
        assert result.chars_removed == 4

    def test_removes_bom(self):
        text = "\uFEFFContent starts here"
        result = clean(text)
        assert result.cleaned_text == "Content starts here"
        assert result.chars_removed == 1

    def test_preserves_normal_unicode(self):
        text = "Caf\u00e9 na\u00efve r\u00e9sum\u00e9"
        result = clean(text)
        assert result.cleaned_text == text
        assert result.chars_removed == 0

    def test_smart_chars_not_normalized_by_default(self):
        text = '\u201CHello\u201D'
        result = clean(text)
        assert result.cleaned_text == text  # Smart quotes preserved
        assert result.chars_removed == 0

    def test_smart_chars_normalized_when_enabled(self):
        text = '\u201CHello,\u201D she said \u2014 loudly.'
        result = clean(text, normalize_smart_chars=True)
        assert result.cleaned_text == '"Hello," she said -- loudly.'
        assert result.chars_removed == 3

    def test_removals_list_has_correct_names(self):
        text = "a\u200Bb\u200Bc\u200C"
        result = clean(text)
        names = {r["name"] for r in result.removals}
        assert "ZERO WIDTH SPACE" in names
        assert "ZERO WIDTH NON-JOINER" in names

    def test_removals_counts_correct(self):
        text = "a\u200Bb\u200Bc"
        result = clean(text)
        zwsp_removal = [r for r in result.removals if r["char"] == "U+200B"][0]
        assert zwsp_removal["count"] == 2

    def test_cleans_all_invisible_categories(self):
        # One char from each category
        text = "a\u200Bb\u200Ec\u2003d\u206Ae\u2061f"
        result = clean(text)
        assert result.cleaned_text == "abcdef"
        assert result.chars_removed == 5

    def test_text_with_only_invisible_chars_becomes_empty(self):
        text = "\u200B\u200C\u200D"
        result = clean(text)
        assert result.cleaned_text == ""
        assert result.chars_removed == 3
