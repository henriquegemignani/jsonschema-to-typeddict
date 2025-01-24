# This file is generated. Manual changes will be lost
# fmt: off
# ruff: noqa
# mypy: disable-error-code="misc"
from __future__ import annotations

import typing_extensions as typ


# Definitions
@typ.final
class DictDefinition(typ.TypedDict):
    """
    Title
    
    A description of the schema.
    
    Examples: [{'nested_ref': 's010_cave', 'number': 0}, {'nested_ref': 's020_magma', 'number': 1}]
    """

    nested_ref: ScenarioName
    number: typ.Annotated[int, '0 <= value < 100'] = 0

ScenarioName = typ.Literal[
    's010_cave',
    's020_magma',
    's030_baselab',
    's040_aqua',
    's050_forest',
    's060_quarantine',
    's070_basesanc',
    's080_shipyard',
    's090_skybase'
]

UnionEnum = typ.Literal[
    'foo',
    2403,
    12.34,
    None
]


# Schema entries
class SampleBasicArrayItem(typ.TypedDict, total=False):
    something: float

SampleComplexNonTotalObjectPickupType = typ.Literal[
    'actor',
    'emmi',
    'corex',
    'corpius',
    'cutscene'
]

class SampleComplexNonTotalObject(typ.TypedDict, total=False):
    pickup_type: typ.Required[SampleComplexNonTotalObjectPickupType]
    model: typ.Annotated[list[str], 'len() >= 1']
    pickup_lua_callback: str
    pickup_actordef: typ.Annotated[str, '/[a-zA-Z0-9_/]+?\\.bmsad/']
    pickup_string_key: str

@typ.final
class Sample(typ.TypedDict, total=False):
    basic_dict: dict[ScenarioName, str]
    basic_array: list[SampleBasicArrayItem]
    complex_non_total_object: SampleComplexNonTotalObject
    basic_pattern_properties_dict: dict[str, ScenarioName]
    complex_dict: dict[ScenarioName | str, ScenarioName | str]
