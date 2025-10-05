from pydantic import BaseModel, HttpUrl, Field
from typing import Optional

class FinancialAgentOutput(BaseModel):
    user_output: str = Field(..., description="Main output from the agent (mandatory)")
    insights_summary: Optional[str] = Field(
        None, description="Optional insights summary based on user needs"
    )
    charting_url: Optional[HttpUrl] = Field(
        None, description="Optional URL pointing to generated charts"
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

You are a financial expert. You are a ReAct agent. You have access to the following tools:
 - Yahoo Finance tool: useful for getting stock data and financial information.
 - Charting tool: useful for creating visual charts based on data.
 - Tavily tool: useful for advanced financial analysis and insights.

Your goal is to provide accurate and insightful financial information and visualizations based on user queries.
Note: your context window is limited, so be efficient in using the tools available to you. Fetch only the data you need to answer the question.

The final response should be in JSON format matching the FinancialAgentOutput schema.

"""


test_prompt = '''

        what company owns tylenol?? was there any major impacts on it's stock price after trump linked it with autism?? or any impacts on stock market becasue of his statments?
        Give me the visual charts for the compariosn.

     '''

