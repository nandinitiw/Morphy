import asyncio

import anthropic

from agent.prompts import COACH_SYSTEM_PROMPT
from agent.tools import TOOLS, execute_tool

client = anthropic.Anthropic()
MAX_TOOL_ITERATIONS = 10


async def run_coach_session(username: str, user_message: str, db) -> str:
    """
    Runs one turn of the coach agent.
    The agent autonomously decides which tools to call and chains them together.
    """

    messages = [{"role": "user", "content": user_message}]

    for _ in range(MAX_TOOL_ITERATIONS):
        response = await asyncio.to_thread(
            client.messages.create,
            model="claude-opus-4-5",
            max_tokens=4096,
            system=COACH_SYSTEM_PROMPT.format(username=username),
            tools=TOOLS,
            messages=messages,
        )

        text_blocks = [block.text for block in response.content if block.type == "text"]
        tool_use_blocks = [block for block in response.content if block.type == "tool_use"]

        if response.stop_reason == "end_turn" or not tool_use_blocks:
            return "\n".join(text_blocks)

        tool_results = []
        for tool_use in tool_use_blocks:
            result = await execute_tool(tool_use.name, tool_use.input, username, db)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": result,
            })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    return "Coach session exceeded maximum tool iterations."
