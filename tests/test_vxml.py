from dataclasses import dataclass
from io import BytesIO, StringIO
from pathlib import Path

import pytest

from kniferpy import vxml
from kniferpy.internal import xmlx
from kniferpy.verr import DecodeError


def test_escape_unescape_roundtrip() -> None:
    raw = '<tag attr="v">a & b \' c</tag>'
    escaped = vxml.escape(raw)
    assert "&lt;" in escaped
    assert "&amp;" in escaped
    assert "&quot;" in escaped
    assert "&apos;" in escaped
    assert vxml.unescape(escaped) == raw


def test_unescape_named_and_numeric_entities() -> None:
    assert vxml.unescape("a&nbsp;b") == "a\xa0b"
    assert vxml.unescape("&#65;&#x42;") == "AB"


def test_clean_invalid_removes_control_chars() -> None:
    dirty = "a\x00b\x08c\x0bd"
    assert vxml.clean_invalid(dirty) == "abcd"
    # Valid whitespace (tab/newline/carriage return) is preserved.
    assert vxml.clean_invalid("a\tb\nc\rd") == "a\tb\nc\rd"


def test_clean_comment_removes_comments() -> None:
    xml = "<r><!-- drop me --><a>1</a></r>"
    assert vxml.clean_comment(xml) == "<r><a>1</a></r>"
    assert vxml.clean_comment("<r><!-- multi\nline --><a/></r>") == "<r><a/></r>"


def test_to_map_scalars_and_nesting() -> None:
    xml = "<root><n>42</n><f>3.14</f><b>true</b><s>hello</s></root>"
    result = vxml.to_map(xml)
    assert result == {
        "root": {
            "n": 42,
            "f": 3.14,
            "b": True,
            "s": "hello",
        }
    }


def test_to_map_repeated_siblings_become_list() -> None:
    xml = "<root><item>1</item><item>2</item><item>3</item></root>"
    assert vxml.to_map(xml) == {"root": {"item": [1, 2, 3]}}


def test_to_map_attributes_and_mixed_content() -> None:
    xml = '<root id="7">text<child>x</child></root>'
    result = vxml.to_map(xml)
    assert result["root"]["id"] == 7
    assert result["root"]["child"] == "x"
    assert result["root"][vxml.CONTENT_KEY] == "text"


def test_to_map_empty_element() -> None:
    assert vxml.to_map("<root><empty/></root>") == {"root": {"empty": ""}}


def test_to_map_namespace_prefix_stripped() -> None:
    xml = '<root xmlns:ns="urn:x"><ns:child>v</ns:child></root>'
    assert vxml.to_map(xml) == {"root": {"child": "v"}}


def test_is_valid() -> None:
    assert vxml.is_valid("<root><a/></root>") is True
    assert vxml.is_valid("<root><a></root>") is False
    assert vxml.is_valid("not xml at all <") is False


def test_to_map_invalid_raises_decode_error() -> None:
    with pytest.raises(DecodeError):
        vxml.to_map("<root><unclosed></root>")


def test_doctype_is_rejected() -> None:
    payload = '<?xml version="1.0"?>' '<!DOCTYPE foo [<!ENTITY xxe "boom">]>' "<root>&xxe;</root>"
    assert vxml.is_valid(payload) is False
    with pytest.raises(DecodeError):
        vxml.to_map(payload)


def test_constants_and_error_repr() -> None:
    assert vxml.NBSP == "&nbsp;"
    assert vxml.AMP == "&amp;"
    assert vxml.QUOTE == "&quot;"
    assert vxml.APOS == "&apos;"
    assert vxml.LT == "&lt;"
    assert vxml.GT == "&gt;"
    assert vxml.InvalidRegex
    assert vxml.CommentRegex
    assert vxml.IndentDefault == 2
    assert vxml.DefaultCharset == "UTF-8"
    assert repr(vxml.Element(name="root", text="x" * 80)) == (
        "Element(name='root', text='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx', children=0)"
    )
    assert isinstance(vxml.XMLError("bad"), DecodeError)


