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


ScenarioName: typ.TypeAlias = str


# Schema entries
class SampleFieldBItem(typ.TypedDict, total=False):
    something: float

class SampleFieldC(typ.TypedDict, total=False):
    pickup_type: typ.Required[str]
    model: list[str]
    pickup_lua_callback: str
    pickup_actordef: str
    pickup_string_key: str

@typ.final
class Sample(typ.TypedDict):
    field_a: dict[str, str]
    field_b: typ.NotRequired[list[SampleFieldBItem]]
    field_c: SampleFieldC

