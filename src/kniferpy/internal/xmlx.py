from __future__ import annotations

import html
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree
from xml.sax.saxutils import escape as _sax_escape

from kniferpy.verr import DecodeError

# ========== Constants ==========

NBSP = "&nbsp;"
AMP = "&amp;"
QUOTE = "&quot;"
APOS = "&apos;"
LT = "&lt;"
GT = "&gt;"
CONTENT_KEY = "content"

_INVALID_RE = re.compile("[\x00-\x08\x0b-\x0c\x0e-\x1f]")
InvalidRegex = "[\x00-\x08\x0b-\x0c\x0e-\x1f]"
_COMMENT_RE = re.compile(r"<!--.+?-->", re.DOTALL)
CommentRegex = r"(?s)<!--.+?-->"
_DOCTYPE_RE = re.compile(r"<!(?:DOCTYPE|ENTITY)", re.IGNORECASE)
_INT_RE = re.compile(r"[+-]?\d+")
_FLOAT_RE = re.compile(r"[+-]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?")
_ESCAPE_ENTITIES = {'"': QUOTE, "'": APOS}

IndentDefault = 2
DefaultCharset = "UTF-8"

# ========== XMLError ==========


class XMLError(DecodeError):
    """XML-specific error with optional code and cause."""

    pass


# ========== Document / Element Tree ==========


@dataclass
class Element:
    name: str = ""
    attr: dict[str, str] = field(default_factory=dict)
    text: str = ""
    children: list[Element] = field(default_factory=list)
    parent: Element | None = None

    def __repr__(self) -> str:
        return (
            f"Element(name={self.name!r}, text={self.text[:40]!r}, children={len(self.children)})"
        )


@dataclass
class Document:
    root: Element | None = None


# ========== Namespace Cache ==========


@dataclass
class NamespaceCache:
    default: str = ""
    prefix: dict[str, str] = field(default_factory=dict)
    uri: dict[str, str] = field(default_factory=dict)


def new_namespace_cache(doc: Document) -> NamespaceCache:
    cache = NamespaceCache()
    _walk(get_root_element(doc), lambda e: _collect_namespaces(e, cache))
    return cache


def _collect_namespaces(ele: Element, cache: NamespaceCache) -> None:
    for k, v in ele.attr.items():
        if k == "xmlns":
            cache.default = v
            cache.prefix["DEFAULT"] = v
            cache.uri[v] = "DEFAULT"
        elif k.startswith("xmlns:"):
            prefix = k.split(":", 1)[1]
            cache.prefix[prefix] = v
            cache.uri[v] = prefix


def namespace_uri(cache: NamespaceCache, prefix: str) -> str:
    return cache.prefix.get(prefix, "")


def prefix_of(cache: NamespaceCache, uri: str) -> str:
    return cache.uri.get(uri, "")


# ========== Tree Construction ==========


def create_xml() -> Document:
    return Document()


def create_xml_with_root(root_element_name: str) -> Document:
    return Document(root=Element(name=root_element_name))


def create_xml_with_root_ns(root_element_name: str, namespace: str) -> Document:
    root = Element(name=root_element_name)
    if namespace:
        root.attr["xmlns"] = namespace
    return Document(root=root)


def get_root_element(doc: Document | None) -> Element | None:
    if doc is None:
        return None
    return doc.root


def get_owner_document(node: Element | None) -> Document | None:
    if node is None:
        return None
    while node.parent is not None:
        node = node.parent
    return Document(root=node)


# ========== Element Manipulation ==========


def append_child(node: Element | None, tag_name: str, namespace: str = "") -> Element | None:
    if node is None:
        return None
    child = Element(name=tag_name, parent=node)
    if namespace:
        child.attr["xmlns"] = namespace
    node.children.append(child)
    return child


def append_text(node: Element | None, text: Any) -> Element | None:
    if node is None:
        return None
    node.text += str(text)
    return node


def append(node: Element | None, data: Any) -> None:
    if node is None:
        return
    if isinstance(data, dict):
        _append_dict(node, data)
    elif isinstance(data, list):
        for item in data:
            append(node, item)
    elif isinstance(data, str):
        append_text(node, data)
    elif data is not None:
        append_text(node, str(data))


