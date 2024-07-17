import toml

with open("pyproject.toml", "r") as f:
    try:
        toml_data = toml.load(f)
        print("TOML file is valid")
    except toml.TomlDecodeError as e:
        print(f"TOML file is invalid: {e}")
