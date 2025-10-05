"""
Serializers for the agent API.
"""
from rest_framework import serializers
import json


class AgentQuerySerializer(serializers.Serializer):
    """Serializer for agent query requests."""
    prompt = serializers.CharField(required=True, help_text="The user's query prompt")
    thread_id = serializers.CharField(required=False, default="1", help_text="Thread ID for conversation context")


class AgentResponseSerializer(serializers.Serializer):
    """Serializer for agent responses."""
    response = serializers.CharField(help_text="The agent's response")
    thread_id = serializers.CharField(help_text="Thread ID used for this query")
    full_response = serializers.JSONField(required=False, help_text="Full response data from agent")
    
    def validate_full_response(self, value):
        """Allow full_response to be any type - dict, list, or string"""
        if value is None:
            return value
        # If it's already a dict or list, return as is
        if isinstance(value, (dict, list)):
            return value
        # If it's a string, try to parse it as JSON, otherwise return the string
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return {"raw": value}
        return value


class StructuredAgentResponseSerializer(serializers.Serializer):
    """Serializer for structured agent responses."""
    user_output = serializers.CharField(help_text="Main response to the user")
    insights_summary = serializers.CharField(required=False, allow_null=True, help_text="Key insights or analysis")
    charting_url = serializers.CharField(required=False, allow_null=True, help_text="Chart URL if generated")
    thread_id = serializers.CharField(help_text="Thread ID used for this query")
