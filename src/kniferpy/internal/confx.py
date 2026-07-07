from __future__ import annotations

import dataclasses
import hashlib
import os
import re
import threading
import urllib.parse
from pathlib import Path
from typing import Any, Callable

from kniferpy.internal import convx
from kniferpy.verr import ValidationError

# Field type constants (mirrors Go's TypeString, TypeBool, etc.)
TypeString = "str"
TypeBool = "bool"
TypeInt = "int"
TypeFloat = "float"
TypeList = "list"

# Default max bytes for remote loading (16 MiB, matches Go's DefaultMaxBytes).
DefaultMaxBytes = 16 << 20

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

    def get_by_group_expanded(self, group: str, key: str) -> str:
        """Return a grouped value with ``${...}`` placeholders resolved."""
        return self.get_expanded(key, group)

    def get_int_by_group(self, group: str, key: str, default: int = 0) -> int:
        """Return an int value from a named group."""
        return self.get_int(key, default, group)

    def get_bool_by_group(self, group: str, key: str, default: bool = False) -> bool:
        """Return a bool value from a named group."""
        return self.get_bool(key, default, group)

    def get_int_e(self, key: str, group: str = _DEFAULT_GROUP) -> int:
        """Return an int value or raise ValidationError."""
        value, ok = self.lookup(group, key)
        if not ok:
            raise ValidationError(
                message=f"key {key!r} not found", code="knifer.conf.key_not_found"
            )
        return convx.to_int(value, 0)

    def get_bool_e(self, key: str, group: str = _DEFAULT_GROUP) -> bool:
        """Return a bool value or raise ValidationError."""
        value, ok = self.lookup(group, key)
        if not ok:
            raise ValidationError(
                message=f"key {key!r} not found", code="knifer.conf.key_not_found"
            )
        return convx.to_bool(value)

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

    def decrypt_values(self, decrypt: Callable[[str], str]) -> Conf:
        """Return a copy with every value decrypted via ``decrypt``."""
        out = Conf()
        for group, section in self._data.items():
            for key, value in section.items():
                try:
                    out.set_by_group(group, key, decrypt(value))
                except Exception:
                    out.set_by_group(group, key, value)
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


class ConfError(ValidationError):
    """Configuration error with error code and optional cause."""

    def __init__(self, message: str, cause: BaseException | None = None) -> None:
        super().__init__(message=message, code="knifer.conf.error")
        self.cause = cause

    def __str__(self) -> str:
        if self.cause is not None:
            return f"{self.message}: {self.cause}"
        return self.message


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


# ---------------------------------------------------------------------------
# Watch — file watching via polling
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class WatchEvent:
    path: str
    old_config: Conf | None
    new_config: Conf


_WatchCallback = Callable[[WatchEvent], None]


def _default_watch_runner(
    path: str,
    interval: float,
    onChange: _WatchCallback,
    stop: threading.Event,
) -> None:
    last_hash = ""
    while not stop.is_set():
        try:
            data = Path(path).read_bytes()
            current_hash = hashlib.sha256(data).hexdigest()
        except OSError:
            stop.wait(interval)
            continue

        if last_hash and current_hash != last_hash:
            try:
                old = load(path)
                new = load(path)
                onChange(WatchEvent(path=path, old_config=old, new_config=new))
            except Exception:
                pass
        elif not last_hash:
            last_hash = current_hash
        else:
            last_hash = current_hash

        stop.wait(interval)


def watch(
    path: str | Path,
    onChange: Callable[[WatchEvent], None],
    *,
    interval: float = 1.0,
) -> threading.Thread:
    """Watch a file for changes via polling.

    Returns a thread that can be stopped via ``.stop()``.
    """
    path_str = str(path)
    stop = threading.Event()
    t = threading.Thread(
        target=_default_watch_runner,
        args=(path_str, interval, onChange, stop),
        daemon=True,
    )
    t._conf_stop = stop  # type: ignore[attr-defined]
    t.start()
    return t


# ---------------------------------------------------------------------------
# Bind — struct binding via dataclass fields
# ---------------------------------------------------------------------------


def _conf_field_name(field: dataclasses.Field[Any]) -> str:
    """Extract config key from dataclass field metadata."""
    name = field.name
    if field.metadata and "conf" in field.metadata:
        name = field.metadata["conf"]
    return name