def _append_dict(node: Element, data: dict[str, Any]) -> None:
    for k, v in data.items():
        if k.startswith("@"):
            node.attr[k[1:]] = str(v)
        elif k == CONTENT_KEY:
            node.text += str(v)
        elif isinstance(v, dict):
            child = append_child(node, k)
            if child:
                _append_dict(child, v)
        elif isinstance(v, list):
            for item in v:
                child = append_child(node, k)
                if child:
                    append(child, item)
        else:
            child = append_child(node, k)
            if child:
                child.text = str(v) if v is not None else ""


# ========== Navigation ==========


def get_elements(element: Element | None, tag_name: str = "") -> list[Element]:
    if element is None:
        return []
    if tag_name == "":
        return list(element.children)
    return [c for c in element.children if c.name == tag_name]


def get_element(element: Element | None, tag_name: str) -> Element | None:
    if element is None:
        return None
    for child in element.children:
        if child.name == tag_name:
            return child
    return None


def element_text(element: Element | None, tag_name: str, default_value: str = "") -> str:
    if child := get_element(element, tag_name):
        return child.text.strip()
    return default_value


def trans_elements(nodes: list[Element | None]) -> list[Element]:
    return [n for n in nodes if n is not None]


def is_element(node: Element | None) -> bool:
    return node is not None


# ========== XPath ==========


def get_element_by_xpath(expression: str, source: Any) -> Element | None:
    root = _element_of(source)
    if root is None:
        return None
    results = _find_by_path(root, expression)
    return results[0] if results else None


def get_node_list_by_xpath(expression: str, source: Any) -> list[Element]:
    root = _element_of(source)
    if root is None:
        return []
    return _find_by_path(root, expression)


def get_node_by_xpath(expression: str, source: Any) -> Element | None:
    return get_element_by_xpath(expression, source)


def get_by_xpath(expression: str, source: Any, return_type: str = "node") -> Any:
    rt = return_type.lower()
    if rt in ("string", "text"):
        node = get_node_by_xpath(expression, source)
        return node.text.strip() if node else ""
    if rt in ("nodes", "nodelist", "list"):
        return get_node_list_by_xpath(expression, source)
    return get_node_by_xpath(expression, source)


def _element_of(source: Any) -> Element | None:
    if isinstance(source, Element):
        return source
    if isinstance(source, Document):
        return source.root
    if isinstance(source, str):
        doc = parse_xml(source)
        return doc.root
    return None


def _find_by_path(root: Element, expr: str) -> list[Element]:
    expr = expr.strip()
    if not expr:
        return []
    if expr.startswith("//"):
        name = expr[2:]
        result: list[Element] = []
        _walk(root, lambda e: result.append(e) if e.name == name else None)
        return result
    parts = [p for p in expr.strip("/").split("/") if p]
    if not parts:
        return []
    current = [root]
    # Skip root name if it matches
    if parts[0] == root.name:
        parts = parts[1:]
    for part in parts:
        if not part:
            continue
        nxt: list[Element] = []
        for ele in current:
            for child in ele.children:
                if child.name == part:
                    nxt.append(child)
        current = nxt
    return current


def _walk(element: Element | None, fn: Callable[[Element], None]) -> None:
    if element is None:
        return
    fn(element)
    for child in element.children:
        _walk(child, fn)


# ========== Parse (return Document) ==========


def parse_xml(xml_str: str) -> Document:
    if _DOCTYPE_RE.search(xml_str):
        raise DecodeError("vxml: DTD/DOCTYPE is not allowed", code="xml.doctype_forbidden")
    try:
        et_root = ElementTree.fromstring(xml_str)
    except ElementTree.ParseError as exc:
        raise DecodeError(f"vxml: parse error: {exc}", code="xml.invalid") from exc
    return Document(root=_et_to_element(et_root))


def read_xml(path_or_content: str) -> Document:
    try:
        from kniferpy.internal import filex

        content = filex.read_text(path_or_content)
        return parse_xml(content)
    except Exception:
        return parse_xml(path_or_content)


def read_xml_file(path: str) -> Document:
    from kniferpy.internal import filex

    return parse_xml(filex.read_text(path))


def read_xml_bytes(data: bytes) -> Document:
    return parse_xml(data.decode("utf-8"))


