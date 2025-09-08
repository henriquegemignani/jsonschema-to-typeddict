import copy
import json
import keyword
import typing
from pathlib import Path

NoDefault = object()


class CodeResult(typing.NamedTuple):
    block: str
    inline: str
    inline_docstring: list[str]
    default_value: typing.Any


def _get_docstring(entry_value: dict) -> list[str]:
    """Creates a docstring for the entry based on the schema metadata"""
    docstring: list[str] = []

    def _docstring_newline() -> None:
        if docstring:
            docstring.append("")

    if "title" in entry_value:
        _docstring_newline()
        docstring.append(entry_value["title"])

    if "description" in entry_value:
        _docstring_newline()
        docstring.append(entry_value["description"])

    examples = []
    if "examples" in entry_value:
        examples.extend(entry_value["examples"])
    if examples:
        if "default" in entry_value:
            examples.insert(0, entry_value["default"])
        _docstring_newline()
        docstring.append("Examples:")
        docstring.extend(f"    `{repr(example)}`" for example in examples)

    return docstring


def _get_default(entry_value: dict) -> typing.Any:
    """Safely returns the default value for the schema"""
    return entry_value.get("default", NoDefault)


def _snake_case_to_pascal_case(snake: str) -> str:
    return snake.replace("_", " ").title().replace(" ", "")


def _convert_union(entry_name: str, alternatives: list, defs: dict) -> CodeResult:
    """Convert a union to a CodeResult"""
    block_result = ""
    nested_inlines = []

    single = len(alternatives) == 1
    for i, alternative in enumerate(alternatives):
        inner_name = entry_name if single else f"{entry_name}__any{i}"
        inner = _convert_schema_entry(inner_name, alternative, defs)
        if inner.block:
            block_result += f"{inner.block}\n"
        nested_inlines.append(inner.inline)

    return CodeResult(block_result, " | ".join(nested_inlines), [], None)


def _range_metadata(
    minimum: int | None, maximum: int | None, value_name: str, exclusive_min: bool = False, exclusive_max: bool = False
) -> list:
    """Get an annotation for the given range, if applicable"""
    annotations = []

    max_compare = "<" if exclusive_max else "<="

    if minimum is not None and maximum is not None:
        if minimum == maximum:
            annotations.append(f"{value_name} == {minimum}")
        else:
            min_compare = "<" if exclusive_min else "<="
            annotations.append(f"{minimum} {min_compare} {value_name} {max_compare} {maximum}")
    elif minimum is not None:
        min_compare = ">" if exclusive_min else ">="
        annotations.append(f"{value_name} {min_compare} {minimum}")
    elif maximum is not None:
        annotations.append(f"{value_name} {max_compare} {maximum}")

    return annotations


def _convert_any_of(entry_name: str, entry_value: dict, defs: dict) -> CodeResult:
    """Handle entries that have an anyOf key"""
    return _convert_union(entry_name, entry_value["anyOf"], defs)


def _convert_array_entry(entry_name: str, entry_value: dict, defs: dict) -> CodeResult:
    """Handles that are type = array"""
    inner = _convert_schema_entry(f"{entry_name}__item", entry_value["items"], defs)
    inline = f"list[{inner.inline}]"

    annotations = []

    annotations.extend(
        _range_metadata(
            entry_value.get("minItems"),
            entry_value.get("maxItems"),
            "len()",
        )
    )

    unique = entry_value.get("uniqueItems")
    if unique:
        annotations.append("Unique items")

    if annotations:
        inline = f"typ.Annotated[{inline}, {repr(annotations)[1:-1]}]"

    return CodeResult(
        inner.block,
        inline,
        _get_docstring(entry_value),
        _get_default(entry_value),
    )


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


def _convert_true_dict(entry_name: str, entry_value: dict, defs: dict) -> CodeResult:
    """Handles objects with no properties, and patternProperties or additionalProperties as schemas"""
    additionalProperties = entry_value.get("additionalProperties", True)
    patternProperties = entry_value.get("patternProperties", {})
    propertyNames = entry_value.get("propertyNames", {})

    key_types = []
    if propertyNames:
        key_types.append(propertyNames)
    if patternProperties or not key_types:
        key_types.append({"type": "string"})

    val_types = [alternative for _, alternative in patternProperties.items()]
    if additionalProperties and isinstance(additionalProperties, dict):
        val_types.append(additionalProperties)

    key = _convert_union(f"{entry_name}__key", key_types, defs)
    val = _convert_union(f"{entry_name}", val_types, defs)

    block = f"{key.block}{val.block}"
    inline = f"dict[{key.inline}, {val.inline}]"

    annotations = _range_metadata(
        entry_value.get("minProperties"),
        entry_value.get("maxProperties"),
        "len()",
    )

    if annotations:
        inline = f"typ.Annotated[{inline}, {repr(annotations)[1:-1]}]"

    return CodeResult(block, inline, _get_docstring(entry_value), _get_default(entry_value))


