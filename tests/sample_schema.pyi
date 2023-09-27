# This file is generated. Manual changes will be lost
# fmt: off
# ruff: noqa
from __future__ import annotations

import typing


class DefDictDefinition(typing.TypedDict):
    nested_ref: typing.NotRequired[def_scenario_name]
    number: typing.NotRequired[int]


def_dict_definition = DefDictDefinition
def_scenario_name = str


# The root object

class SampleFieldA(typing.TypedDict, total=False):
    pass


class SampleFieldBItem(typing.TypedDict, total=False):
    something: typing.NotRequired[float]


class SampleFieldC(typing.TypedDict, total=False):
    pickup_type: typing.Required[str]
    model: typing.NotRequired[list[str]]
    pickup_lua_callback: typing.NotRequired[str]
    pickup_actordef: typing.NotRequired[str]
    pickup_string_key: typing.NotRequired[str]


class Sample(typing.TypedDict):
    field_a: typing.Required[SampleFieldA]
    field_b: typing.NotRequired[list[SampleFieldBItem]]
    field_c: typing.Required[SampleFieldC]


Sample = Sample
