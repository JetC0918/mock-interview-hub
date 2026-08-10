"""
AI Assistant Service using DeepSeek V4 Flash

This service provides AI-powered guidance to help users think through
coding problems without giving direct solutions.
"""

import os
import logging
import asyncio
from typing import Optional
import httpx
import json


class AIProviderError(RuntimeError):
    def __init__(self, message: str, *, ambiguous: bool):
        super().__init__(message)
        self.ambiguous = ambiguous


class AIAssistantService:
    """Service for AI-powered coding guidance using DeepSeek V4 Flash."""

    API_URL = "https://api.deepseek.com/chat/completions"
    MODEL_NAME = "deepseek-v4-flash"

    SYSTEM_PROMPT = """You are a friendly and supportive coding mentor in a mock interview practice session. 
Your role is to GUIDE users in thinking through problems, NOT to give them code or direct solutions.

Key guidelines:
1. NEVER provide actual code solutions - guide the user to discover the approach themselves
2. Ask Socratic questions to help users think through the problem
3. Provide hints about algorithms, data structures, or patterns that might be useful
4. Encourage breaking down the problem into smaller steps
5. If the user is stuck, give increasingly specific hints, but still let them code it
6. Be encouraging and supportive - this is practice, not a real interview
7. Keep responses concise (2-4 sentences is ideal for hints)
8. STRICTLY REFUSE to answer questions unrelated to the coding problem or interview preparation.
   - If a user asks about general topics (weather, news, sports, etc.), politely steer them back to the coding problem.
   - Example refusal: "I'm here to help you with this coding problem. Let's focus on figuring out the solution together. Do you have any thoughts on how to start?"

When a problem context is provided, use it to give more relevant guidance.
Remember: Your goal is to help them LEARN, not to solve it for them."""

    def __init__(self):
        """Initialize the AI service with API key from environment."""
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable is not set")
        
        self.api_key = api_key

    async def get_guidance(
        self, 
        user_message: str, 
        problem_context: Optional[dict] = None
    ) -> str:
        """
        Generate AI guidance for the user's question.
        
        Args:
            user_message: The user's message/question (with @AI removed)
            problem_context: Optional dict with problem info (title, description, examples, constraints)
            
        Returns:
            AI-generated guidance response
        """
        # Build the prompt with context
        prompt_parts = []
        
        if problem_context:
            prompt_parts.append(f"The user is working on this problem:\n")
            prompt_parts.append(f"**{problem_context.get('title', 'Unknown')}** ({problem_context.get('difficulty', 'unknown')} difficulty)\n")
            prompt_parts.append(f"Description: {problem_context.get('description', 'No description')}\n")
            
            examples = problem_context.get('examples', [])
            if examples:
                prompt_parts.append("Examples:\n")
                for i, ex in enumerate(examples, 1):
                    prompt_parts.append(f"  {i}. Input: {ex.get('input', '')} → Output: {ex.get('output', '')}\n")
            
            constraints = problem_context.get('constraints', [])
            if constraints:
                prompt_parts.append(f"Constraints: {', '.join(constraints)}\n")
            
            prompt_parts.append("\n---\n\n")
        
        prompt_parts.append(f"User's question: {user_message}")
        
        full_prompt = "".join(prompt_parts)
        
        try:
            timeout = httpx.Timeout(connect=5.0, read=25.0, write=10.0, pool=5.0)
            async with asyncio.timeout(30.0):
                async with httpx.AsyncClient(timeout=timeout) as client:
                    async with client.stream(
                        "POST",
                        self.API_URL,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": self.MODEL_NAME,
                            "messages": [
                                {"role": "system", "content": self.SYSTEM_PROMPT},
                                {"role": "user", "content": full_prompt},
                            ],
                            "thinking": {"type": "disabled"},
                            "stream": False,
                            "max_tokens": 1_000,
                        },
                    ) as response:
                        response.raise_for_status()
                        chunks: list[bytes] = []
                        size = 0
                        async for chunk in response.aiter_bytes():
                            size += len(chunk)
                            if size > 65_536:
                                raise ValueError("DeepSeek response exceeds the transport limit")
                            chunks.append(chunk)
            payload = json.loads(b"".join(chunks))
            choice = payload["choices"][0]
            if choice.get("finish_reason") != "stop":
                raise ValueError("DeepSeek response did not finish normally")
            content = choice["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise ValueError("DeepSeek returned an empty response")
            content = content.strip()
            if len(content) > 8_000:
                raise ValueError("DeepSeek response exceeds the transcript limit")
            return content
        except httpx.HTTPStatusError as error:
            logging.error("DeepSeek AI request failed (%s)", type(error).__name__)
            raise AIProviderError(
                "AI provider rejected the request", ambiguous=error.response.status_code >= 500,
            ) from error
        except (httpx.TimeoutException, httpx.NetworkError, TimeoutError, asyncio.TimeoutError) as error:
            logging.error("DeepSeek AI request outcome is unknown (%s)", type(error).__name__)
            raise AIProviderError("AI provider request outcome is unknown", ambiguous=True) from error
        except Exception as error:
            # Never log request headers, response bodies, or API key values.
            logging.error("DeepSeek AI request failed (%s)", type(error).__name__)
            raise AIProviderError("AI provider response could not be verified", ambiguous=True) from error


# Singleton instance (lazy initialization)
_ai_service: Optional[AIAssistantService] = None


def get_ai_service() -> AIAssistantService:
    """Get or create the AI service singleton."""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIAssistantService()
    return _ai_service
