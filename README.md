# jsonschema-to-typeddict
precommit hook for creating a TypedDict definition for your JsonSchema

## Usage

Add the following to your `.pre-commit-config.yaml`:

```yaml
-   repo: https://github.com/henriquegemignani/jsonschema-to-typeddict
    rev: v1.0.1
    hooks:
    -   id: jsonschema-to-typeddict
        files: src/my_package/files/schema.json
        args: [ --output-path, src/my_package/configuration.pyi, --root-name, Configuration ]
```