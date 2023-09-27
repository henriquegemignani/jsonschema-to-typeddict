import argparse
from pathlib import Path

from . import converter


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("schema_path", type=Path, help="Path to the jsonschema file")
    parser.add_argument("output_path", type=Path, help="Path to the generated stub file")
    parser.add_argument("root_name", type=str, help="Name of the root argument")
    return parser


def main() -> None:
    args = create_parser().parse_args()
    converter.convert_schema_to(
        args.schema_path,
        args.output_path,
        args.root_name,
    )


main()
