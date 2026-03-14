# Copyright (c) 2026 CoReason Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_etl_cdc_wonder


from pydantic import BaseModel, Field, HttpUrl


class EpistemicWonderEndpointPolicy(BaseModel):
    """
    Defines the contract for the CDC WONDER API endpoint URL.
    """

    base_url: HttpUrl = Field(
        default=HttpUrl("https://wonder.cdc.gov/controller/datarequest/"),
        description="The base URL for the CDC WONDER API.",
    )
    dataset_code: str = Field(
        default="D76", description="The dataset code for the CDC WONDER API. Defaults to D76 for 1999-2020 Mortality."
    )

    @property
    def full_url(self) -> str:
        """
        Computes the full endpoint URL by appending the dataset code to the base URL.
        """
        return f"{self.base_url}{self.dataset_code}"


class EpistemicRequestParameterContract(BaseModel):
    """
    Defines the contract for the CDC WONDER API XML payload parameters.
    """

    accept_datause_restrictions: bool = Field(
        default=True,
        description=(
            "AGENT INSTRUCTION: This field MUST be set to True. "
            "Failure to include this returns HTML error pages instead of XML."
        ),
    )

    default_parameters: dict[str, str] = Field(
        default_factory=dict, description="Additional default XML parameters for the payload."
    )

    def to_xml_dict(self) -> dict[str, str]:
        """
        Converts the parameters to a dictionary format suitable for XML payload generation.
        """
        params = self.default_parameters.copy()
        params["accept_datause_restrictions"] = "true" if self.accept_datause_restrictions else "false"
        return params
