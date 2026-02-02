import os
import random
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from utils.logger import get_logger
from config import settings

logger = get_logger(__name__)

# Chat history
_history = []

# Cached safe answers for fallback when LLM fails
SAFE_ANSWERS = [
    "I'm having a bit of trouble right now. Could you try asking again?",
    "Sorry, I couldn't process that properly. Can you rephrase your question?",
    "I'm experiencing some technical difficulties. Please try again in a moment.",
    "Hmm, something went wrong on my end. Could you repeat that?",
    "I apologize, but I'm having trouble responding right now. Please try again.",
]


def clear_history():
    global _history
    _history = []


def get_history():
    return _history.copy()


async def generate(message: str) -> str:
    global _history
    
    if not message or not message.strip():
        raise ValueError("Message cannot be empty")
    
    llm = ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        temperature=0.7,
        max_tokens=256
    )
    
    # Build messages
    messages = [SystemMessage(content=settings.system_prompt)]
    messages.extend(_history)
    messages.append(HumanMessage(content=message))
    
    try:
        response = await llm.ainvoke(messages)
        reply = response.content.strip()
        
        # Update history
        _history.append(HumanMessage(content=message))
        _history.append(AIMessage(content=reply))
        
        # Keep history short
        if len(_history) > 20:
            _history = _history[-20:]
        
        logger.info(f"Generated: '{reply[:50]}...'")
        return reply
        
    except Exception as e:
        logger.error(f"LLM error: {e}, using cached safe answer")
        # Return a cached safe answer instead of failing
        return random.choice(SAFE_ANSWERS)
