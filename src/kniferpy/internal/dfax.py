from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass

CharFilter = Callable[[str], bool]
"""Decides whether a single character participates in matching."""

Processor = Callable[["FoundWord"], str]
"""Replaces a found word during text filtering."""

DEFAULT_SEPARATOR = ","
"""Separator used by :func:`init_string` when none is provided."""


@dataclass(frozen=True, slots=True)
class FoundWord:
    """A matched dictionary word and its location in the input."""

    word: str
    found_word: str
    start: int
    end: int

    def __str__(self) -> str:
        return self.found_word


class _Node:
    __slots__ = ("children", "end", "word")

    def __init__(self) -> None:
        self.children: dict[str, _Node] = {}
        self.end: bool = False
        self.word: str = ""


# The default set of runes ignored while building and scanning the trie. It is
# ported verbatim from knifer-go so that matching behaviour stays identical.
_STOP_CHARS = (
    " '、。·ˉˇ々—～‖…‘’“”〔〕〈〉《》「」『』〖〗【】±＋－×÷∧∨∑∏∪∩∈√⊥⊙∫∮≡≌≈∽∝≠≮≯≤≥∞∶∵∴∷"
    "♂♀°′〃℃＄¤￠￡‰§☆★〇○●◎◇◆□■△▽⊿▲▼◣◤◢◥▁▂▃▄▅▆▇█▉▊▋▌▍▎▏▓※→←↑↓↖↗↘↙〓"
    "ⅰⅱⅲⅳⅴⅵⅶⅷⅸⅹ①②③④⑤⑥⑦⑧⑨⑩⒈⒉⒊⒋⒌⒍⒎⒏⒐⒑⒒⒓⒔⒕⒖⒗⒘⒙⒚⒛"
    "⑴⑵⑶⑷⑸⑹⑺⑻⑼⑽⑾⑿⒀⒁⒂⒃⒄⒅⒆⒇ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ"
    "！＃￥％＆（）＊，．／０１２３４５６７８９：；＜＝＞？＠＼＾＿｛｜｝"
    "ΡΥΦΧΨΩαβγδεζηθικλμνξοπρστυφχψω﹊﹍╭╮╰╯\ue83a"
    '_^/\\"<>`{}~()-$@*&#卐㎎㎏㎜㎝㎞㎡㏄㏎㏑㏒㏕+=?:.!;]|%'
)
_STOP_RUNES: frozenset[str] = frozenset(_STOP_CHARS)


def is_stop_char(char: str) -> bool:
    """Report whether ``char`` should be ignored by the default matcher."""
    return char.isspace() or char in _STOP_RUNES


def is_not_stop_char(char: str) -> bool:
    """Report whether ``char`` should participate in matching."""
    return not is_stop_char(char)


def default_processor(word: FoundWord) -> str:
    """Replace each character of the matched text with an asterisk."""
    return "*" * len(word.found_word)


class WordTree:
    """A rune trie that matches dictionary words with DFA-style scans.

    Characters rejected by the character filter (punctuation, whitespace, and
    other separators by default) are skipped both when adding words and when
    scanning input, so ``bad`` still matches ``b-a-d``.
    """

    __slots__ = ("_char_filter", "_root")

    def __init__(self, *, char_filter: CharFilter | None = None) -> None:
        self._root = _Node()
        self._char_filter: CharFilter = char_filter or is_not_stop_char

    def set_char_filter(self, char_filter: CharFilter | None) -> WordTree:
        """Set the filter deciding whether a character participates in matching."""
        if char_filter is not None:
            self._char_filter = char_filter
        return self

    def add_words(self, *words: str) -> WordTree:
        """Add every word to the tree, ignoring duplicates."""
        seen: set[str] = set()
        for word in words:
            if word in seen:
                continue
            seen.add(word)
            self.add_word(word)
        return self

    def add_word(self, word: str) -> WordTree:
        """Add a single word to the tree after filtering ignored characters."""
        char_filter = self._char_filter
        current = self._root
        accepted: list[str] = []
        for char in word:
            if not char_filter(char):
                continue
            child = current.children.get(char)
            if child is None:
                child = _Node()
                current.children[char] = child
            current = child
            accepted.append(char)
        if accepted:
            current.end = True
            current.word = "".join(accepted)
        return self

    def clear(self) -> None:
        """Remove all words from the tree."""
        self._root = _Node()

    def is_empty(self) -> bool:
        """Report whether the tree contains no words."""
        return not self._root.children

    def is_match(self, text: str) -> bool:
        """Report whether ``text`` contains at least one word from the tree."""
        return self.match_word(text) is not None

    def match(self, text: str) -> str | None:
        """Return the first matched text, or ``None`` when nothing matches."""
        found = self.match_word(text)
        return found.found_word if found is not None else None

    def match_word(self, text: str) -> FoundWord | None:
        """Return the first matched word with position metadata."""
        words = self.match_all_words(text, 1, False, False)
        return words[0] if words else None

    def match_all(self, text: str) -> list[str]:
        """Return every matched text without a limit."""
        return self.match_all_limit(text, -1)

    def match_all_limit(self, text: str, limit: int) -> list[str]:
        """Return matched texts up to ``limit``. A non-positive limit means no limit."""
        return self.match_all_mode(text, limit, False, False)

    def match_all_mode(
        self, text: str, limit: int, density_match: bool, greed_match: bool
    ) -> list[str]:
        """Return matched texts with dense and greedy matching controls."""
        words = self.match_all_words(text, limit, density_match, greed_match)
        return [word.found_word for word in words]

    def match_all_words(
        self,
        text: str,
        limit: int = -1,
        density_match: bool = False,
        greed_match: bool = False,
    ) -> list[FoundWord]:
        """Return found words with dense and greedy matching controls.

        A non-positive ``limit`` returns every match. When ``density_match`` is
        false the scan resumes past the end of each match; when it is true but
        ``greed_match`` is false the scan stops at the shortest match starting
        at a position.
        """
        if text == "":
            return []
        runes = list(text)
        char_filter = self._char_filter
        found: list[FoundWord] = []
        n = len(runes)
        i = 0
        while i < n:
            if not char_filter(runes[i]):
                i += 1
                continue
            current = self._root
            found_runes: list[str] = []
            key_runes: list[str] = []
            j = i
            while j < n:
                r = runes[j]
                if not char_filter(r):
                    if found_runes:
                        found_runes.append(r)
                    j += 1
                    continue
                child = current.children.get(r)
                if child is None:
                    break
                found_runes.append(r)
                key_runes.append(r)
                current = child
                if current.end:
                    word = current.word or "".join(key_runes)
                    found.append(
                        FoundWord(
                            word=word,
                            found_word="".join(found_runes),
                            start=i,
                            end=j,
                        )
                    )
                    if limit > 0 and len(found) >= limit:
                        return found
                    if not density_match:
                        i = j
                        break
                    if not greed_match:
                        break
                j += 1
            i += 1
        return found

    def filter(
        self, text: str, greed_match: bool = False, processor: Processor | None = None
    ) -> str:
        """Replace matched words in ``text`` using ``processor`` or the default mask."""
        if text == "":
            return text
        found = self.match_all_words(text, -1, True, greed_match)
        if not found:
            return text
        if processor is None:
            processor = default_processor
        by_start = {word.start: word for word in found}
        runes = list(text)
        out: list[str] = []
        n = len(runes)
        i = 0
        while i < n:
            word = by_start.get(i)
            if word is not None:
                out.append(processor(word))
                i = word.end + 1
                continue
            out.append(runes[i])
            i += 1
        return "".join(out)