def _et_to_element(et_elem: Any) -> Element:
    name = _local(et_elem.tag)
    attr = {_local(k): v for k, v in et_elem.attrib.items()}
    text = et_elem.text.strip() if et_elem.text else ""
    ele = Element(name=name, attr=attr, text=text)
    for child in et_elem:
        child_ele = _et_to_element(child)
        child_ele.parent = ele
        ele.children.append(child_ele)
        if child.tail and child.tail.strip():
            ele.text += child.tail.strip()
    return ele


# ========== Element to Map / Bean ==========


def xml_node_to_map(node: Element | None) -> Any:
    if node is None:
        return {}
    result: dict[str, Any] = {}
    for k, v in node.attr.items():
        result[k] = _parse_scalar(v)
    for child in node.children:
        _add_map_value(result, child.name, xml_node_to_map(child))
    if node.text.strip():
        if not result:
            return _parse_scalar(node.text.strip())
        result[CONTENT_KEY] = _parse_scalar(node.text.strip())
    if not result and not node.children:
        return ""
    return result


def xml_node_to_bean(node: Element | None, dst: type) -> Any:
    m = xml_node_to_map(node)
    return _map_to_bean(m, dst)


def xml_to_map_into(xml_str: str, result: dict[str, Any] | None = None) -> dict[str, Any]:
    m = xml_node_to_map(parse_xml(xml_str).root)
    if not isinstance(m, dict):
        return {CONTENT_KEY: m}
    if result is not None:
        result.update(m)
        return result
    return m


def xml_node_to_map_into(
    node: Element | None, result: dict[str, Any] | None = None
) -> dict[str, Any]:
    m = xml_node_to_map(node)
    if not isinstance(m, dict):
        return {CONTENT_KEY: m}
    if result is not None:
        result.update(m)
        return result
    return m


# ========== Serialize (Marshal) ==========


def marshal_map(data: dict[str, Any], root_tag: str = "root", *, pretty: bool = False) -> str:
    return to_xml(data, root_tag, pretty=pretty)


def marshal_bean(bean: Any, root_tag: str = "root", *, pretty: bool = False) -> str:
    import dataclasses

    if dataclasses.is_dataclass(bean) and not isinstance(bean, type):
        d = dataclasses.asdict(bean)
        return marshal_map(d, root_tag, pretty=pretty)
    return marshal_map({"value": str(bean)}, root_tag, pretty=pretty)


def marshal_string(v: Any, *, pretty: bool = False) -> str:
    """Marshal any value to XML string (Go compat alias for marshal_bean)."""
    if isinstance(v, dict):
        return marshal_map(v, pretty=pretty)
    if isinstance(v, list):
        d = {"item": v}
        return marshal_map(d, "root", pretty=pretty)
    return marshal_bean(v, pretty=pretty)


def write_to(doc: Document, *, pretty: bool = False) -> str:
    if doc.root is None:
        return ""
    m = xml_node_to_map(doc.root)
    tag = doc.root.name
    return to_xml(m, tag, pretty=pretty)


def write_file(path: str, doc: Document, *, pretty: bool = True) -> None:
    from kniferpy.internal import filex

    content = write_to(doc, pretty=pretty)
    filex.write_text(path, content)


# ========== Core parse helpers (shared) ==========


def _parse(xml_str: str) -> Any:
    if _DOCTYPE_RE.search(xml_str):
        raise DecodeError("vxml: DTD/DOCTYPE is not allowed", code="xml.doctype_forbidden")
    try:
        return ElementTree.fromstring(xml_str)
    except ElementTree.ParseError as exc:
        raise DecodeError(f"vxml: parse error: {exc}", code="xml.invalid") from exc


def _local(tag: str) -> str:
    if tag.startswith("{"):
        return tag.rsplit("}", 1)[-1]
    return tag


def _direct_text(elem: Any) -> str:
    parts = [elem.text or ""]
    parts.extend(child.tail or "" for child in elem)
    return "".join(parts)


def _element_to_value(elem: Any) -> Any:
    obj: dict[str, Any] = {}
    for key, value in elem.attrib.items():
        obj[_local(key)] = _parse_scalar(value)
    for child in elem:
        _add_map_value(obj, _local(child.tag), _element_to_value(child))
    text = _direct_text(elem).strip()
    if not obj:
        return "" if text == "" else _parse_scalar(text)
    if text != "":
        obj[CONTENT_KEY] = _parse_scalar(text)
    return obj


