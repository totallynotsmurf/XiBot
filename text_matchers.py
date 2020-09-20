from textblob import TextBlob

from common import *

import re


# Helper classes for mapping inputs to responses.
class if_contains:
    def __init__(self, *strings):
        self.strings = list(strings)

    def __call__(self, string):
        return any([search_string in string for search_string in self.strings])


class if_matches:
    def __init__(self, *regexes):
        self.regexes = list(regexes)

    def __call__(self, string):
        return any([re.search(rgx, string) is not None for rgx in self.regexes])


class if_contains_word:
    def __init__(self, *words):
        self.words = list(words)

    def __call__(self, string):
        for word in self.words:
            for index in string_find_all(string, word):
                if (
                        (index == 0 or string[index - 1].isspace()) and
                        (index + len(word) >= len(string) or string[index + len(word)].isspace())
                ): return True

        return False


class sentiment_less_than:
    def __init__(self, value):
        self.value = value

    def __call__(self, string):
        return TextBlob(string).sentiment <= self.value


class sentiment_more_than:
    def __init__(self, value):
        self.value = value

    def __call__(self, string):
        return TextBlob(string).sentiment >= self.value


class logical_and:
    def __init__(self, *fns):
        self.fns = list(fns)

    def __call__(self, string):
        return all([fn(string) for fn in self.fns])


class logical_or:
    def __init__(self, *fns):
        self.fns = list(fns)

    def __call__(self, string):
        return any([fn(string) for fn in self.fns])


class logical_not:
    def __init__(self, fn):
        self.fn = fn

    def __call__(self, string):
        return not self.fn(string)