def _block_docstring(docstring: list[str]) -> list[str]:
    """Convert a list of docstring lines to a list of lines for an indented docstring"""
    result = []
    if docstring:
        if len(docstring) == 1:
            result.append(f'    """{docstring[0]}"""')
        else:
            result.append('    """')
            result.extend(f"    {line}" for line in docstring)
            result.append('    """')
        result.append("")
    return result


def _typed_dict_prologue(type_name: str, is_total: bool, has_invalid_identifiers: bool) -> str:
    """The first line of the TypedDict definition"""
    if has_invalid_identifiers:
        return f"{type_name} = typ.TypedDict('{type_name}', {'{'}"
    elif is_total:
        return f"class {type_name}(typ.TypedDict):"
    else:
        return f"class {type_name}(typ.TypedDict, total=False):"


def _typed_dict_epilogue(class_length: int, is_total: bool, has_invalid_identifiers: bool) -> str | None:
    """The last line of the TypedDict definition"""
    if has_invalid_identifiers:
        if is_total:
            return "})"
        else:
            return "}, total=False)"
    elif class_length == 1:
        return "    pass"
    return None


def _convert_object_entry(entry_name: str, entry_value: dict, defs: dict) -> CodeResult:
    """Handles that are type = object"""
    block_result = ""

    _merge_conditionals_into_main(entry_value)

    properties = typing.cast("dict[str, typing.Any]", entry_value.get("properties", {}))
    additionalProperties = entry_value.get("additionalProperties", True)
    patternProperties = entry_value.get("patternProperties", {})
    properties.pop("$schema", None)  # ignore the schema field, as it's invalid syntax and not interesting

    if not properties and (patternProperties or isinstance(additionalProperties, dict)):
        return _convert_true_dict(entry_name, entry_value, defs)

    has_invalid_identifiers = any(not name.isidentifier() or keyword.iskeyword(name) for name in properties)

    typed_dict = []
    if not (has_invalid_identifiers or additionalProperties):
        typed_dict.append("@typ.final")

    required_fields = entry_value.get("required", [])

    type_name = _snake_case_to_pascal_case(entry_name)
    is_total = len(required_fields) > len(properties) - len(required_fields)

    typed_dict.append(_typed_dict_prologue(type_name, is_total, has_invalid_identifiers))

    docstring = _get_docstring(entry_value)
    typed_dict.extend(_block_docstring(docstring))

    for prop_name, prop_value in properties.items():
        inner = _convert_schema_entry(f"{entry_name}__{prop_name}", prop_value, defs)
        if inner.block:
            block_result += f"{inner.block}\n"

        if (prop_name in required_fields) == is_total:
            prop_inline = inner.inline
        elif prop_name in required_fields:
            prop_inline = f"typ.Required[{inner.inline}]"
        else:
            prop_inline = f"typ.NotRequired[{inner.inline}]"

        if inner.default_value is not NoDefault:
            prop_inline += f" = {repr(inner.default_value)}"

        if has_invalid_identifiers:
            typed_dict.append(f"    '{prop_name}': {prop_inline},")
        else:
            typed_dict.append(f"    {prop_name}: {prop_inline}")
            typed_dict.extend(_block_docstring(inner.inline_docstring))

    epilogue = _typed_dict_epilogue(len(typed_dict), is_total, has_invalid_identifiers)
    if epilogue is not None:
        typed_dict.append(epilogue)

    merged_dict = "\n".join(typed_dict)
    block_result += f"\n{merged_dict}"

    desc = entry_value.get("description")
    inline_doc = [desc] if isinstance(desc, str) else []

    return CodeResult(block_result, type_name, inline_doc, _get_default(entry_value))


def _convert_enum_entry(entry_name: str, entry_value: dict, defs: dict) -> CodeResult:
    """Convert entries with an `enum` field"""
    # TODO: verify the type field matches the values in the enum field? or not, idk
    values = [repr(value) for value in entry_value["enum"]]
    inline = _snake_case_to_pascal_case(entry_name)
    value_block = ",\n    ".join(values)
    return CodeResult(
        f"{inline} = typ.Literal[\n    {value_block}\n]",
        inline,
        _get_docstring(entry_value),
        _get_default(entry_value),
    )


PRIMITIVE_TYPES = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "null": "None",
}


