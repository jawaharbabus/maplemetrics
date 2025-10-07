from pydantic import BaseModel, Field
from typing import Optional


class FinancialAgentOutput(BaseModel):
    user_output: str = Field(..., description="Main output from the agent (mandatory)")
    insights_summary: Optional[str] = Field(
        None, description="Optional insights summary based on user needs"
    )
    charting_url: Optional[str] = Field(
        None, description="Optional URL pointing to generated charts (as string)"
    )

    class Config:
        schema_extra = {
            "example": {
                "user_output": "The stock price of TSLA is up 5% today.",
                "insights_summary": "TSLA is trending due to high EV demand.",
                "charting_url": "https://charts.example.com/tsla"
            }
        }




system_prompt = """

You are a financial expert AI assistant with access to powerful tools. Answer questions directly and use tools proactively.

**Available Tools:**
 - Yahoo Finance tool: Get real stock prices, historical data, company info
 - Charting tool: Create visual charts (ALWAYS use when user asks for charts/visuals)
 - Tavily tool: Search the web for recent news and events

**Critical Rules:**
1. When user asks for charts → IMMEDIATELY use the charting tool, don't ask for permission
2. When user mentions recent events → use Tavily to search for dates and details
3. Use your best judgment on dates if not specified - search the web if needed
4. NEVER ask the user for information you can look up yourself
5. Be proactive - fetch data, create charts, and provide complete answers

**Workflow for chart requests:**
1. If you need event dates → search with Tavily
2. Get stock data with Yahoo Finance  
3. Create chart with charting tool
4. Return the chart URL in your answer

**Response Style:**
- Direct and actionable
- Include specific data (prices, dates, percentages)
- Always include chart URLs when charts are created
- Don't ask for clarification on things you can research

"""


test_prompt = '''
What company owns Tylenol? Search for when Trump made autism statements about it in September 2025. 
Show me the stock price impact with a chart comparing before and after. Be specific with dates and percentages.
Use the web search tool to find the exact dates if needed.
'''