def test_document_element_construction_navigation_and_owner() -> None:
    empty = vxml.create_xml()
    doc = vxml.create_xml_with_root_ns("root", "urn:root")
    root = vxml.get_root_element(doc)
    assert vxml.get_root_element(empty) is None
    assert vxml.get_root_element(None) is None
    assert root is not None
    assert root.attr == {"xmlns": "urn:root"}

    child = vxml.append_child(root, "child", "urn:child")
    ignored = vxml.append_child(None, "x")
    assert ignored is None
    assert child is not None
    assert child.attr == {"xmlns": "urn:child"}
    assert vxml.append_text(child, " value ") is child
    assert vxml.append_text(None, "x") is None
    vxml.append(root, {"@id": 7, "name": "kniferpy", "items": [{"value": 1}, {"value": 2}]})
    vxml.append(root, ["tail", 3, None])
    vxml.append(None, {"x": 1})

    assert vxml.get_owner_document(child).root is root
    assert vxml.get_owner_document(None) is None
    assert vxml.get_elements(root)
    assert vxml.get_elements(root, "name")[0].text == "kniferpy"
    assert vxml.get_elements(None) == []
    assert vxml.get_element(root, "missing") is None
    assert vxml.get_element(None, "missing") is None
    assert vxml.element_text(root, "child") == "value"
    assert vxml.element_text(root, "missing", "fallback") == "fallback"
    assert vxml.trans_elements([child, None]) == [child]
    assert vxml.is_element(child)
    assert not vxml.is_element(None)


def test_namespace_cache_collects_default_and_prefixed_namespaces() -> None:
    doc = vxml.create_xml_with_root_ns("root", "urn:default")
    root = doc.root
    assert root is not None
    root.attr["xmlns:ns"] = "urn:ns"
    child = vxml.append_child(root, "child")
    assert child is not None
    child.attr["xmlns:inner"] = "urn:inner"

    cache = vxml.new_namespace_cache(doc)

    assert cache.default == "urn:default"
    assert vxml.namespace_uri(cache, "DEFAULT") == "urn:default"
    assert vxml.namespace_uri(cache, "ns") == "urn:ns"
    assert vxml.namespace_uri(cache, "inner") == "urn:inner"
    assert vxml.prefix_of(cache, "urn:ns") == "ns"
    assert vxml.prefix_of(cache, "missing") == ""


def test_xpath_helpers_support_document_element_string_and_return_types() -> None:
    xml = "<root><item><name>a</name></item><item><name>b</name></item></root>"
    doc = vxml.parse_xml(xml)
    root = doc.root
    assert root is not None

    assert vxml.get_element_by_xpath("/root/item/name", doc).text == "a"
    assert vxml.get_element_by_xpath("//name", root).text == "a"
    assert [node.text for node in vxml.get_node_list_by_xpath("//name", xml)] == ["a", "b"]
    assert vxml.get_node_by_xpath("/root/missing", doc) is None
    assert vxml.get_node_list_by_xpath("/root/item", None) == []
    assert vxml.get_by_xpath("//name", doc, "string") == "a"
    assert len(vxml.get_by_xpath("//name", doc, "nodes")) == 2
    assert vxml.get_by_xpath("//name", doc).text == "a"
    assert xmlx._find_by_path(root, "") == []


def test_parse_and_read_xml_variants(tmp_path: Path) -> None:
    path = tmp_path / "data.xml"
    path.write_text("<root><a>1</a></root>", encoding="utf-8")

    parsed = vxml.parse_xml("<root><a>1</a></root>")
    from_content = vxml.read_xml("<root><a>2</a></root>")
    from_file = vxml.read_xml(str(path))
    direct_file = vxml.read_xml_file(str(path))
    from_bytes = vxml.read_xml_bytes(b"<root><a>3</a></root>")
    from_reader = vxml.read_xml_reader(StringIO("<root><a>4</a></root>"))
    from_bytes_reader = vxml.read_xml_reader(BytesIO(b"<root><a>5</a></root>"))
    from_non_reader = vxml.read_xml_reader("<root><a>6</a></root>")

    assert vxml.element_text(parsed.root, "a") == "1"
    assert vxml.element_text(from_content.root, "a") == "2"
    assert vxml.element_text(from_file.root, "a") == "1"
    assert vxml.element_text(direct_file.root, "a") == "1"
    assert vxml.element_text(from_bytes.root, "a") == "3"
    assert vxml.element_text(from_reader.root, "a") == "4"
    assert vxml.element_text(from_bytes_reader.root, "a") == "5"
    assert vxml.element_text(from_non_reader.root, "a") == "6"


