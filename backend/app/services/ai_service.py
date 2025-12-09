"""
AI Assistant Service using Google Gemini 2.5 Flash

This service provides AI-powered guidance to help users think through
coding problems without giving direct solutions.
"""

import os
from typing import Optional
import google.generativeai as genai


class AIAssistantService:
    """Service for AI-powered coding guidance using Gemini 2.5 Flash."""

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
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-preview-05-20",
            system_instruction=self.SYSTEM_PROMPT
        )

    def get_guidance(
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
            response = self.model.generate_content(full_prompt)
            return response.text.strip()
        except Exception as e:
            return f"I'm having trouble connecting right now. Please try again in a moment. (Error: {str(e)[:50]})"


# Singleton instance (lazy initialization)
_ai_service: Optional[AIAssistantService] = None


def get_ai_service() -> AIAssistantService:
    """Get or create the AI service singleton."""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIAssistantService()
    return _ai_service
