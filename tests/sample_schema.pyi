# This file is generated. Manual changes will be lost
# fmt: off
# ruff: noqa
from __future__ import annotations

import typing_extensions as typ


# Definitions
@typ.final
class DictDefinition(typ.TypedDict):
    nested_ref: ScenarioName
    number: int

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
    model: list[str]
    pickup_lua_callback: str
    pickup_actordef: str
    pickup_string_key: str

@typ.final
class Sample(typ.TypedDict, total=False):
    basic_dict: dict[ScenarioName, str]
    basic_array: list[SampleBasicArrayItem]
    complex_non_total_object: SampleComplexNonTotalObject
    basic_pattern_properties_dict: dict[str, ScenarioName]
    complex_dict: dict[ScenarioName | str, ScenarioName | str]