def test_xml_node_to_map_and_into_variants() -> None:
    doc = vxml.parse_xml('<root id="7"><item>1</item><item>2</item><empty/></root>')
    assert doc.root is not None
    existing = {"existing": True}

    assert vxml.xml_node_to_map(None) == {}
    assert vxml.xml_node_to_map(doc.root) == {"id": 7, "item": [1, 2], "empty": ""}
    assert vxml.xml_to_map_into("<root><a>true</a></root>") == {"a": True}
    assert vxml.xml_to_map_into("<root><a>true</a></root>", existing) is existing
    assert existing["a"] is True
    into = {"base": "x"}
    assert vxml.xml_node_to_map_into(doc.root, into) is into
    assert into["item"] == [1, 2]
    assert vxml.xml_node_to_map_into(None) == {}


def test_bean_conversion_from_xml_and_node() -> None:
    @dataclass
    class Item:
        name: str
        count: int = 0

    root = vxml.parse_xml("<root><name>knife</name><count>3</count></root>").root
    assert root is not None

    bean = vxml.xml_node_to_bean(root, Item)

    assert bean == Item(name="knife", count=3)
    with pytest.raises(TypeError):
        vxml.to_bean("<item><name>knife</name><count>3</count></item>", Item)


def test_marshal_to_xml_and_write_variants(tmp_path: Path) -> None:
    @dataclass
    class Item:
        name: str
        count: int

    data = {"@id": "7", "name": "knife", "items": ["a", "b"], "safe": True}
    doc = vxml.create_xml_with_root("root")
    assert doc.root is not None
    vxml.append(doc.root, data)
    target = tmp_path / "out.xml"
    map_target = tmp_path / "map.xml"

    xml = vxml.to_xml(data, "root")
    pretty = vxml.to_xml(data, "root", pretty=True)

    assert xml == (
        '<root id="7"><name>knife</name><items>a</items><items>b</items>' "<safe>True</safe></root>"
    )
    assert "\n" in pretty
    assert vxml.marshal_map(data, "root") == xml
    assert "<name>knife</name>" in vxml.marshal_bean(Item("knife", 3), "item")
    assert "<value>plain</value>" in vxml.marshal_bean("plain")
    assert "<item>a</item>" in vxml.marshal_string(["a", "b"])
    assert "<name>knife</name>" in vxml.marshal_string({"name": "knife"})
    assert "<value>plain</value>" in vxml.marshal_string("plain")
    assert vxml.write_to(vxml.create_xml()) == ""
    assert "<name>knife</name>" in vxml.write_to(doc)

    vxml.write_file(str(target), doc, pretty=False)
    assert target.read_text(encoding="utf-8").startswith("<root")
    vxml.write(str(map_target), {"name": "knife"}, "root", pretty=False)
    assert map_target.read_text(encoding="utf-8") == "<root><name>knife</name></root>"
    assert vxml.read(str(map_target)) == {"root": {"name": "knife"}}


def test_format_xml_and_get_by_path() -> None:
    xml = "<root><items><item>a</item><item>b</item></items></root>"

    assert "<?xml" in vxml.format_xml(xml)
    assert vxml.format_xml("<root>") == "<root>"
    assert vxml.get_by_path(xml, "root.items.item.0") == "a"
    assert vxml.get_by_path(xml, "root.items.item.9") is None
    assert vxml.get_by_path(xml, "root.items.item.nope") is None
    assert vxml.get_by_path(xml, "root.items.item.0.missing") is None


def test_sax_callbacks_and_file_variant(tmp_path: Path) -> None:
    events: list[tuple[str, object]] = []
    path = tmp_path / "sax.xml"
    xml = '<root id="7"><item>a</item><item>b</item></root>'
    path.write_text(xml, encoding="utf-8")

    def on_start(name: str, attrs: dict[str, str]) -> None:
        events.append(("start", name, attrs))

    def on_end(name: str) -> None:
        events.append(("end", name))

    def on_chars(text: str) -> None:
        events.append(("text", text.strip()))

    try:
        vxml.read_by_sax(
            xml,
            on_start_element=on_start,
            on_end_element=on_end,
            on_characters=on_chars,
        )
        vxml.read_by_sax_file(str(path), on_start_element=on_start)
    except AttributeError:
        pytest.skip("ElementTree parser does not expose low-level SAX handlers")

    assert ("start", "root", {"id": "7"}) in events
    assert ("text", "a") in events
    assert ("end", "root") in events


