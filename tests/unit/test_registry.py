from app.tools.registry import REQUIRED_TOOLS, ToolRegistry


def test_required_tools_and_strict_schemas() -> None:
    registry = ToolRegistry()
    assert set(registry.definitions) == set(REQUIRED_TOOLS)
    for tool in registry.openai_tools():
        assert tool["strict"] is True
        schema = tool["parameters"]
        assert schema["additionalProperties"] is False
        assert set(schema["required"]) == set(schema["properties"])
        assert callable(registry.definitions[tool["name"]].handler)
