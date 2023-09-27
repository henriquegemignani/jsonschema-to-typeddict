import argparse
from pathlib import Path

from . import converter


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-path", type=Path, required=True, help="Path to the generated stub file")
    parser.add_argument("--root-name", type=str, required=True, help="Name of the root argument")
    parser.add_argument("schema_path", type=Path, help="Path to the jsonschema file")
    return parser


def main() -> None:
    args = create_parser().parse_args()
    converter.convert_schema_to(
        args.schema_path,
        args.output_path,
        args.root_name,
    )


main()