def _add_map_value(mapping: dict[str, Any], key: str, value: Any) -> None:
    if key in mapping:
        existing = mapping[key]
        if isinstance(existing, list):
            existing.append(value)
        else:
            mapping[key] = [existing, value]
        return
    mapping[key] = value


def _parse_scalar(s: str) -> Any:
    s = s.strip()
    lowered = s.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "null":
        return None
    if _INT_RE.fullmatch(s):
        return int(s)
    if _FLOAT_RE.fullmatch(s):
        return float(s)
    return s


# ========== Escape / Unescape ==========


def escape(s: str) -> str:
    return _sax_escape(s, _ESCAPE_ENTITIES)


def unescape(s: str) -> str:
    return html.unescape(s)


# ========== Clean ==========


def clean_invalid(xml_content: str) -> str:
    return _INVALID_RE.sub("", xml_content)


def clean_comment(xml_content: str) -> str:
    return _COMMENT_RE.sub("", xml_content)


# ========== Validation ==========


def is_valid(xml_str: str) -> bool:
    try:
        _parse(xml_str)
    except DecodeError:
        return False
    return True


# ========== Map / Bean (public) ==========


def to_map(xml_str: str) -> dict[str, Any]:
    doc = parse_xml(xml_str)
    if doc.root is None:
        return {}
    result: dict[str, Any] = {}
    _add_map_value(result, doc.root.name, xml_node_to_map(doc.root))
    return result


def to_bean(xml_str: str, bean_class: type) -> Any:
    m = to_map(xml_str)
    return _map_to_bean(m, bean_class)


def _map_to_bean(d: dict[str, Any], bean_class: type) -> Any:
    hints = {}
    for cls in bean_class.__mro__:
        if hasattr(cls, "__annotations__"):
            hints.update(cls.__annotations__)
    kwargs: dict[str, Any] = {}
    for field_name in hints:
        if field_name in d:
            kwargs[field_name] = d[field_name]
    return bean_class(**kwargs)


# ========== XML Writing ==========


def to_xml(data: dict[str, Any], root_tag: str = "root", *, pretty: bool = False) -> str:
    if pretty:
        return _dict_to_xml_pretty(data, root_tag)
    return _dict_to_xml(data, root_tag)


def _dict_to_xml(data: dict[str, Any], tag: str) -> str:
    parts: list[str] = [f"<{tag}"]
    attrs = ""
    children = ""
    for k, v in data.items():
        if k.startswith("@"):
            attrs += f' {k[1:]}="{_xml_escape_attr(str(v))}"'
        else:
            children += _val_to_xml(k, v)
    parts.append(attrs)
    parts.append(">")
    parts.append(children)
    parts.append(f"</{tag}>")
    return "".join(parts)


def _dict_to_xml_pretty(data: dict[str, Any], tag: str, indent: int = 0) -> str:
    sp = "  " * indent
    parts: list[str] = [f"{sp}<{tag}"]
    attrs = ""
    children: list[str] = []
    for k, v in data.items():
        if k.startswith("@"):
            attrs += f' {k[1:]}="{_xml_escape_attr(str(v))}"'
        else:
            children.append(_val_to_xml_pretty(k, v, indent + 1))
    parts.append(attrs)
    if children:
        parts.append(">\n")
        parts.append("\n".join(children))
        parts.append(f"\n{sp}</{tag}>")
    else:
        parts.append(" />")
    return "".join(parts)


def _val_to_xml(tag: str, value: Any) -> str:
    if isinstance(value, dict):
        return _dict_to_xml(value, tag)
    if isinstance(value, list):
        return "".join(_val_to_xml(tag, item) for item in value)
    return f"<{tag}>{_xml_escape_text(str(value))}</{tag}>"


def _val_to_xml_pretty(tag: str, value: Any, indent: int) -> str:
    sp = "  " * indent
    if isinstance(value, dict):
        return _dict_to_xml_pretty(value, tag, indent)
    if isinstance(value, list):
        return "\n".join(_val_to_xml_pretty(tag, item, indent) for item in value)
    return f"{sp}<{tag}>{_xml_escape_text(str(value))}</{tag}>"


