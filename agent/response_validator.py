from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional, Dict, Any
import json


class AgentResponse(BaseModel):
    """
    Pydantic model for validating agent responses with structured output.
    
    Fields:
        user_output: Mandatory text response for the user
        insights_summary: Optional summary of key insights and findings
        charting_url: Optional URL to generated charts or visualizations
    """
    
    user_output: str = Field(
        ...,  # Required field
        min_length=1,
        description="The main response text for the user. This field is mandatory."
    )
    
    insights_summary: Optional[str] = Field(
        None,
        description="Optional summary of key insights, analysis, or findings from the query."
    )
    
    charting_url: Optional[HttpUrl] = Field(
        None,
        description="Optional URL to charts, graphs, or visualizations generated for the user."
    )
    
    @validator('user_output')
    def validate_user_output(cls, v):
        """Ensure user_output is not empty or just whitespace"""
        if not v or not v.strip():
            raise ValueError('user_output cannot be empty or just whitespace')
        return v.strip()
    
    @validator('insights_summary')
    def validate_insights_summary(cls, v):
        """Clean up insights_summary if provided"""
        if v is not None:
            v = v.strip()
            if not v:  # If empty after stripping, set to None
                return None
        return v
    
    def to_user_friendly_dict(self) -> Dict[str, Any]:
        """Convert to a user-friendly dictionary format"""
        result = {"response": self.user_output}
        
        if self.insights_summary:
            result["insights"] = self.insights_summary
        
        if self.charting_url:
            result["chart_url"] = str(self.charting_url)
        
        return result
    
    def to_json_string(self, **kwargs) -> str:
        """Convert to JSON string with pretty formatting by default"""
        if 'indent' not in kwargs:
            kwargs['indent'] = 2
        return self.json(**kwargs)
    
    @classmethod
    def from_raw_response(cls, raw_response: str) -> 'AgentResponse':
        """
        Create AgentResponse from raw agent response text.
        Tries to parse as JSON first, falls back to treating as plain text.
        """
        try:
            # Try to parse as JSON
            data = json.loads(raw_response)
            return cls(**data)
        except (json.JSONDecodeError, TypeError, ValueError):
            # If not JSON, treat as plain user_output
            return cls(user_output=raw_response)
    
    @classmethod
    def create_simple_response(cls, message: str) -> 'AgentResponse':
        """Create a simple response with just user_output"""
        return cls(user_output=message)
    
    @classmethod
    def create_with_insights(cls, message: str, insights: str) -> 'AgentResponse':
        """Create a response with user_output and insights"""
        return cls(user_output=message, insights_summary=insights)
    
    @classmethod
    def create_with_chart(cls, message: str, chart_url: str, insights: Optional[str] = None) -> 'AgentResponse':
        """Create a response with user_output, chart URL, and optional insights"""
        return cls(
            user_output=message,
            insights_summary=insights,
            charting_url=chart_url
        )


class AgentResponseParser:
    """Helper class for parsing and validating agent responses"""
    
    @staticmethod
    def parse_and_validate(response_text: str) -> AgentResponse:
        """
        Parse and validate agent response text into structured format.
        
        Args:
            response_text: Raw response text from the agent
            
        Returns:
            Validated AgentResponse object
            
        Raises:
            ValidationError: If the response doesn't meet validation requirements
        """
        try:
            return AgentResponse.from_raw_response(response_text)
        except Exception as e:
            # If validation fails, create a simple response with error info
            return AgentResponse.create_simple_response(
                f"Response validation failed: {str(e)}\n\nOriginal response: {response_text}"
            )
    
    @staticmethod
    def extract_structured_response(agent_output: Dict[str, Any]) -> AgentResponse:
        """
        Extract structured response from full agent output dictionary.
        
        Args:
            agent_output: Full agent response dictionary
            
        Returns:
            Validated AgentResponse object
        """
        # Try to find the main response text
        response_text = ""
        
        # Look for response in common locations
        if isinstance(agent_output, dict):
            # Check messages array
            messages = agent_output.get("messages", [])
            for message in reversed(messages):  # Start from the end
                if hasattr(message, 'content') and message.content:
                    response_text = message.content
                    break
                elif isinstance(message, dict) and message.get('content'):
                    response_text = message['content']
                    break
            
            # Fallback to direct content
            if not response_text:
                response_text = agent_output.get("content", "")
        
        # If still no response, convert the whole output to string
        if not response_text:
            response_text = str(agent_output)
        
        return AgentResponseParser.parse_and_validate(response_text)


# Example usage and validation functions
def validate_response_example():
    """Example of how to use the AgentResponse validator"""
    
    # Example 1: Simple response
    simple = AgentResponse.create_simple_response("Apple Inc. owns Tylenol through its subsidiary.")
    print("Simple Response:")
    print(simple.to_json_string())
    print()
    
    # Example 2: Response with insights
    with_insights = AgentResponse.create_with_insights(
        message="Johnson & Johnson owns Tylenol. Here's the stock analysis:",
        insights="Stock showed minimal impact from Trump's statements about autism links. No significant market correlation found."
    )
    print("Response with Insights:")
    print(with_insights.to_json_string())
    print()
    
    # Example 3: Full response with chart
    full_response = AgentResponse.create_with_chart(
        message="Here's the complete analysis of J&J stock performance around Trump's statements:",
        chart_url="http://localhost:1122/chart/jnj_analysis.png",
        insights="Analysis shows no statistically significant impact on stock price following the statements."
    )
    print("Full Response with Chart:")
    print(full_response.to_json_string())
    print()
    
    # Example 4: JSON parsing
    json_text = '''
    {
        "user_output": "Based on my analysis, Johnson & Johnson owns Tylenol.",
        "insights_summary": "No significant stock impact observed.",
        "charting_url": "http://localhost:1122/charts/jnj_timeline.png"
    }
    '''
    
    parsed = AgentResponse.from_raw_response(json_text)
    print("Parsed from JSON:")
    print(parsed.to_user_friendly_dict())


if __name__ == "__main__":
    validate_response_example()
