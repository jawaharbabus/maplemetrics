#!/usr/bin/env python3
"""
Test the FinancialAgent with Pydantic response validation
"""

import asyncio
import sys
import os

# Add current directory to path so we can import from agent module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.test_client import FinancialAgent
from agent.misc import test_prompt
from response_validator import AgentResponse


async def test_basic_validation():
    """Test basic Pydantic validation functionality"""
    print("🧪 Testing Pydantic Response Validation")
    print("=" * 50)
    
    # Test 1: Simple response
    simple = AgentResponse.create_simple_response("Johnson & Johnson owns Tylenol.")
    print("✅ Simple Response:")
    print(simple.to_json_string())
    print()
    
    # Test 2: Response with insights
    with_insights = AgentResponse.create_with_insights(
        message="J&J owns Tylenol. Stock analysis shows minimal impact from Trump's statements.",
        insights="No statistically significant correlation found between the statements and stock performance."
    )
    print("✅ Response with Insights:")
    print(with_insights.to_json_string())
    print()
    
    # Test 3: Full structured response
    full_response = AgentResponse.create_with_chart(
        message="Complete analysis of J&J stock around Trump's autism-Tylenol statements:",
        chart_url="http://localhost:1122/charts/jnj_impact_analysis.png",
        insights="Analysis period: 2016-2024. No significant market reaction detected."
    )
    print("✅ Full Structured Response:")
    print(full_response.to_user_friendly_dict())
    print()


async def test_agent_with_validation():
    """Test the FinancialAgent with response validation"""
    print("🤖 Testing FinancialAgent with Response Validation")
    print("=" * 60)
    
    try:
        # Create agent
        agent = FinancialAgent(model_name="gpt-4o")  # Use proper model name
        print("✅ Agent created")
        
        # Test different response methods
        print(f"📝 Query: {test_prompt[:100]}...")
        print()
        
        # Method 1: Simple chat (just text)
        print("1️⃣ Simple Chat Response:")
        print("-" * 30)
        try:
            chat_response = await agent.chat(test_prompt)
            print(chat_response)
        except Exception as e:
            print(f"❌ Chat error: {e}")
        print()
        
        # Method 2: Structured response
        print("2️⃣ Structured Response:")
        print("-" * 30)
        try:
            structured = await agent.invoke_structured(test_prompt)
            print("Raw structured object:")
            print(structured.to_json_string())
        except Exception as e:
            print(f"❌ Structured response error: {e}")
        print()
        
        # Method 3: Full analysis dictionary
        print("3️⃣ Full Analysis Dictionary:")
        print("-" * 30)
        try:
            analysis = await agent.get_full_analysis(test_prompt)
            print(analysis)
        except Exception as e:
            print(f"❌ Analysis error: {e}")
        
        # Cleanup
        await agent.aclose()
        print("\n✅ Agent closed successfully")
        
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        import traceback
        traceback.print_exc()


async def interactive_test():
    """Interactive test mode"""
    print("🎯 Interactive Financial Agent with Response Validation")
    print("Commands: 'quit' to exit, 'simple' for text only, 'full' for structured")
    print("-" * 60)
    
    try:
        agent = FinancialAgent(model_name="gpt-4o")
        print("✅ Agent ready")
        
        while True:
            user_input = input("\n💬 Your query: ").strip()
            
            if user_input.lower() == 'quit':
                break
            elif not user_input:
                continue
            
            try:
                # Default to full structured response
                if user_input.lower() == 'simple':
                    response = await agent.chat("Tell me about Apple stock.")
                    print(f"🤖 Response: {response}")
                elif user_input.lower() == 'full':
                    analysis = await agent.get_full_analysis("Analyze Tesla stock performance.")
                    print("🤖 Full Analysis:")
                    for key, value in analysis.items():
                        print(f"   {key}: {value}")
                else:
                    # Process the actual user input
                    analysis = await agent.get_full_analysis(user_input)
                    print("🤖 Analysis:")
                    for key, value in analysis.items():
                        print(f"   {key}: {value}")
                        
            except Exception as e:
                print(f"❌ Error: {e}")
        
        await agent.aclose()
        print("👋 Goodbye!")
        
    except KeyboardInterrupt:
        print("\n👋 Interrupted!")
    except Exception as e:
        print(f"❌ Interactive test failed: {e}")


async def main():
    """Main test function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        await interactive_test()
    elif len(sys.argv) > 1 and sys.argv[1] == "--validation-only":
        await test_basic_validation()
    else:
        # Run both tests
        await test_basic_validation()
        await test_agent_with_validation()


if __name__ == "__main__":
    asyncio.run(main())
