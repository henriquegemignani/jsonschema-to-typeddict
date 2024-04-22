import json
import typing
from pathlib import Path


class CodeResult(typing.NamedTuple):
    block: str
    inline: str


def _snake_case_to_pascal_case(snake: str) -> str:
    return snake.replace("_", " ").title().replace(" ", "")


def _convert_union(entry_name: str, alternatives: list) -> CodeResult:
    block_result = ""
    nested_inlines = []
    
    single = len(alternatives) == 1
    for i, alternative in enumerate(alternatives):
        inner_name = entry_name if single else f"{entry_name}__any{i}"
        inner = _convert_schema_entry(inner_name, alternative)
        if inner.block:
            block_result += f"{inner.block}\n"
        nested_inlines.append(inner.inline)

    return CodeResult(block_result, " | ".join(nested_inlines))


def _convert_any_of(entry_name: str, entry_value: dict) -> CodeResult:
    """Handle entries that have an anyOf key"""
    return _convert_union(entry_name, entry_value["anyOf"])


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


def _convert_true_dict(entry_name: str, entry_value: dict) -> CodeResult:
    """Handles objects with no properties, and patternProperties or additionalProperties as schemas"""
    additionalProperties = entry_value.get("additionalProperties", True)
    patternProperties = entry_value.get("patternProperties", {})
    propertyNames = entry_value.get("propertyNames", {})

    key_types = []
    if propertyNames:
        key_types.append(propertyNames)
    if patternProperties or not key_types:
        key_types.append({"type": "string"})
    
    val_types = [alternative for _, alternative in patternProperties]
    if additionalProperties and isinstance(additionalProperties, dict):
        val_types.append(additionalProperties)
    
    key = _convert_union(f"{entry_name}__key", key_types)
    val = _convert_union(f"{entry_name}", val_types)

    block = f"{key.block}{val.block}"
    inline = f"dict[{key.inline}, {val.inline}]"
    return CodeResult(block, inline)


def _convert_object_entry(entry_name: str, entry_value: dict) -> CodeResult:
    """Handles that are type = object"""
    block_result = ""

    _merge_conditionals_into_main(entry_value)

    properties = entry_value.get("properties", {})
    additionalProperties = entry_value.get("additionalProperties", True)
    patternProperties = entry_value.get("patternProperties", {})

    if not properties and (patternProperties or isinstance(additionalProperties, dict)):
        return _convert_true_dict(entry_name, entry_value)

    typed_dict = []
    if not additionalProperties:
        typed_dict.append("@typ.final")

    required_fields = entry_value.get("required", [])
    properties.pop("$schema", None) # ignore the schema field, as it's invalid syntax and not interesting

    type_name = _snake_case_to_pascal_case(entry_name)
    is_total = len(required_fields) > len(properties) - len(required_fields)

    if is_total:
        typed_dict.append(f"class {type_name}(typ.TypedDict):")
    else:
        typed_dict.append(f"class {type_name}(typ.TypedDict, total=False):")

    for prop_name, prop_value in properties.items():
        inner = _convert_schema_entry(f"{entry_name}__{prop_name}", prop_value)
        if inner.block:
            block_result += f"{inner.block}\n"
        
        if (prop_name in required_fields) == is_total:
            prop_inline = inner.inline
        elif prop_name in required_fields:
            prop_inline = f"typ.Required[{inner.inline}]"
        else:
            prop_inline = f"typ.NotRequired[{inner.inline}]"

        typed_dict.append(f"    {prop_name}: {prop_inline}")

    if len(typed_dict) == 1:
        typed_dict.append("    pass")

    merged_dict = "\n".join(typed_dict)
    block_result += f"{merged_dict}\n"
    return CodeResult(block_result, type_name)


def _convert_schema_entry(entry_name: str, entry_value: dict) -> CodeResult:
    if "$ref" in entry_value:
        if "#/$defs/" not in entry_value["$ref"]:
            msg = f"Invalid entry at {entry_name}: only $defs are supported in $ref ({entry_value})"
            raise ValueError(msg)
        return CodeResult("", _snake_case_to_pascal_case(entry_value["$ref"][8:]))

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
# fmt: off
# ruff: noqa
from __future__ import annotations

import typing_extensions as typ


"""
    defs = schema.get("$defs", {})

    if defs:
        result += "# Definitions\n"
    
    for def_name, def_value in defs.items():
        inner = _convert_schema_entry(def_name, def_value)

        if inner.block:
            result += f"\n{inner.block}\n\n"

        def_pascal = _snake_case_to_pascal_case(def_name)
        if def_pascal != inner.inline:
            result += f"{def_pascal}: typ.TypeAlias = {inner.inline}\n"

    result += "\n\n# Schema entries\n"

    root = _convert_schema_entry(root_name, schema)
    if root.block:
        result += f"{root.block}\n"

    if root_name != root.inline:
        result += f"{root_name}: typ.TypeAlias = {root.inline}\n"

    output.write_text(result)