def _xml_escape_text(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _xml_escape_attr(s: str) -> str:
    return _xml_escape_text(s).replace('"', "&quot;")


# ========== Format ==========


def format_xml(xml_str: str) -> str:
    try:
        from xml.dom import minidom

        dom = minidom.parseString(xml_str)
        return dom.toprettyxml(indent="  ")
    except Exception:
        return xml_str


# ========== Simple path access (on dict) ==========


def get_by_path(xml_str: str, path: str) -> Any:
    m = to_map(xml_str)
    return _get_by_path_dict(m, path)


def _get_by_path_dict(d: Any, path: str) -> Any:
    current = d
    for part in path.split("."):
        if isinstance(current, dict):
            if part not in current:
                return None
            current = current[part]
        elif isinstance(current, list):
            if not part.isdigit():
                return None
            idx = int(part)
            if idx >= len(current):
                return None
            current = current[idx]
        else:
            return None
    return current


# ========== File I/O ==========


def read(path: str) -> dict[str, Any]:
    from kniferpy.internal import filex

    return to_map(filex.read_text(path))


def write(path: str, data: dict[str, Any], root_tag: str = "root", *, pretty: bool = True) -> None:
    from kniferpy.internal import filex

    filex.write_text(path, to_xml(data, root_tag, pretty=pretty))


# ========== SAX streaming parsing =============================================


def read_xml_reader(reader: Any) -> Document:
    """Parse XML from a reader/stream."""
    if hasattr(reader, "read"):
        content = reader.read()
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        return parse_xml(content)
    return parse_xml(str(reader))


def read_by_sax(
    xml_str: str,
    *,
    on_start_element: Callable[[str, dict[str, str]], None] | None = None,
    on_end_element: Callable[[str], None] | None = None,
    on_characters: Callable[[str], None] | None = None,
) -> None:
    """Parse XML with SAX-style callbacks."""
    if _DOCTYPE_RE.search(xml_str):
        raise DecodeError("vxml: DTD/DOCTYPE is not allowed", code="xml.doctype_forbidden")

    class _SAXHandler:
        def start(self, tag: str, attrib: dict[str, str]) -> None:
            nonlocal on_start_element
            if on_start_element:
                on_start_element(_local(tag), {_local(k): v for k, v in attrib.items()})

        def end(self, tag: str) -> None:
            nonlocal on_end_element
            if on_end_element:
                on_end_element(_local(tag))

        def data(self, text: str) -> None:
            nonlocal on_characters
            if on_characters and text.strip():
                on_characters(text)

    try:
        parser = ElementTree.XMLParser(target=ElementTree.TreeBuilder())
        parser.parser.StartElementHandler = _SAXHandler().start
        parser.parser.EndElementHandler = _SAXHandler().end
        parser.parser.CharacterDataHandler = _SAXHandler().data
        parser.feed(xml_str)
        parser.close()
    except ElementTree.ParseError as exc:
        raise DecodeError(f"vxml: parse error: {exc}", code="xml.invalid") from exc


def read_by_sax_file(
    path: str,
    *,
    on_start_element: Callable[[str, dict[str, str]], None] | None = None,
    on_end_element: Callable[[str], None] | None = None,
    on_characters: Callable[[str], None] | None = None,
) -> None:
    from kniferpy.internal import filex

    read_by_sax(
        filex.read_text(path),
        on_start_element=on_start_element,
        on_end_element=on_end_element,
        on_characters=on_characters,
    )


# ========== XML Transformation =================================================


def transform_with(
    src: Document,
    dest: Document,
    *,
    on_element: Callable[[Element], Element | None] | None = None,
) -> None:
    """Copy XML from source to result with optional transforms."""
    if src.root is None:
        return

    def _copy(src_elem: Element, parent: Element | None) -> None:
        transformed = on_element(src_elem) if on_element else src_elem
        if transformed is None:
            return
        clone = Element(
            name=transformed.name,
            attr=dict(transformed.attr),
            text=transformed.text,
            parent=parent,
        )
        if parent is not None:
            parent.children.append(clone)
        if dest.root is None:
            dest.root = clone
        for child in src_elem.children:
            _copy(child, clone)

    _copy(src.root, None)