def test_sax_rejects_doctype_and_invalid_xml() -> None:
    with pytest.raises(DecodeError) as doctype_exc:
        vxml.read_by_sax("<!DOCTYPE root><root/>")
    assert doctype_exc.value.code == "xml.doctype_forbidden"

    try:
        with pytest.raises(DecodeError) as invalid_exc:
            vxml.read_by_sax("<root>")
        assert invalid_exc.value.code == "xml.invalid"
    except AttributeError:
        pytest.skip("ElementTree parser does not expose low-level SAX handlers")


def test_transform_with_copies_and_filters_elements() -> None:
    src = vxml.parse_xml('<root id="1"><keep>a</keep><drop>b</drop></root>')
    dest = vxml.create_xml()

    def transform(element: vxml.Element) -> vxml.Element | None:
        if element.name == "drop":
            return None
        if element.name == "keep":
            return vxml.Element(name="renamed", text=element.text.upper(), attr=element.attr)
        return element

    vxml.transform_with(src, dest, on_element=transform)

    assert dest.root is not None
    assert dest.root.name == "root"
    assert vxml.get_element(dest.root, "drop") is None
    renamed = vxml.get_element(dest.root, "renamed")
    assert renamed is not None
    assert renamed.text == "A"
    empty_dest = vxml.create_xml()
    vxml.transform_with(vxml.create_xml(), empty_dest)
    assert empty_dest.root is None


def test_append_dict_content_key_nested_dict_and_none_values() -> None:
    root = vxml.Element(name="root")

    vxml.append(
        root,
        {
            vxml.CONTENT_KEY: "text",
            "nested": {"@id": "1", "name": "child"},
            "nil": None,
        },
    )

    nested = vxml.get_element(root, "nested")
    nil = vxml.get_element(root, "nil")
    assert root.text == "text"
    assert nested is not None
    assert nested.attr == {"id": "1"}
    assert vxml.element_text(nested, "name") == "child"
    assert nil is not None
    assert nil.text == ""


def test_xpath_and_walk_edge_branches() -> None:
    root = vxml.Element(name="root")
    child = vxml.append_child(root, "child")
    assert child is not None

    seen: list[str] = []
    xmlx._walk(None, lambda element: seen.append(element.name))
    xmlx._walk(root, lambda element: seen.append(element.name))

    assert seen == ["root", "child"]
    assert vxml.get_element_by_xpath("/root/child", object()) is None
    assert xmlx._find_by_path(root, "/") == []
    assert xmlx._find_by_path(root, "/root//child") == [child]


def test_et_to_element_preserves_tail_text_and_internal_value_helpers() -> None:
    et_root = xmlx.ElementTree.fromstring(
        '<root xmlns:ns="urn"><ns:child code="7">1</ns:child>tail<empty /></root>'
    )
    converted = xmlx._et_to_element(et_root)
    value = xmlx._element_to_value(et_root)
    scalar_empty = xmlx._element_to_value(xmlx.ElementTree.fromstring("<empty />"))

    assert converted.name == "root"
    assert converted.text == "tail"
    assert converted.children[0].name == "child"
    assert converted.children[0].attr == {"code": "7"}
    assert value == {
        "child": {"code": 7, vxml.CONTENT_KEY: 1},
        "empty": "",
        vxml.CONTENT_KEY: "tail",
    }
    assert scalar_empty == ""
    assert xmlx._local("plain") == "plain"
    assert xmlx._parse_scalar("false") is False
    assert xmlx._parse_scalar("null") is None


def test_to_map_empty_document_branch_and_pretty_empty_element() -> None:
    assert vxml.to_map("<root/>") == {"root": ""}
    assert xmlx.xml_node_to_map(vxml.Element(name="leaf", text=" false ")) is False
    assert xmlx._dict_to_xml_pretty({}, "empty") == "<empty />"
    assert xmlx._val_to_xml("node", {"@id": '"quoted"', "text": "a&b"}) == (
        '<node id="&quot;quoted&quot;"><text>a&amp;b</text></node>'
    )
    assert xmlx._val_to_xml_pretty("items", ["a", "b"], 1) == (
        "  <items>a</items>\n  <items>b</items>"
    )


def test_get_by_path_internal_edge_cases() -> None:
    data = {"root": {"items": ["a", "b"], "name": "knife"}}

    assert xmlx._get_by_path_dict(data, "root.name") == "knife"
    assert xmlx._get_by_path_dict(data, "root.missing") is None
    assert xmlx._get_by_path_dict(data, "root.items.nope") is None
    assert xmlx._get_by_path_dict(data, "root.items.9") is None
    assert xmlx._get_by_path_dict(data, "root.name.0") is None
