# Copyright (c) 2026 CoReason Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_etl_cdc_wonder

from collections.abc import Iterable, Iterator
from typing import Any

from lxml import etree

from coreason_etl_cdc_wonder.utils.logger import logger


class ChunkStream:
    """
    AGENT INSTRUCTION: Helper class to wrap an iterable of bytes into a file-like object
    with a `read()` method, as expected by `lxml.etree.iterparse`.
    """

    def __init__(self, iterator: Iterable[bytes]) -> None:
        self.iterator = iter(iterator)
        self.buffer = b""

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            result = self.buffer + b"".join(self.iterator)
            self.buffer = b""
            return result

        while len(self.buffer) < size:
            try:
                chunk = next(self.iterator)
                self.buffer += chunk
            except StopIteration:
                break

        result = self.buffer[:size]
        self.buffer = self.buffer[size:]
        return result


def parse_wonder_xml_stream(stream: Iterable[bytes]) -> Iterator[dict[str, Any]]:
    """
    AGENT INSTRUCTION: Parses an XML stream from the CDC WONDER API using lxml.etree.iterparse.
    Extracts `<r>` elements from `<data-table>` and yields them wrapped in `{"raw_data": ...}`.
    It strictly clears elements from memory immediately after processing to prevent OOM errors.
    """
    logger.info("Starting memory-conscious XML stream parsing")

    file_like_stream = ChunkStream(stream)

    context = etree.iterparse(file_like_stream, events=("end",), tag="r", recover=True)

    for _event, elem in context:
        row_dict = _element_to_dict(elem)
        yield {"raw_data": row_dict}

        # Free memory by clearing the element and preceding siblings
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
        result[f"@{k}"] = v

    text = elem.text.strip() if elem.text else ""
    if text:
        result["#text"] = text

    for child in elem:
        child_dict = _element_to_dict(child)
        if child.tag not in result:
            result[child.tag] = child_dict
        else:
            if not isinstance(result[child.tag], list):
                result[child.tag] = [result[child.tag]]
            result[child.tag].append(child_dict)

    return result
