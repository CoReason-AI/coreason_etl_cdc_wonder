# Copyright (c) 2026 CoReason Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_etl_cdc_wonder

import xml.etree.ElementTree as ET

from coreason_etl_cdc_wonder.config import CDCWonderParametersConfig, CDCWonderRequestConfig
from coreason_etl_cdc_wonder.payload import generate_wonder_xml_payload


def test_generate_wonder_xml_payload_default() -> None:
    """Test generating XML payload with default config includes datause restrictions."""
    config = CDCWonderRequestConfig()
    xml_str = generate_wonder_xml_payload(config)

    # Verify it parses correctly as XML
    root = ET.fromstring(xml_str)  # noqa: S314
    assert root.tag == "request-parameters"

    # Check that accept_datause_restrictions exists and is true
    found_datause = False
    for param in root.findall("parameter"):
        name_elem = param.find("name")
        value_elem = param.find("value")
        if name_elem is not None and value_elem is not None and name_elem.text == "accept_datause_restrictions":
            assert value_elem.text == "true"
            found_datause = True

    assert found_datause, "The accept_datause_restrictions parameter MUST be in the payload."


def test_generate_wonder_xml_payload_without_datause() -> None:
    """Test generating XML payload when accept_datause_restrictions is False (edge case)."""
    config = CDCWonderRequestConfig(accept_datause_restrictions=False)
    xml_str = generate_wonder_xml_payload(config)

    root = ET.fromstring(xml_str)  # noqa: S314

    for param in root.findall("parameter"):
        name_elem = param.find("name")
        if name_elem is not None:
            assert name_elem.text != "accept_datause_restrictions", "Should not be present if set to False"


def test_generate_wonder_xml_payload_custom_params() -> None:
    """Test generating XML payload with custom parameters ensuring correct structure and alias usage."""
    custom_params = {"I_21": "D76.V21", "O_1": "1"}
    params_config = CDCWonderParametersConfig(
        B_1="D76.V2",  # Override default
        custom_parameters=custom_params,
    )
    config = CDCWonderRequestConfig(parameters=params_config)
    xml_str = generate_wonder_xml_payload(config)

    root = ET.fromstring(xml_str)  # noqa: S314

    # Map parsed XML parameters to a dictionary for easier assertion
    parsed_params = {}
    for param in root.findall("parameter"):
        name_elem = param.find("name")
        value_elem = param.find("value")
        if name_elem is not None and value_elem is not None and name_elem.text and value_elem.text:
            parsed_params[name_elem.text] = value_elem.text

    assert parsed_params["accept_datause_restrictions"] == "true"
    assert parsed_params["B_1"] == "D76.V2"
    assert parsed_params["B_2"] == "D76.V2"
    assert parsed_params["I_21"] == "D76.V21"
    assert parsed_params["O_1"] == "1"


def test_generate_wonder_xml_payload_deterministic_ordering() -> None:
    """Test generating XML payload ensures parameters are deterministically sorted."""
    config = CDCWonderRequestConfig(parameters=CDCWonderParametersConfig(custom_parameters={"Z": "1", "A": "2"}))
    xml_str = generate_wonder_xml_payload(config)
    root = ET.fromstring(xml_str)  # noqa: S314

    # Get all names in order
    names = [
        name_elem.text
        for param in root.findall("parameter")
        if (name_elem := param.find("name")) is not None and name_elem.text is not None
    ]

    # 'accept_datause_restrictions' is appended first in the function
    assert names[0] == "accept_datause_restrictions"

    # The rest should be sorted by dictionary items
    # Check that Z comes after A
    idx_a = names.index("A")
    idx_z = names.index("Z")
    assert idx_a < idx_z