def new_word_tree(*, char_filter: CharFilter | None = None) -> WordTree:
    """Create an empty word tree using the default stop-rune filter."""
    return WordTree(char_filter=char_filter)


# --- Package-level default matcher ------------------------------------------

_matcher_lock = threading.Lock()
_matcher = WordTree()


def _current_matcher() -> WordTree:
    return _matcher


def is_inited() -> bool:
    """Report whether the package-level matcher contains words."""
    return not _current_matcher().is_empty()


def init(words: list[str], *, char_filter: CharFilter | None = None) -> None:
    """Replace the package-level matcher with ``words``."""
    global _matcher
    tree = WordTree(char_filter=char_filter)
    tree.add_words(*words)
    with _matcher_lock:
        _matcher = tree


def init_string(
    words: str,
    separator: str = DEFAULT_SEPARATOR,
    *,
    char_filter: CharFilter | None = None,
) -> None:
    """Initialize the package-level matcher from a separated string."""
    if separator == "":
        separator = DEFAULT_SEPARATOR
    clean = [part.strip() for part in words.split(separator) if part.strip()]
    init(clean, char_filter=char_filter)


def set_char_filter(char_filter: CharFilter | None) -> None:
    """Set the filter used by the package-level matcher."""
    if char_filter is not None:
        _current_matcher().set_char_filter(char_filter)


def contains(text: str) -> bool:
    """Report whether ``text`` contains a word from the package-level matcher."""
    return _current_matcher().is_match(text)


def get_found_first(text: str) -> FoundWord | None:
    """Return the first found word from the package-level matcher."""
    return _current_matcher().match_word(text)


def get_found_all(text: str) -> list[FoundWord]:
    """Return all found words from the package-level matcher."""
    return _current_matcher().match_all_words(text, -1, False, False)


def get_found_all_mode(text: str, density_match: bool, greed_match: bool) -> list[FoundWord]:
    """Return all found words with dense and greedy matching controls."""
    return _current_matcher().match_all_words(text, -1, density_match, greed_match)


def filter(text: str, greed_match: bool = True, processor: Processor | None = None) -> str:
    """Replace words found by the package-level matcher."""
    return _current_matcher().filter(text, greed_match, processor)


def contains_any(text: str) -> bool:
    """Report whether ``text`` contains any word from the package-level matcher (alias for contains)."""
    return contains(text)


def get_found_first_any(text: str) -> FoundWord | None:
    """Return the first found word from the package-level matcher (alias for get_found_first)."""
    return get_found_first(text)


def get_found_all_any(text: str) -> list[FoundWord]:
    """Return all found words from the package-level matcher (alias for get_found_all)."""
    return get_found_all(text)


def filter_mode(text: str, density_match: bool, greed_match: bool,
                processor: Processor | None = None) -> str:
    """Replace words found by the package-level matcher with density/greedy controls."""
    matcher = _current_matcher()
    if text == "":
        return text
    found = matcher.match_all_words(text, -1, density_match, greed_match)
    if not found:
        return text
    if processor is None:
        processor = default_processor
    by_start = {word.start: word for word in found}
    runes = list(text)
    out: list[str] = []
    n = len(runes)
    i = 0
    while i < n:
        word = by_start.get(i)
        if word is not None:
            out.append(processor(word))
            i = word.end + 1
            continue
        out.append(runes[i])
        i += 1
    return "".join(out)


def filter_any(text: str, greed_match: bool = True, processor: Processor | None = None) -> str:
    """Replace words found by the package-level matcher (alias for filter)."""
    return filter(text, greed_match, processor)
