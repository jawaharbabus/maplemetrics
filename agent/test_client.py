import os
import asyncio
import logging
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages.utils import count_tokens_approximately
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from langmem.short_term import SummarizationNode, RunningSummary
from langgraph.prebuilt.chat_agent_executor import AgentState

from agent.misc import FinancialAgentOutput, test_prompt, system_prompt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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
        enable_yfinance: bool = False,
        enable_tavily: bool = False,
    ):
        logger.info("🚀 Initializing FinancialAgent...")
        logger.info(f"📊 Model: {model_name}")
        logger.info(f"🔧 Chart URL: {chart_url}")
        logger.info(f"📈 Yahoo Finance enabled: {enable_yfinance}")
        logger.info(f"🔍 Tavily enabled: {enable_tavily}")
        
        # === API keys and model setup ===
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_KEY")
        self.tavily_api_key = tavily_api_key or os.getenv("TAVILY_API_KEY")

        self.model = ChatOpenAI(model=model_name, api_key=self.openai_api_key)
        logger.info("✅ OpenAI model initialized")
        
        # === MCP Client Setup (only enable what's needed) ===
        mcp_servers = {}
        
        # Only add chart if URL is provided
        if chart_url:
            logger.info(f"📊 Adding chart server: {chart_url}")
            mcp_servers["chart"] = {
                "url": chart_url,
                "transport": "streamable_http",
            }
        
        # Optional: Yahoo Finance (requires mcp-yahoo-finance installed)
        if enable_yfinance:
            logger.info("📈 Adding Yahoo Finance MCP server")
            mcp_servers["yfinance"] = {
                "command": "mcp-yahoo-finance",
                "args": [],
                "transport": "stdio",
            }
        
        # Optional: Tavily search
        if enable_tavily and self.tavily_api_key:
            logger.info("🔍 Adding Tavily search server")
            mcp_servers["tavily"] = {
                "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={self.tavily_api_key}",
                "transport": "streamable_http",
            }
        
        logger.info(f"🔌 Total MCP servers configured: {len(mcp_servers)}")
        self.client = MultiServerMCPClient(mcp_servers) if mcp_servers else None

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
        logger.info("⚙️ Initializing agent and loading tools...")
        tools = []
        if self.client:
            try:
                tools = await self.client.get_tools()
                logger.info(f"✅ Loaded {len(tools)} tools from MCP servers")
                for i, tool in enumerate(tools, 1):
                    logger.info(f"  {i}. {tool.name}")
            except Exception as e:
                logger.error(f"❌ Error loading tools: {e}")
                raise

        self.agent = create_react_agent(
            model=self.model,
            tools=tools,
            # state_schema=self.State,
            checkpointer=self.checkpointer,
            # pre_model_hook=self.summarization_node,  # optional: enable if summarization is desired
        )
        logger.info("✅ Agent initialized successfully")

    async def invoke(self, user_prompt: str, thread_id: str = "1") -> Any:
        """Invokes the ReAct agent asynchronously."""
        logger.info("=" * 80)
        logger.info(f"💬 USER PROMPT (Thread: {thread_id}):")
        logger.info(f"   {user_prompt}")
        logger.info("=" * 80)
        
        if not self.agent:
            await self.initialize()

        config = {"configurable": {"thread_id": thread_id}}

        try:
            logger.info("🤖 Invoking agent...")
            response = await self.agent.ainvoke(
                {"messages": [{"role":"system","content":system_prompt},{"role": "user", "content": user_prompt}]},
                config=config,
            )
            
            # Log the response
            if response and "messages" in response:
                logger.info(f"📨 Received {len(response['messages'])} messages")
                final_message = response["messages"][-1]
                logger.info(f"✅ AGENT RESPONSE:")
                logger.info(f"   Role: {getattr(final_message, 'type', 'unknown')}")
                logger.info(f"   Content: {final_message.content[:500]}..." if len(str(final_message.content)) > 500 else f"   Content: {final_message.content}")
            
            logger.info("=" * 80)
            return response
            
        except Exception as e:
            logger.error(f"❌ Error during agent invocation: {e}")
            logger.exception("Full traceback:")
            raise

    async def invoke_structured(self, user_prompt: str, thread_id: str = "1") -> FinancialAgentOutput:
        """Invokes the agent and returns structured output."""
        logger.info("📋 Requesting structured output...")
        
        # First get the regular response
        response = await self.invoke(user_prompt, thread_id)
        
        # Extract the final message content
        final_message = response["messages"][-1].content
        logger.info("🔄 Parsing response into structured format...")
        
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
        
        try:
            structured_response = await structured_model.ainvoke([{"role": "user", "content": parsing_prompt}])
            logger.info("✅ STRUCTURED OUTPUT:")
            logger.info(f"   📝 User Output: {structured_response.user_output[:200]}..." if len(structured_response.user_output) > 200 else f"   📝 User Output: {structured_response.user_output}")
            if structured_response.insights_summary:
                logger.info(f"   💡 Insights: {structured_response.insights_summary}")
            if structured_response.charting_url:
                logger.info(f"   📊 Chart URL: {structured_response.charting_url}")
            logger.info("=" * 80)
            return structured_response
        except Exception as e:
            logger.error(f"❌ Error parsing structured output: {e}")
            raise

    async def aclose(self):
        """Closes the MCP client gracefully."""
        logger.info("🔌 Closing MCP client connections...")
        if self.client:
            await self.client.aclose()
            logger.info("✅ MCP client closed")


# === Example Usage ===
if __name__ == "__main__":
    from agent.misc import test_prompt

    async def main():
        agent = FinancialAgent()
        
        # Test regular invoke
        response = await agent.invoke(test_prompt)
        print("Regular response:", response)
        
        # Test structured invoke
        structured_response = await agent.invoke_structured(test_prompt)
        print("Structured response:", structured_response)
        
        await agent.aclose()

    asyncio.run(main())
