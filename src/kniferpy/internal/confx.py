from __future__ import annotations

import os
import re
from pathlib import Path

from kniferpy.internal import convx
from kniferpy.verr import ValidationError

# The default (ungrouped) section, matching knifer-go's empty group name.
_DEFAULT_GROUP = ""

# Matches ``$name`` and ``${name}`` placeholders the way Go's os.Expand does.
_PLACEHOLDER_RE = re.compile(r"\$(\w+)|\$\{([^}]*)\}")

# Guards against runaway recursion while resolving nested placeholders.
_MAX_EXPAND_DEPTH = 64

# Alias captured before ``Conf.set`` shadows the builtin ``set`` in annotations.
_StrSet = set[str]


def _unquote(value: str) -> str:
    """Strip a single pair of matching surrounding quotes."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def _split_list(text: str) -> list[str]:
    """Split a comma-separated value into trimmed, non-empty-aware parts."""
    if not text.strip():
        return []
    return [part.strip() for part in text.split(",")]


class Conf:
    """Grouped key-value configuration parsed from properties/INI text.

    Values live in named groups (INI ``[section]`` headers); the default group
    is the empty string. Typed getters fall back to a supplied default when a
    key is missing or unparseable, mirroring knifer-go's fail-safe accessors.
    """

    __slots__ = ("_data",)

    def __init__(self) -> None:
        self._data: dict[str, dict[str, str]] = {_DEFAULT_GROUP: {}}

    # --- Lookups ------------------------------------------------------------

    def lookup(self, group: str, key: str) -> tuple[str, bool]:
        """Return ``(value, found)`` for a grouped key."""
        section = self._data.get(group)
        if section is None or key not in section:
            return "", False
        return section[key], True

    def get(self, key: str) -> str:
        """Return a default-group value, or empty string when absent."""
        return self.get_by_group(_DEFAULT_GROUP, key)

    def get_by_group(self, group: str, key: str) -> str:
        """Return a grouped value, or empty string when absent."""
        value, _ = self.lookup(group, key)
        return value

    def get_or_default(self, key: str, default: str) -> str:
        """Return a default-group value, or ``default`` when absent."""
        value, ok = self.lookup(_DEFAULT_GROUP, key)
        return value if ok else default

    def get_int(self, key: str, default: int = 0, group: str = _DEFAULT_GROUP) -> int:
        """Return an int value, or ``default`` when absent or unparseable."""
        value, ok = self.lookup(group, key)
        if not ok:
            return default
        return convx.to_int(value, default)

    def get_float(self, key: str, default: float = 0.0, group: str = _DEFAULT_GROUP) -> float:
        """Return a float value, or ``default`` when absent or unparseable."""
        value, ok = self.lookup(group, key)
        if not ok:
            return default
        return convx.to_float(value, default)

    def get_bool(self, key: str, default: bool = False, group: str = _DEFAULT_GROUP) -> bool:
        """Return a bool value, or ``default`` when absent or unparseable."""
        value, ok = self.lookup(group, key)
        if not ok:
            return default
        return convx.to_bool(value, default)

    def get_list(self, key: str, group: str = _DEFAULT_GROUP) -> list[str]:
        """Return a comma-separated value as a list of trimmed parts."""
        value, ok = self.lookup(group, key)
        if not ok:
            return []
        return _split_list(value)

    def get_expanded(self, key: str, group: str = _DEFAULT_GROUP) -> str:
        """Return a grouped value with ``${...}`` placeholders resolved."""
        value, ok = self.lookup(group, key)
        if not ok:
            return ""
        return self._expand_value(group, value, set(), 0)

    # --- Mutators -----------------------------------------------------------

    def set(self, key: str, value: str) -> None:
        """Store a value in the default group."""
        self.set_by_group(_DEFAULT_GROUP, key, value)

    def set_by_group(self, group: str, key: str, value: str) -> None:
        """Store a grouped value, creating the group when needed."""
        self._data.setdefault(group, {})[key] = value

    def delete(self, key: str) -> None:
        """Remove a key from the default group."""
        self.delete_by_group(_DEFAULT_GROUP, key)

    def delete_by_group(self, group: str, key: str) -> None:
        """Remove a key from a group."""
        section = self._data.get(group)
        if section is not None:
            section.pop(key, None)

    # --- Introspection ------------------------------------------------------

    def groups(self) -> list[str]:
        """Return all group names in sorted order."""
        return sorted(self._data)

    def keys(self, group: str = _DEFAULT_GROUP) -> list[str]:
        """Return all keys in a group in sorted order."""
        return sorted(self._data.get(group, {}))

    def to_dict(self) -> dict[str, dict[str, str]]:
        """Return a deep copy of all groups."""
        return {group: dict(section) for group, section in self._data.items()}

    def clone(self) -> Conf:
        """Return an independently mutable deep copy."""
        out = Conf()
        out._data = self.to_dict()
        return out

    # --- Composition --------------------------------------------------------

    def merge(self, other: Conf | None) -> Conf:
        """Overlay ``other`` onto this config; existing keys are overwritten."""
        if other is None:
            return self
        for group, section in other._data.items():
            for key, value in section.items():
                self.set_by_group(group, key, value)
        return self

    def expand(self) -> Conf:
        """Return a copy with every value's ``${...}`` placeholders resolved."""
        out = Conf()
        for group, section in self._data.items():
            for key, value in section.items():
                out.set_by_group(
                    group,
                    key,
                    self._expand_value(group, value, {f"{group}.{key}"}, 0),
                )
        return out

    def apply_profile(self, profile: str) -> Conf:
        """Overlay ``profile.<profile>`` and ``profile.<profile>.<group>`` groups."""
        out = Conf()
        profile = profile.strip()
        prefix = "profile." + profile

        for group, section in self._data.items():
            if profile and group == "profile":
                continue
            if profile and (group == prefix or group.startswith(prefix + ".")):
                continue
            for key, value in section.items():
                out.set_by_group(group, key, value)

        if not profile:
            return out

        for group, section in self._data.items():
            if group != prefix and not group.startswith(prefix + "."):
                continue
            target_group = _DEFAULT_GROUP
            if group.startswith(prefix + "."):
                target_group = group[len(prefix) + 1 :]
            for key, value in section.items():
                out.set_by_group(target_group, key, value)

        profile_group = self._data.get("profile", {})
        key_prefix = profile + "."
        for key, value in profile_group.items():
            if not key.startswith(key_prefix):
                continue
            rest = key[len(key_prefix) :]
            if not rest:
                continue
            target_group = _DEFAULT_GROUP
            target_key = rest
            dot = rest.rfind(".")
            if dot >= 0:
                target_group = rest[:dot]
                target_key = rest[dot + 1 :]
            out.set_by_group(target_group, target_key, value)

        return out

    # --- Internal helpers ---------------------------------------------------

    def _expand_value(self, group: str, value: str, seen: _StrSet, depth: int) -> str:
        if depth > _MAX_EXPAND_DEPTH:
            return value

        def replace(match: re.Match[str]) -> str:
            name = match.group(1) if match.group(1) is not None else match.group(2)
            if name.startswith("ENV:"):
                return os.environ.get(name[4:], "")
            key, sep, fallback = name.partition(":")
            has_fallback = sep == ":"
            lookup_group = group
            lookup_key = key
            dot = key.find(".")
            if dot > 0:
                lookup_group, lookup_key = key[:dot], key[dot + 1 :]
            seen_key = f"{lookup_group}.{lookup_key}"
            if seen_key in seen:
                return fallback if has_fallback else ""
            resolved, ok = self.lookup(lookup_group, lookup_key)
            if not ok:
                return fallback if has_fallback else ""
            seen.add(seen_key)
            try:
                return self._expand_value(lookup_group, resolved, seen, depth + 1)
            finally:
                seen.discard(seen_key)

        return _PLACEHOLDER_RE.sub(replace, value)


