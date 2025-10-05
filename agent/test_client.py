import os
import asyncio
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages.utils import count_tokens_approximately
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from langmem.short_term import SummarizationNode, RunningSummary
from langgraph.prebuilt.chat_agent_executor import AgentState

from agent.misc import FinancialAgentOutput, test_prompt, system_prompt


class FinancialAgent:
    """
    FinancialAgent integrates LangGraph's ReAct agent with multiple MCP tools 
    (charting, Yahoo Finance, Tavily) and a summarization node for context management.
    """

    def __init__(
        self,
        openai_api_key: str | None = None,
        tavily_api_key: str | None = None,
        chart_url: str = "http://localhost:1122/mcp",
        model_name: str = "gpt-5",
        max_context_tokens: int = 2000,
        max_summary_tokens: int = 1000,
    ):
        # === API keys and model setup ===
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_KEY")
        self.tavily_api_key = tavily_api_key or os.getenv("TAVILY_API_KEY")

        self.model = ChatOpenAI(model=model_name, api_key=self.openai_api_key)
        
        # === MCP Client Setup ===
        self.client = MultiServerMCPClient(
            {
                "chart": {
                    "url": chart_url,
                    "transport": "streamable_http",
                },
                "yfinance": {
                    "command": "mcp-yahoo-finance",
                    "args": [],
                    "transport": "stdio",
                },
                "tavily": {
                    "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={self.tavily_api_key}",
                    "transport": "streamable_http",
                },
            }
        )

        # === Summarization Node for rolling memory ===
        self.summarization_node = SummarizationNode(
            token_counter=count_tokens_approximately,
            model=self.model,
            max_tokens=max_context_tokens,
            max_summary_tokens=max_summary_tokens,
            output_messages_key="llm_input_messages",
        )

        # === State and checkpointing setup ===
        class State(AgentState):
            context: dict[str, RunningSummary]

        self.State = State
        self.checkpointer = InMemorySaver()

        # === Initialize agent lazily ===
        self.agent = None

    async def initialize(self):
        """Initializes the agent asynchronously (loads tools)."""
        tools = await self.client.get_tools()

        self.agent = create_react_agent(
            model=self.model,
            tools=tools,
            # state_schema=self.State,
            checkpointer=self.checkpointer,
            # pre_model_hook=self.summarization_node,  # optional: enable if summarization is desired
        )

    async def invoke(self, user_prompt: str, thread_id: str = "1") -> Any:
        """Invokes the ReAct agent asynchronously."""
        if not self.agent:
            await self.initialize()

        config = {"configurable": {"thread_id": thread_id}}

        response = await self.agent.ainvoke(
            {"messages": [{"role":"system","content":system_prompt},{"role": "user", "content": user_prompt}]},
            config=config,
        )   
        return response

    async def invoke_structured(self, user_prompt: str, thread_id: str = "1") -> FinancialAgentOutput:
        """Invokes the agent and returns structured output."""
        # First get the regular response
        response = await self.invoke(user_prompt, thread_id)
        
        # Extract the final message content
        final_message = response["messages"][-1].content
        
        # Use structured output model to parse the response
        structured_model = self.model.with_structured_output(FinancialAgentOutput)
        
        # Create a parsing prompt
        parsing_prompt = f"""
        Please extract the following information from this agent response and format it according to the schema:
        
        Agent Response: {final_message}
        
        Extract:
        - user_output (mandatory): The main response to the user
        - insights_summary (optional): Any key insights or analysis 
        - charting_url (optional): Any chart URLs that were generated
        """
        
        structured_response = await structured_model.ainvoke([{"role": "user", "content": parsing_prompt}])
        return structured_response

    # async def aclose(self):
    #     """Closes the MCP client gracefully."""
    #     await self.client.aclose()


# === Example Usage ===
if __name__ == "__main__":
    from agent.misc import test_prompt

    async def main():
        agent = FinancialAgent()
        
        # Test regular invoke
        # response = await agent.invoke(test_prompt)
        # print("Regular response:", response)
        
        # Test structured invoke
        structured_response = await agent.invoke_structured(test_prompt)
        print("Structured response:", structured_response)
        
        # await agent.aclose()

    asyncio.run(main())
