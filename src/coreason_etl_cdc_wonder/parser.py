# Copyright (c) 2026 CoReason Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_etl_cdc_wonder

from collections.abc import Iterator
from typing import IO, Any

from lxml import etree

from coreason_etl_cdc_wonder.utils.logger import logger


def parse_wonder_xml_stream(stream: IO[bytes]) -> Iterator[dict[str, Any]]:
    """
    AGENT INSTRUCTION: Parses an XML stream from the CDC WONDER API using lxml.etree.iterparse.
    Extracts `<r>` elements from `<data-table>` and yields them wrapped in `{"raw_data": ...}`.
    It strictly clears elements from memory immediately after processing to prevent OOM errors.
    """
    logger.info("Starting memory-conscious XML stream parsing")

    context = etree.iterparse(stream, events=("end",), tag="r", recover=True)

    for _event, elem in context:
        row_dict = _element_to_dict(elem)
        yield {"raw_data": row_dict}

        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]


def _element_to_dict(elem: etree._Element) -> dict[str, Any]:
    """
    AGENT INSTRUCTION: Recursively converts an lxml Element into a JSON-serializable dictionary.
    Handles attributes by prefixing them with `@`.
    """
    result: dict[str, Any] = {}

    for k, v in elem.attrib.items():
        k_str = k if isinstance(k, str) else str(k, encoding="utf-8")
        result[f"@{k_str}"] = v

    text = elem.text.strip() if elem.text else ""
    if text:
        result["#text"] = text

    for child in elem:
        child_dict = _element_to_dict(child)
        tag = child.tag if isinstance(child.tag, str) else str(child.tag, encoding="utf-8")
        if tag not in result:
            result[tag] = child_dict
        else:
            if not isinstance(result[tag], list):
                result[tag] = [result[tag]]
            result[tag].append(child_dict)

    return result