def _set_reflect_value(obj: Any, field: dataclasses.Field[Any], value: Any) -> None:
    """Set a dataclass field value with type coercion."""
    field_type = field.type
    # With from __future__ import annotations, field.type may be a string
    type_str = str(field_type) if not isinstance(field_type, type) else ""
    try:
        if field_type is int or type_str == "int" or type_str == "<class 'int'>":
            setattr(obj, field.name, int(value))
        elif field_type is float or type_str == "float" or type_str == "<class 'float'>":
            setattr(obj, field.name, float(value))
        elif field_type is bool or type_str == "bool" or type_str == "<class 'bool'>":
            setattr(obj, field.name, convx.to_bool(str(value)))
        elif field_type is list[str] or type_str in ("list[str]", "list"):
            setattr(obj, field.name, _split_list(str(value)))
        else:
            setattr(obj, field.name, value)
    except (ValueError, TypeError):
        pass


def bind(conf: Conf, obj: Any) -> None:
    """Bind configuration values to a dataclass instance."""
    bind_group(conf, _DEFAULT_GROUP, obj)


def bind_group(conf: Conf, group: str, obj: Any) -> None:
    """Bind configuration values from a group to a dataclass instance."""
    for field in dataclasses.fields(obj):
        key = _conf_field_name(field)
        value, ok = conf.lookup(group, key)
        if ok:
            _set_reflect_value(obj, field, value)


# ---------------------------------------------------------------------------
# Schema — validation rules
# ---------------------------------------------------------------------------


_FIELD_TYPE_STR = "str"
_FIELD_TYPE_BOOL = "bool"
_FIELD_TYPE_INT = "int"
_FIELD_TYPE_FLOAT = "float"
_FIELD_TYPE_LIST = "list"


