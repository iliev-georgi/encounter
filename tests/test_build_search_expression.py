import pytest
from src.helper import build_search_expression
from src.exception import UserInputException

def test_none_input_raises_user_input_exception():
    with pytest.raises(UserInputException):
        build_search_expression(partial = None)

def test_whitespace_input_returns_empty_string():
    assert build_search_expression("        ") == ""

def test_empty_input_returns_empty_string():
    assert build_search_expression("") == ""

def test_single_short_input_term_does_not_return_wildcard():
    assert build_search_expression("cor") == "'cor'"

def test_single_long_input_term_returns_wildcard():
    assert build_search_expression("corn") == "'corn*'"

def test_multiple_short_input_terms_return_and_without_wildcard():
    assert build_search_expression("cor bee") == "'cor' AND 'bee'"

def test_mixed_short_and_long_input_terms_return_and_with_wildcard_on_long_term():
    assert build_search_expression("corn bee") == "'corn*' AND 'bee'"

def test_multiple_long_input_terms_return_and_with_wildcard_on_all():
    assert build_search_expression("corn beef") == "'corn*' AND 'beef*'"


class TestPunctuationSanitization:
    """Tests for punctuation removal in search terms"""

    def test_period_removed(self):
        assert build_search_expression("dog.") == "'dog'"

    def test_comma_removed(self):
        assert build_search_expression("cat,") == "'cat'"

    def test_question_mark_removed(self):
        assert build_search_expression("what?") == "'what*'"

    def test_exclamation_removed(self):
        assert build_search_expression("wow!") == "'wow'"

    def test_apostrophe_removed(self):
        assert build_search_expression("it's") == "'it' AND 's'"

    def test_quotation_marks_removed(self):
        assert build_search_expression('"dog"') == "'dog'"

    def test_semicolon_removed(self):
        assert build_search_expression("dog; cat") == "'dog' AND 'cat'"

    def test_colon_removed(self):
        assert build_search_expression("dog: cat") == "'dog' AND 'cat'"

    def test_parentheses_removed(self):
        assert build_search_expression("dog(cat)") == "'dog' AND 'cat'"

    def test_hyphen_removed(self):
        assert build_search_expression("dog-cat") == "'dog' AND 'cat'"

    def test_brackets_removed(self):
        assert build_search_expression("dog[cat]") == "'dog' AND 'cat'"

    def test_mixed_punctuation_with_short_terms(self):
        assert build_search_expression("a.b c,d") == "'a' AND 'b' AND 'c' AND 'd'"

    def test_mixed_punctuation_with_long_terms(self):
        assert build_search_expression("abc.def ghi,jkl") == "'abc' AND 'def' AND 'ghi' AND 'jkl'"

    def test_punctuation_at_start(self):
        assert build_search_expression(".dog") == "'dog'"

    def test_punctuation_at_end(self):
        assert build_search_expression("dog.") == "'dog'"

    def test_multiple_punctuation_marks(self):
        assert build_search_expression("dog...cat!!!") == "'dog' AND 'cat'"

    def test_punctuation_between_words(self):
        assert build_search_expression("dog.cat.bee") == "'dog' AND 'cat' AND 'bee'"

