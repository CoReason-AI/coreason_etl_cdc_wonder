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

from coreason_etl_cdc_wonder.config import CDCWonderRequestConfig


def generate_wonder_xml_payload(config: CDCWonderRequestConfig) -> str:
    """
    AGENT INSTRUCTION: Generates the XML payload required by the CDC WONDER API.
    It MUST explicitly include the accept_datause_restrictions parameter.
    """
    root = ET.Element("request-parameters")

    if config.accept_datause_restrictions:
        param = ET.SubElement(root, "parameter")
        name = ET.SubElement(param, "name")
        name.text = "accept_datause_restrictions"
        value = ET.SubElement(param, "value")
        value.text = "true"

    params_dict = config.parameters.model_dump(by_alias=True, exclude={"custom_parameters"})
    for k, v in sorted(params_dict.items()):
        if v is not None:
            param = ET.SubElement(root, "parameter")
            name = ET.SubElement(param, "name")
            name.text = k
            value = ET.SubElement(param, "value")
            value.text = str(v)

    for k, v in sorted(config.parameters.custom_parameters.items()):
        if v is not None:
            param = ET.SubElement(root, "parameter")
            name = ET.SubElement(param, "name")
            name.text = k
            value = ET.SubElement(param, "value")
            value.text = str(v)

    xml_bytes = ET.tostring(root, encoding="utf-8", method="xml", xml_declaration=True)
    return str(xml_bytes.decode("utf-8"))
