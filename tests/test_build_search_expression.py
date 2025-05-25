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