def _string_metadata(entry_value: dict) -> list:
    """Returns annotations for string-type metadata"""
    annotations = []

    annotations.extend(_range_metadata(entry_value.get("minLength"), entry_value.get("maxLength"), "len()"))

    pattern = entry_value.get("pattern")
    if pattern is not None:
        annotations.append(f"/{pattern}/")

    return annotations


def _number_metadata(entry_value: dict) -> list:
    """Returns annotations for number-type metadata"""
    annotations = []

    minimum = entry_value.get("minimum")
    exclusive_min = entry_value.get("exclusiveMinimum")
    if exclusive_min is not None:
        minimum = exclusive_min
        exclusive_min = True

    maximum = entry_value.get("maximum")
    exclusive_max = entry_value.get("exclusiveMaximum")
    if exclusive_max is not None:
        maximum = exclusive_max
        exclusive_max = True

    annotations.extend(_range_metadata(minimum, maximum, "value", exclusive_min, exclusive_max))

    multiple_of = entry_value.get("multipleOf")
    if multiple_of is not None:
        annotations.append(f"value % {multiple_of} == 0")

    return annotations


def _convert_primitive_entry(entry_name: str, entry_value: dict, defs: dict) -> CodeResult:
    """Converts entries of primitive type"""
    inline = PRIMITIVE_TYPES[entry_value["type"]]

    annotations = []
    annotations.extend(_string_metadata(entry_value))
    annotations.extend(_number_metadata(entry_value))

    if annotations:
        inline = f"typ.Annotated[{inline}, {repr(annotations)[1:-1]}]"

    return CodeResult(
        "",
        inline,
        _get_docstring(entry_value),
        _get_default(entry_value),
    )


def _convert_schema_entry(entry_name: str, entry_value: dict, defs: dict) -> CodeResult:
    if "$ref" in entry_value:
        if "#/$defs/" not in entry_value["$ref"]:
            msg = f"Invalid entry at {entry_name}: only $defs are supported in $ref ({entry_value})"
            raise ValueError(msg)

        def_id = entry_value["$ref"][8:]

        combined_value = defs.get(def_id, {})
        combined_value.update(entry_value)

        return CodeResult(
            "", _snake_case_to_pascal_case(def_id), _get_docstring(combined_value), _get_default(combined_value)
        )

    if "anyOf" in entry_value:
        return _convert_any_of(entry_name, entry_value, defs)

    if "enum" in entry_value:
        return _convert_enum_entry(entry_name, entry_value, defs)

    entry_types = entry_value.get("type")
    if entry_types is None:
        raise ValueError(f"{entry_name} has no type defined")

    if isinstance(entry_types, list):
        alternatives: list[dict] = []
        for entry_type in entry_types:
            alternative = copy.copy(entry_value)
            alternative["type"] = entry_type
            alternatives.append(alternative)
        return _convert_union(entry_name, alternatives, defs)

    return _convert_single_schema_entry(entry_name, entry_value, defs)


def _convert_single_schema_entry(entry_name: str, entry_value: dict, defs: dict) -> CodeResult:
    entry_type = entry_value["type"]
    match entry_type:
        case "array":
            result = _convert_array_entry(entry_name, entry_value, defs)

        case "object":
            result = _convert_object_entry(entry_name, entry_value, defs)

        case _:
            if entry_type not in PRIMITIVE_TYPES:
                msg = f"Invalid entry at {entry_name}: unknown type {entry_type}"
                raise ValueError(msg)
            result = _convert_primitive_entry(entry_name, entry_value, defs)

    return result


def convert_schema_to(schema_path: Path, output: Path, root_name: str) -> None:
    with schema_path.open() as f:
        schema = json.load(f)

    result = """# This file is generated. Manual changes will be lost
# fmt: off
# ruff: noqa
# mypy: disable-error-code="misc"
from __future__ import annotations

import typing_extensions as typ


"""
    defs = schema.get("$defs", {})

    if defs:
        result += "# Definitions\n"

        for def_name, def_value in defs.items():
            inner = _convert_schema_entry(def_name, def_value, {})

            if inner.block:
                result += f"{inner.block}\n"

            def_pascal = _snake_case_to_pascal_case(def_name)
            if def_pascal != inner.inline:
                result += f"{def_pascal}: typ.TypeAlias = {inner.inline}\n"

        result += "\n"

    result += "# Schema entries\n"

    root = _convert_schema_entry(root_name, schema, defs)
    if root.block:
        result += root.block

    if root_name != root.inline:
        result += f"\n{root_name}: typ.TypeAlias = {root.inline}\n"
    elif result[-1] != "\n":
        result += "\n"

    output.write_text(result)
