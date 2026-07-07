# Copyright (c) 2026 CoReason Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_etl_cdc_wonder

import io

from lxml import etree

from coreason_etl_cdc_wonder.parser import _element_to_dict, parse_wonder_xml_stream


def test_element_to_dict() -> None:
    """Test recursively converting lxml Element into dict."""
    xml_str = '<r a="1" b="2"><c v="A">foo</c><c v="B"/></r>'
    root = etree.fromstring(xml_str)

    result = _element_to_dict(root)
    assert result == {"@a": "1", "@b": "2", "c": [{"@v": "A", "#text": "foo"}, {"@v": "B"}]}


def test_streaming_parser() -> None:
    """Test parse_wonder_xml_stream correctly parses and wraps `<r>` tags in JSON."""
    xml_data = b"""<?xml version="1.0"?>
    <page>
    <data-table>
    <r><c v="2010"/><c v="C34.9"/><c v="120"/></r>
    <r><c v="2011"/><c v="C34.9"/><c v="130"/></r>
    </data-table>
    </page>"""

    stream = io.BytesIO(xml_data)
    records = list(parse_wonder_xml_stream(stream))

    assert len(records) == 2
    assert records[0] == {"raw_data": {"c": [{"@v": "2010"}, {"@v": "C34.9"}, {"@v": "120"}]}}
    assert records[1] == {"raw_data": {"c": [{"@v": "2011"}, {"@v": "C34.9"}, {"@v": "130"}]}}
