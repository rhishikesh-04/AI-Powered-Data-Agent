import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.messages import AIMessage, ToolMessage
from Models.schema import ETLAgentSchema
from agents.etl_analyst import tool_node


def test_duplicate_tool_call():
    args = {
        "url": "https://pokeapi.co/api/v2/pokemon?limit=10",
        "output_file": "extract/duplicate_test.csv"
    }

    first_call = AIMessage(
        content="",
        tool_calls=[{
            "name": "safe_extract_tool",
            "args": args,
            "id": "call_1",
            "type": "tool_call"
        }]
    )

    first_result = ToolMessage(
        content=str({
            "status": "success",
            "rows": 10,
            "output_file": "extract/duplicate_test.csv"
        }),
        tool_call_id="call_1"
    )

    repeated_call = AIMessage(
        content="",
        tool_calls=[{
            "name": "safe_extract_tool",
            "args": args,
            "id": "call_2",
            "type": "tool_call"
        }]
    )

    state = ETLAgentSchema(
        messages=[first_call, first_result, repeated_call]
    )

    result = tool_node(state)

    response = result["messages"][0]

    print("Duplicate response:", response.content)

    assert response.tool_call_id == "call_2"
    assert "already completed successfully" in response.content

    print("PASS: Duplicate tool execution was blocked.")


if __name__ == "__main__":
    test_duplicate_tool_call()