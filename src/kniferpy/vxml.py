from __future__ import annotations

from typing import Any

from kniferpy.internal import xmlx
from kniferpy.internal.xmlx import (
    Document,
    Element,
    NamespaceCache,
    CONTENT_KEY,
    NBSP,
    AMP,
    QUOTE,
    APOS,
    LT,
    GT,
)

# Constants
CONTENT_KEY = CONTENT_KEY

# Escape / Unescape
escape = xmlx.escape
unescape = xmlx.unescape

# Clean
clean_invalid = xmlx.clean_invalid
clean_comment = xmlx.clean_comment

# Validation
is_valid = xmlx.is_valid

# Document / Element construction
create_xml = xmlx.create_xml
create_xml_with_root = xmlx.create_xml_with_root
create_xml_with_root_ns = xmlx.create_xml_with_root_ns
get_root_element = xmlx.get_root_element
get_owner_document = xmlx.get_owner_document

# Element manipulation
append_child = xmlx.append_child
append_text = xmlx.append_text
append = xmlx.append

# Navigation
get_elements = xmlx.get_elements
get_element = xmlx.get_element
element_text = xmlx.element_text
trans_elements = xmlx.trans_elements
is_element = xmlx.is_element

# XPath
get_element_by_xpath = xmlx.get_element_by_xpath
get_node_list_by_xpath = xmlx.get_node_list_by_xpath
get_node_by_xpath = xmlx.get_node_by_xpath
get_by_xpath = xmlx.get_by_xpath

# Namespace
new_namespace_cache = xmlx.new_namespace_cache
namespace_uri = xmlx.namespace_uri
prefix_of = xmlx.prefix_of

# Parse
parse_xml = xmlx.parse_xml
read_xml = xmlx.read_xml
read_xml_file = xmlx.read_xml_file
read_xml_bytes = xmlx.read_xml_bytes

# Node to map/bean
xml_node_to_map = xmlx.xml_node_to_map
xml_node_to_bean = xmlx.xml_node_to_bean
xml_to_map_into = xmlx.xml_to_map_into
xml_node_to_map_into = xmlx.xml_node_to_map_into

# Map / Bean
to_map = xmlx.to_map
to_bean = xmlx.to_bean

# Serialize
marshal_map = xmlx.marshal_map
marshal_bean = xmlx.marshal_bean
to_xml = xmlx.to_xml
write_to = xmlx.write_to
write_file = xmlx.write_file

# Format
format_xml = xmlx.format_xml

# Simple path access
get_by_path = xmlx.get_by_path

# File I/O
read = xmlx.read
write = xmlx.write

__all__ = [
    "Document",
    "Element",
    "NamespaceCache",
    "CONTENT_KEY",
    "NBSP",
    "AMP",
    "QUOTE",
    "APOS",
    "LT",
    "GT",
    "escape",
    "unescape",
    "clean_invalid",
    "clean_comment",
    "is_valid",
    "create_xml",
    "create_xml_with_root",
    "create_xml_with_root_ns",
    "get_root_element",
    "get_owner_document",
    "append_child",
    "append_text",
    "append",
    "get_elements",
    "get_element",
    "element_text",
    "trans_elements",
    "is_element",
    "get_element_by_xpath",
    "get_node_list_by_xpath",
    "get_node_by_xpath",
    "get_by_xpath",
    "new_namespace_cache",
    "namespace_uri",
    "prefix_of",
    "parse_xml",
    "read_xml",
    "read_xml_file",
    "read_xml_bytes",
    "xml_node_to_map",
    "xml_node_to_bean",
    "xml_to_map_into",
    "xml_node_to_map_into",
    "to_map",
    "to_bean",
    "marshal_map",
    "marshal_bean",
    "to_xml",
    "write_to",
    "write_file",
    "format_xml",
    "get_by_path",
    "read",
    "write",
]