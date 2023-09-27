import json
import typing
from pathlib import Path


class CodeResult(typing.NamedTuple):
    block: str
    inline: str


def _snake_case_to_pascal_case(snake: str) -> str:
    return snake.replace("_", " ").title().replace(" ", "")


def _convert_any_of(entry_name: str, entry_value: dict) -> CodeResult:
    """Handle entries that have an anyOf key"""
    block_result = ""
    nested_inlines = []

    for i, alternative in enumerate(entry_value["anyOf"]):
        inner = _convert_schema_entry(f"{entry_name}__any{i}", alternative)
        if inner.block:
            block_result += f"{inner.block}\n"
        nested_inlines.append(inner.inline)

    return CodeResult(block_result, " | ".join(nested_inlines))


def _convert_array_entry(entry_name: str, entry_value: dict) -> CodeResult:
    """Handles that are type = array"""
    inner = _convert_schema_entry(f"{entry_name}__item", entry_value["items"])
    return CodeResult(inner.block, f"list[{inner.inline}]")


def _merge_conditional_into(entry_value: dict, alternative: dict) -> None:
    for prop_name, prop_value in alternative.get("properties", {}).items():
        if prop_name not in entry_value:
            if "properties" not in entry_value:
                entry_value["properties"] = {}
            entry_value["properties"][prop_name] = prop_value


def _merge_conditionals_into_main(entry_value: dict) -> None:
    for alternative in entry_value.pop("oneOf", []) + [entry_value.pop("then", None), entry_value.pop("else", None)]:
        if alternative is not None:
            _merge_conditionals_into_main(alternative)
            _merge_conditional_into(entry_value, alternative)


def _convert_object_entry(entry_name: str, entry_value: dict) -> CodeResult:
    """Handles that are type = object"""
    block_result = ""

    _merge_conditionals_into_main(entry_value)

    type_name = _snake_case_to_pascal_case(entry_name)
    if entry_value.get("additionalProperties", True):
        typed_dict = [f"class {type_name}(typing.TypedDict, total=False):"]
    else:
        typed_dict = [f"class {type_name}(typing.TypedDict):"]

    required_fields = entry_value.get("required", [])

    for prop_name, prop_value in entry_value.get("properties", {}).items():
        if prop_name == "$schema":
            # ignore the schema field, as it's invalid syntax and not interesting
            continue

        inner = _convert_schema_entry(f"{entry_name}__{prop_name}", prop_value)
        if inner.block:
            block_result += f"{inner.block}\n"

        if prop_name in required_fields:
            prop_inline = f"typing.Required[{inner.inline}]"
        else:
            prop_inline = f"typing.NotRequired[{inner.inline}]"

        typed_dict.append(f"    {prop_name}: {prop_inline}")

    if len(typed_dict) == 1:
        typed_dict.append("    pass")

    merged_dict = "\n".join(typed_dict)
    block_result += f"\n{merged_dict}\n"
    return CodeResult(block_result, type_name)


def _convert_schema_entry(entry_name: str, entry_value: dict) -> CodeResult:
    if "$ref" in entry_value:
        return CodeResult("", entry_value["$ref"].replace("#/$defs/", "def_"))

    if "anyOf" in entry_value:
        return _convert_any_of(entry_name, entry_value)

    entry_type = entry_value.get("type")
    match entry_type:
        case "string":
            inline_result = "str"

        case "integer":
            inline_result = "int"

        case "number":
            inline_result = "float"

        case "boolean":
            inline_result = "bool"

        case "null":
            inline_result = "None"

        case "array":
            return _convert_array_entry(entry_name, entry_value)

        case "object":
            return _convert_object_entry(entry_name, entry_value)

        case _:
            msg = f"Invalid entry at {entry_name}: unknown type {entry_type}"
            raise ValueError(msg)

    return CodeResult("", inline_result)


def convert_schema_to(schema_path: Path, output: Path, root_name: str) -> None:
    with schema_path.open() as f:
        schema = json.load(f)

    result = """# This file is generated. Manual changes will be lost
from __future__ import annotations

import typing
"""

    for def_name, def_value in schema["$defs"].items():
        inner = _convert_schema_entry(f"def_{def_name}", def_value)

        if inner.block:
            result += f"\n{inner.block}\n\n"

        result += f"def_{def_name} = {inner.inline}\n"

    result += "\n\n# The root object\n"

    root = _convert_schema_entry(root_name, schema)
    if root.block:
        result += f"{root.block}\n\n"

    result += f"{root_name} = {root.inline}\n"

    output.write_text(result)
