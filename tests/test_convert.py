from pathlib import Path

from jsonschema_to_typeddict import converter


def test_convert(tmp_path: Path):
    this = Path(__file__).parent
    expected = this.joinpath("sample_schema.pyi").read_text()

    converter.convert_schema_to(
        this.joinpath("sample_schema.json"),
        tmp_path.joinpath("output.pyi"),
        "Sample",
    )
    output = tmp_path.joinpath("output.pyi").read_text()

    assert output == expected