def new() -> Conf:
    """Create an empty :class:`Conf`."""
    return Conf()


def parse(content: str) -> Conf:
    """Parse properties/INI text into a :class:`Conf`.

    Blank lines and ``#``/``;`` comments are ignored. ``[section]`` headers
    switch groups. Keys and values are separated by ``=`` or ``:`` and trimmed;
    a single pair of surrounding quotes is stripped from values.
    """
    conf = Conf()
    group = _DEFAULT_GROUP
    for line_no, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        if line.startswith("[") and line.endswith("]"):
            group = line[1:-1].strip()
            conf._data.setdefault(group, {})
            continue
        sep_index = _first_index_any(line, "=:")
        if sep_index < 0:
            raise ValidationError(
                message=f"invalid setting line {line_no}: {line}",
                code="knifer.conf.invalid_line",
            )
        key = line[:sep_index].strip()
        value = line[sep_index + 1 :].strip()
        if not key:
            raise ValidationError(
                message=f"empty setting key at line {line_no}",
                code="knifer.conf.empty_key",
            )
        conf.set_by_group(group, key, _unquote(value))
    return conf


def parse_bytes(content: bytes) -> Conf:
    """Parse UTF-8 properties/INI bytes into a :class:`Conf`."""
    return parse(content.decode("utf-8"))


def load(path: str | Path) -> Conf:
    """Read and parse a properties/INI file from ``path``."""
    text = Path(path).read_text(encoding="utf-8")
    return parse(text)


def load_files(*paths: str | Path) -> Conf:
    """Load multiple files and merge them in order (later overrides earlier)."""
    out = Conf()
    for path in paths:
        out.merge(load(path))
    return out


def load_profile(path: str | Path, profile: str) -> Conf:
    """Load a file and apply profile-specific overrides."""
    return load(path).apply_profile(profile)


def merge(*configs: Conf) -> Conf:
    """Merge configs in order; later configs override earlier ones."""
    out = Conf()
    for config in configs:
        out.merge(config)
    return out


def _first_index_any(text: str, chars: str) -> int:
    """Return the lowest index of any character in ``chars``, or -1."""
    best = -1
    for ch in chars:
        idx = text.find(ch)
        if idx >= 0 and (best < 0 or idx < best):
            best = idx
    return best
