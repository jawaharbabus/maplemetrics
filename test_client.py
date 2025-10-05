from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain.agents import AgentExecutor
from langchain_openai import ChatOpenAI
import os
import asyncio
from prompt import prompt

async def main():
    client = MultiServerMCPClient(
        {
            "chart": {
            "url": "http://localhost:1122/mcp",   # check port after running server
            "transport": "streamable_http"
        },
        "statcan": {
            "command": "uv",
            "args": [
            "run",
            "--with", "fastmcp",
            "--with", "httpx", 
            "sh",
            "-c",
            "cd ~/Documents/project/opensrc_proj/mcp-statcan && python -m src.server"
            ],
        "transport": "stdio"
        }
        
})
    tools = await client.get_tools()
    model = ChatOpenAI(
        model="gpt-5-mini",
        api_key=os.getenv("OPENAI_KEY")
    )
    agent = create_react_agent(
        model,
        tools
    )

    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # Example query: ask agent to make a chart
    resp = await agent.ainvoke({
        "messages": [
            {
                "role": "user",
                "content": prompt
                }]
    })
    print(resp)
    
if __name__ == "__main__":
    
    asyncio.run(main())