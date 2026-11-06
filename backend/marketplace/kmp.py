"""Knuth-Morris-Pratt string search (Knuth, Morris and Pratt, 1977).

Finds a keyword inside a text in O(n + m) time by never moving back in the text:
when a mismatch happens, the 'failure table' tells us how much of the pattern
we can reuse instead of starting over.
"""


def build_failure_table(pattern):
    """table[i] = length of the longest proper prefix of pattern[:i+1] that is also its suffix."""
    table = [0] * len(pattern)
    length = 0
    for i in range(1, len(pattern)):
        while length > 0 and pattern[i] != pattern[length]:
            length = table[length - 1]
        if pattern[i] == pattern[length]:
            length += 1
        table[i] = length
    return table


def kmp_find(text, pattern):
    """Return the index of the first match of pattern in text, or -1. Case-insensitive."""
    text, pattern = text.lower(), pattern.lower()
    if not pattern:
        return 0
    table = build_failure_table(pattern)
    matched = 0
    for i, char in enumerate(text):
        while matched > 0 and char != pattern[matched]:
            matched = table[matched - 1]
        if char == pattern[matched]:
            matched += 1
        if matched == len(pattern):
            return i - matched + 1
    return -1


def kmp_contains(text, pattern):
    return kmp_find(text, pattern) != -1


def matches_all_terms(text, query):
    """Every word typed by the buyer must be found in the text ('iphone 128' finds 'iPhone 13 128GB')."""
    return all(kmp_contains(text, term) for term in query.split())
