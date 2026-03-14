# Copyright (c) 2026 CoReason Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_etl_cdc_wonder

from pydantic import HttpUrl

from coreason_etl_cdc_wonder.domain.config import EpistemicRequestParameterContract, EpistemicWonderEndpointPolicy


def test_endpoint_policy_defaults() -> None:
    policy = EpistemicWonderEndpointPolicy()
    assert str(policy.base_url) == "https://wonder.cdc.gov/controller/datarequest/"
    assert policy.dataset_code == "D76"
    assert policy.full_url == "https://wonder.cdc.gov/controller/datarequest/D76"


def test_endpoint_policy_custom_values() -> None:
    policy = EpistemicWonderEndpointPolicy(base_url=HttpUrl("https://example.com/api/"), dataset_code="D77")
    assert str(policy.base_url) == "https://example.com/api/"
    assert policy.dataset_code == "D77"
    assert policy.full_url == "https://example.com/api/D77"


def test_request_parameter_contract_defaults() -> None:
    contract = EpistemicRequestParameterContract()
    assert contract.accept_datause_restrictions is True
    assert contract.default_parameters == {}

    xml_dict = contract.to_xml_dict()
    assert xml_dict["accept_datause_restrictions"] == "true"
    assert len(xml_dict) == 1


def test_request_parameter_contract_custom_values() -> None:
    contract = EpistemicRequestParameterContract(
        accept_datause_restrictions=False, default_parameters={"B_1": "D76.V1"}
    )
    assert contract.accept_datause_restrictions is False
    assert contract.default_parameters == {"B_1": "D76.V1"}

    xml_dict = contract.to_xml_dict()
    assert xml_dict["accept_datause_restrictions"] == "false"
    assert xml_dict["B_1"] == "D76.V1"
    assert len(xml_dict) == 2