@dataclasses.dataclass
class FieldRule:
    group: str = ""
    key: str = ""
    required: bool = False
    type: str = _FIELD_TYPE_STR
    default: str = ""
    choices: list[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Schema:
    fields: list[FieldRule] = dataclasses.field(default_factory=list)


def _validate_type(value: str, field_type: str) -> bool:
    if field_type == _FIELD_TYPE_BOOL:
        return value.lower() in ("true", "false", "1", "0", "yes", "no", "on", "off")
    if field_type == _FIELD_TYPE_INT:
        try:
            int(value)
            return True
        except ValueError:
            return False
    if field_type == _FIELD_TYPE_FLOAT:
        try:
            float(value)
            return True
        except ValueError:
            return False
    return True


def validate_schema(conf: Conf, schema: Schema) -> list[str]:
    """Validate a Conf against a Schema. Returns a list of error messages."""
    errors: list[str] = []
    for rule in schema.fields:
        value, ok = conf.lookup(rule.group, rule.key)
        if rule.required and not ok:
            errors.append(f"{rule.group}.{rule.key}: required but missing")
            continue
        if not ok:
            continue
        if not _validate_type(value, rule.type):
            errors.append(f"{rule.group}.{rule.key}: expected {rule.type}, got {value!r}")
        if rule.choices and value not in rule.choices:
            errors.append(f"{rule.group}.{rule.key}: {value!r} not in {rule.choices}")
    return errors


def apply_defaults(conf: Conf, schema: Schema) -> Conf:
    """Apply schema defaults to missing keys."""
    for rule in schema.fields:
        if rule.default and not conf.lookup(rule.group, rule.key)[1]:
            conf.set_by_group(rule.group, rule.key, rule.default)
    return conf


def _infer_rule_type(field_type: type) -> str:
    if field_type is bool:
        return _FIELD_TYPE_BOOL
    if field_type is int:
        return _FIELD_TYPE_INT
    if field_type is float:
        return _FIELD_TYPE_FLOAT
    if field_type is list[str] or field_type is list:
        return _FIELD_TYPE_LIST
    return _FIELD_TYPE_STR


def _parse_conf_tag(tag: str) -> dict[str, str]:
    """Parse a conf tag like 'keyname,required,default:val' into a dict."""
    result: dict[str, str] = {}
    parts = tag.split(",")
    if parts:
        result["key"] = parts[0]
    for part in parts[1:]:
        part = part.strip()
        if part == "required":
            result["required"] = "true"
        elif part.startswith("default:"):
            result["default"] = part[8:]
        elif part.startswith("choices:"):
            result["choices"] = part[8:]
        elif part.startswith("group:"):
            result["group"] = part[6:]
    return result


def schema_from_struct(obj: Any) -> Schema:
    """Build a Schema from a dataclass with conf metadata tags."""
    rules: list[FieldRule] = []
    for field in dataclasses.fields(obj):
        conf_meta = field.metadata.get("conf", "") if hasattr(field.metadata, "get") else ""
        if isinstance(conf_meta, dict):
            conf_meta = conf_meta.get("key", "")

        tag = _parse_conf_tag(conf_meta) if conf_meta else {}
        field_type = field.type
        if not isinstance(field_type, type):
            # String annotation from __future__
            type_str = str(field_type)
            if "int" in type_str:
                field_type = int
            elif "float" in type_str:
                field_type = float
            elif "bool" in type_str:
                field_type = bool
            elif "list" in type_str:
                field_type = list[str]
            else:
                field_type = str

        rule = FieldRule(
            group=tag.get("group", _DEFAULT_GROUP),
            key=tag.get("key", field.name),
            required=tag.get("required") == "true",
            type=_infer_rule_type(field_type),
            default=tag.get("default", ""),
            choices=tag.get("choices", "").split("|") if tag.get("choices") else [],
        )
        rules.append(rule)
    return Schema(fields=rules)


def validate_struct(conf: Conf, obj: Any) -> list[str]:
    """Validate a dataclass-backed Conf using its schema."""
    return validate_schema(conf, schema_from_struct(obj))


def validate_struct_with_options(conf: Conf, obj: Any, **_opts: Any) -> list[str]:
    """Validate a dataclass-backed Conf using its schema with options."""
    return validate_schema(conf, schema_from_struct(obj))


def bind_with_options(conf: Conf, obj: Any, **_opts: Any) -> None:
    """Bind configuration values to a dataclass with options."""
    bind(conf, obj)


def bind_group_with_options(conf: Conf, group: str, obj: Any, **_opts: Any) -> None:
    """Bind configuration values from a group to a dataclass with options."""
    bind_group(conf, group, obj)


# ---------------------------------------------------------------------------
# Base64 decryption
# ---------------------------------------------------------------------------


def base64_decrypt(cipher_text: str) -> str:
    """Decode a Base64-encoded ciphertext into a plaintext string."""
    import base64

    return base64.b64decode(cipher_text).decode("utf-8")


# ---------------------------------------------------------------------------
# LoadOptions
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class LoadOptions:
    """Options for loading configuration files."""

    max_bytes: int = DefaultMaxBytes
    decrypt: Callable[[str], str] | None = None


def load_with_options(path: str | Path, opts: LoadOptions | None = None) -> Conf:
    """Load a file with options (decryption, max bytes)."""
    conf = load(path)
    if opts and opts.decrypt:
        conf = conf.decrypt_values(opts.decrypt)
    return conf


def load_files_with_options(paths: list[str | Path], opts: LoadOptions | None = None) -> Conf:
    """Load multiple files with options."""
    out = Conf()
    for path in paths:
        out.merge(load_with_options(path, opts))
    return out


def parse_by_ext_with_options(content: str, ext: str, **_opts: Any) -> Conf:
    """Parse content by extension with options."""
    return parse_by_ext(content, ext)


def parse_yaml_full(content: str) -> Conf:
    """Parse YAML content into a Conf (same as parse_yaml)."""
    return parse_yaml(content)


def parse_yaml_full_with_options(content: str, **_opts: Any) -> Conf:
    """Parse YAML content into a Conf with options."""
    return parse_yaml(content)


def parse_toml_with_options(content: str, **_opts: Any) -> Conf:
    """Parse TOML content into a Conf with options."""
    return parse_toml(content)


def watch_with_options(
    path: str | Path,
    onChange: Callable[[WatchEvent], None],
    *,
    interval: float = 1.0,
    **_opts: Any,
) -> threading.Thread:
    """Watch a file for changes with options. Returns a daemon thread."""
    return watch(path, onChange, interval=interval)


def _is_private_host(hostname: str) -> bool:
    """Check if a hostname resolves to a private IP."""
    import ipaddress
    import socket

    try:
        info = socket.getaddrinfo(hostname, None)
        for _, _, _, _, sockaddr in info:
            ip = ipaddress.ip_address(sockaddr[0])
            if ip.is_loopback or ip.is_private or ip.is_link_local:
                return True
    except (socket.gaierror, OSError):
        return True
    return False


def load_remote(url: str, timeout: float = 10.0) -> Conf:
    """Load configuration from a remote URL."""
    import urllib.request

    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = resp.read()
            return parse_bytes(data)
    except Exception as exc:
        raise ValidationError(
            message=f"failed to load remote config: {url}",
            code="knifer.conf.load_remote_failed",
            context={"url": url, "error": str(exc)},
        ) from exc


def load_remote_safe(url: str, timeout: float = 10.0) -> Conf:
    """Load configuration from a remote URL with SSRF protection."""
    parsed = urllib.parse.urlparse(url)
    if parsed.hostname is None:
        raise ValidationError(
            message=f"invalid remote URL: {url}",
            code="knifer.conf.invalid_url",
            context={"url": url},
        )
    if _is_private_host(parsed.hostname):
        raise ValidationError(
            message=f"remote URL resolves to private host: {parsed.hostname}",
            code="knifer.conf.private_host",
            context={"url": url, "hostname": parsed.hostname},
        )
    return load_remote(url, timeout)


# ---------------------------------------------------------------------------
# Parse by extension — YAML / TOML / JSON / INI
# ---------------------------------------------------------------------------


def parse_by_ext(content: str, ext: str) -> Conf:
    """Parse content according to file extension (``.yaml``, ``.toml``, ``.json``, ``.ini``)."""
    ext = ext.lower().lstrip(".")
    if ext in ("yaml", "yml"):
        return parse_yaml(content)
    if ext == "toml":
        return parse_toml(content)
    if ext == "json":
        return parse_json(content)
    return parse(content)


def parse_yaml(content: str) -> Conf:
    """Parse YAML content into a Conf."""
    try:
        import yaml
    except ImportError:
        raise ValidationError(
            message="yaml parsing requires PyYAML: pip install pyyaml",
            code="knifer.conf.yaml_missing",
        ) from None
    try:
        data = yaml.safe_load(content)
    except Exception as exc:
        raise ValidationError(
            message=f"yaml parse error: {exc}",
            code="knifer.conf.yaml_parse_failed",
            context={"error": str(exc)},
        ) from exc
    return _flatten_to_conf(data)


def parse_toml(content: str) -> Conf:
    """Parse TOML content into a Conf."""
    try:
        import tomllib
    except ImportError:
        try:
            import toml as _toml

            data = _toml.loads(content)
        except ImportError:
            raise ValidationError(
                message="toml parsing requires tomli/tomllib (Python 3.11+) or toml",
                code="knifer.conf.toml_missing",
            ) from None
        except Exception as exc:
            raise ValidationError(
                message=f"toml parse error: {exc}",
                code="knifer.conf.toml_parse_failed",
                context={"error": str(exc)},
            ) from exc
    else:
        try:
            data = tomllib.loads(content)
        except Exception as exc:
            raise ValidationError(
                message=f"toml parse error: {exc}",
                code="knifer.conf.toml_parse_failed",
                context={"error": str(exc)},
            ) from exc
    return _flatten_to_conf(data)


def parse_json(content: str) -> Conf:
    """Parse JSON content into a Conf."""
    import json

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValidationError(
            message=f"json parse error: {exc}",
            code="knifer.conf.json_parse_failed",
            context={"error": str(exc)},
        ) from exc
    return _flatten_to_conf(data)


def _flatten_to_conf(data: Any, prefix: str = "") -> Conf:
    """Flatten nested dict into a Conf with dot-separated group keys."""
    conf = Conf()
    if isinstance(data, dict):
        for key, value in data.items():
            group = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                sub = _flatten_to_conf(value, group)
                conf.merge(sub)
            elif isinstance(value, list):
                conf.set_by_group(_DEFAULT_GROUP, group, ",".join(str(v) for v in value))
            elif value is not None:
                conf.set_by_group(
                    _DEFAULT_GROUP,
                    group,
                    str(value) if not isinstance(value, (bool, int, float)) else str(value),
                )
    return conf
