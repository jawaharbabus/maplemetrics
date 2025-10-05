"""
Views for the financial agent API.
"""
import asyncio
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

from .test_client import FinancialAgent
from .serializers import AgentQuerySerializer, AgentResponseSerializer, StructuredAgentResponseSerializer

logger = logging.getLogger(__name__)


class AgentQueryView(APIView):
    """
    API endpoint for querying the financial agent.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._agent = None
    
    def _make_serializable(self, obj):
        """Convert complex objects to JSON-serializable format"""
        import json
        
        if obj is None:
            return None
        
        # Try to convert to dict
        if hasattr(obj, '__dict__'):
            try:
                return {k: self._make_serializable(v) for k, v in obj.__dict__.items() if not k.startswith('_')}
            except:
                pass
        
        # Handle lists
        if isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        
        # Handle dicts
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        
        # Handle primitives
        if isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        
        # Convert to string as fallback
        try:
            return str(obj)
        except:
            return None
    
    async def get_agent(self):
        """Get or create the agent instance."""
        if self._agent is None:
            self._agent = FinancialAgent(
                chart_url=settings.CHART_URL,
                model_name=settings.OPENAI_MODEL,
                max_context_tokens=settings.MAX_CONTEXT_TOKENS,
                max_summary_tokens=settings.MAX_SUMMARY_TOKENS,
                enable_yfinance=settings.ENABLE_YFINANCE,
                enable_tavily=settings.ENABLE_TAVILY,
            )
            await self._agent.initialize()
        return self._agent
    
    def post(self, request):
        """Handle POST request to query the agent."""
        logger.info(f"📥 Received query request from {request.META.get('REMOTE_ADDR', 'unknown')}")
        
        serializer = AgentQuerySerializer(data=request.data)
        
        if not serializer.is_valid():
            logger.warning(f"❌ Invalid request data: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user_prompt = serializer.validated_data['prompt']
        thread_id = serializer.validated_data.get('thread_id', '1')
        
        logger.info(f"🎯 Processing query for thread {thread_id}")
        
        # Run async code in sync context
        async def run_query():
            agent = await self.get_agent()
            response = await agent.invoke(user_prompt, thread_id)
            return response
        
        try:
            response = asyncio.run(run_query())
            
            # Extract the final message
            final_message = response["messages"][-1].content if response.get("messages") else ""
            
            # Convert response to serializable format
            serializable_response = self._make_serializable(response)
            
            response_data = {
                'response': final_message,
                'thread_id': thread_id,
                'full_response': serializable_response
            }
            
            response_serializer = AgentResponseSerializer(data=response_data)
            if response_serializer.is_valid():
                logger.info("✅ Query completed successfully")
                return Response(response_serializer.data, status=status.HTTP_200_OK)
            else:
                logger.error(f"❌ Response serialization error: {response_serializer.errors}")
                # Return response anyway without full_response
                return Response({
                    'response': final_message,
                    'thread_id': thread_id
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"❌ Error processing query: {e}")
            logger.exception("Full traceback:")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AgentStructuredQueryView(APIView):
    """
    API endpoint for querying the financial agent with structured output.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._agent = None
    
    async def get_agent(self):
        """Get or create the agent instance."""
        if self._agent is None:
            self._agent = FinancialAgent(
                chart_url=settings.CHART_URL,
                model_name=settings.OPENAI_MODEL,
                max_context_tokens=settings.MAX_CONTEXT_TOKENS,
                max_summary_tokens=settings.MAX_SUMMARY_TOKENS,
                enable_yfinance=settings.ENABLE_YFINANCE,
                enable_tavily=settings.ENABLE_TAVILY,
            )
            await self._agent.initialize()
        return self._agent
    
    def post(self, request):
        """Handle POST request to query the agent with structured output."""
        logger.info(f"📥 Received structured query request from {request.META.get('REMOTE_ADDR', 'unknown')}")
        
        serializer = AgentQuerySerializer(data=request.data)
        
        if not serializer.is_valid():
            logger.warning(f"❌ Invalid request data: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user_prompt = serializer.validated_data['prompt']
        thread_id = serializer.validated_data.get('thread_id', '1')
        
        logger.info(f"🎯 Processing structured query for thread {thread_id}")
        
        # Run async code in sync context
        async def run_query():
            agent = await self.get_agent()
            response = await agent.invoke_structured(user_prompt, thread_id)
            return response
        
        try:
            structured_response = asyncio.run(run_query())
            
            response_data = {
                'user_output': structured_response.user_output,
                'insights_summary': structured_response.insights_summary,
                'charting_url': structured_response.charting_url,
                'thread_id': thread_id,
            }
            
            response_serializer = StructuredAgentResponseSerializer(data=response_data)
            if response_serializer.is_valid():
                logger.info("✅ Structured query completed successfully")
                return Response(response_serializer.data, status=status.HTTP_200_OK)
            else:
                logger.error(f"❌ Response serialization error: {response_serializer.errors}")
                return Response(response_serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"❌ Error processing structured query: {e}")
            logger.exception("Full traceback:")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class HealthCheckView(APIView):
    """
    Simple health check endpoint.
    """
    
    def get(self, request):
        """Handle GET request for health check."""
        return Response({'status': 'healthy'}, status=status.HTTP_200_OK)
