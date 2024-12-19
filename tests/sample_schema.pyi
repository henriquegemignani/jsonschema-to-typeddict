# This file is generated. Manual changes will be lost
# fmt: off
# ruff: noqa
from __future__ import annotations

import typing_extensions as typ


# Definitions
@typ.final
class DictDefinition(typ.TypedDict, total=False):
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
class SampleFieldBItem(typ.TypedDict, total=False):
    something: float

SampleFieldCPickupType = typ.Literal[
    'actor',
    'emmi',
    'corex',
    'corpius',
    'cutscene'
]

class SampleFieldC(typ.TypedDict, total=False):
    pickup_type: typ.Required[SampleFieldCPickupType]
    model: list[str]
    pickup_lua_callback: str
    pickup_actordef: str
    pickup_string_key: str

@typ.final
class Sample(typ.TypedDict):
    field_a: dict[ScenarioName, str]
    field_b: typ.NotRequired[list[SampleFieldBItem]]
    field_c: SampleFieldC
