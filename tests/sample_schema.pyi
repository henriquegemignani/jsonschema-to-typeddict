# This file is generated. Manual changes will be lost
# fmt: off
# ruff: noqa
# mypy: disable-error-code="misc"
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
    model: typ.Annotated[list[str], 'len() >= 1']
    pickup_lua_callback: str
    pickup_actordef: typ.Annotated[str, '/[a-zA-Z0-9_/]+?\\.bmsad/']
    pickup_string_key: str

class SampleMetadata(typ.TypedDict):
    """
    Title
    
    A description of the schema.
    
    Examples:
        `{'nested_ref': 's010_cave', 'number': 0, 'array': [1.0], 'dict': {'foo': True, 'bar': False}}`
        `{'nested_ref': 's020_magma', 'number': 1, 'array': [2, 3.4], 'dict': {'foo': True, 'bar': False}}`
    """

    string: typ.Annotated[str, 'len() <= 15']
    """
    Examples:
        `'s010_cave'`
    """

    number: typ.Annotated[int, '0 <= value < 100'] = 0
    array: typ.Annotated[list[float], 'len() >= 1', 'Unique items']
    dict: typ.Annotated[dict[str, bool], 'len() == 2']

@typ.final
class Sample(typ.TypedDict, total=False):
    basic_dict: dict[ScenarioName, str]
    basic_array: list[SampleBasicArrayItem]
    complex_non_total_object: SampleComplexNonTotalObject
    basic_pattern_properties_dict: dict[str, ScenarioName]
    complex_dict: dict[ScenarioName | str, ScenarioName | str]
    metadata: SampleMetadata = {'nested_ref': 's010_cave', 'number': 0, 'array': [1.0], 'dict': {'foo': True, 'bar': False}}
    """A description of the schema."""
