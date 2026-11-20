import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.llm_pick import pick_llm
from utils.etl_tools import ETLTools
from Models.schema import ETLAgentSchema
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langchain.tools import tool
from langchain_anthropic import ChatAnthropic


#------------------------------------ AGENT TOOLS ------------------------------------#


@tool
def extract_load_tool(url:str, output_folder:str, format:str) -> str:
    """
    This tool extracts the data from the API (url) and loads it into the
    the desired location (output_folder).

    Args:
        url (str): The API endpoint from which to extract data.
        output_folder (str): The folder where the extracted data will be saved.
        format (str): The format in which to save the extracted data (csv, json, parquet).
    
    Returns:
        str: A message indicating the success or failure of the operation.

    """
    etl_tools = ETLTools()
    return etl_tools.extract_load(url, output_folder, format)


@tool
def safe_filter_tool(
    input_file: str,
    output_file: str,
    column: str,
    value: str
) -> str:
    """
    Filter a CSV dataset by matching a column to a value.

    Args:
        input_file: Input CSV path relative to the data directory.
        output_file: Output CSV path relative to the data directory.
        column: Column to filter.
        value: Value to match.

    Returns:
        Result of the filtering operation.
    """
    etl_tools = ETLTools()

    result = etl_tools.safe_filter_csv(
        input_file=input_file,
        output_file=output_file,
        column=column,
        value=value
    )

    return str(result)

@tool
def safe_extract_tool(url: str, output_file: str) -> str:
    """
    Extract Pokemon records from the approved PokeAPI endpoint
    and save them as a CSV file.

    Args:
        url: PokeAPI URL, such as
             https://pokeapi.co/api/v2/pokemon?limit=10
        output_file: CSV path relative to the data directory,
                     such as extract/pokemon_10.csv.

    Returns:
        Extraction result containing status, row count, and file path.
    """
    etl_tools = ETLTools()

    result = etl_tools.safe_extract_api(
        url=url,
        output_file=output_file
    )

    return str(result)


# Toolkit 
tools = [safe_extract_tool, safe_filter_tool]

llm = pick_llm("medium")
llm_bind = llm.bind_tools(tools)


# ---------------------------------------- AGENT GRAPH ---------------------------------------- #

from langchain_core.messages import SystemMessage

def llm_node(state: ETLAgentSchema):

    system_prompt = """
    You are an AI Data Analyst responsible for ETL operations.

    Available tools:

    1. safe_extract_tool:
       Extract records from the approved PokeAPI endpoint
       and save them into a CSV file.

    2. safe_filter_tool:
       Filter an existing CSV file by column and value,
       then save the result to another CSV file.

    Rules:
    - Understand the user's natural-language request.
    - Select the correct tool for each operation.
    - For multi-step requests, execute operations in order.
    - If extraction and filtering are requested, extract first.
    - Wait for the extraction result before filtering.
    - Do not repeat a successful operation.
    - Do not call the same tool again with identical arguments
      after it has succeeded.
    - Use paths relative to the data directory.
    - Never generate or execute arbitrary Python code.
    - Do not claim success unless the tool confirms it.
    - If all requested operations are complete, provide a final answer
      without calling any more tools.
    """

    messages = state.messages

    final_answer = llm_bind.invoke(
        [SystemMessage(content=system_prompt)] + messages
    )

    return {"messages": [final_answer]}


def tool_node(state: ETLAgentSchema):
    """
    Execute ETL tools while preventing duplicate
    successful operations.
    """
    import json

    tools_by_name = {t.name: t for t in tools}
    tool_results = []

    # Track previously successful tool calls.
    successful_calls = set()

    for message in state.messages:
        if not isinstance(message, AIMessage):
            continue

        for call in message.tool_calls or []:
            matching_results = [
                m for m in state.messages
                if isinstance(m, ToolMessage)
                and m.tool_call_id == call["id"]
            ]

            if matching_results:
                result = matching_results[0].content

                if (
                    "status" in result
                    and "success" in result
                ):
                    signature = (
                        call["name"],
                        json.dumps(call["args"], sort_keys=True)
                    )
                    successful_calls.add(signature)

    current_calls = state.messages[-1].tool_calls

    for call in current_calls:
        name = call["name"]
        args = call["args"]

        signature = (
            name,
            json.dumps(args, sort_keys=True)
        )

        if signature in successful_calls:
            observation = (
                "This operation already completed successfully. "
                "Do not repeat it. Continue with the remaining "
                "operations or provide the final answer."
            )
        else:
            try:
                selected_tool = tools_by_name.get(name)

                if selected_tool is None:
                    observation = f"Error: Unknown tool '{name}'"
                else:
                    observation = str(selected_tool.invoke(args))

                    if (
                        "status" in observation
                        and "success" in observation
                    ):
                        successful_calls.add(signature)

            except Exception as e:
                observation = f"Error executing {name}: {e}"

        tool_results.append(
            ToolMessage(
                content=str(observation),
                tool_call_id=call["id"]
            )
        )

    return {"messages": tool_results}

# Nodes & Edges
etl_analyst_graph = StateGraph(ETLAgentSchema)
etl_analyst_graph.add_node("llm_node", llm_node)
etl_analyst_graph.add_node("tool_node", tool_node)

etl_analyst_graph.add_edge(START, "llm_node")

def is_tool_call(state:ETLAgentSchema):
    tool_calls = state.messages[-1].tool_calls

    if tool_calls:
        return "tool_node"
    else:
        return "end"

etl_analyst_graph.add_conditional_edges(
    "llm_node",is_tool_call,
    {
        "tool_node": "tool_node",
        "end": END
    }
)

etl_analyst_graph.add_edge("tool_node", "llm_node")

etl_analyst = etl_analyst_graph.compile()
