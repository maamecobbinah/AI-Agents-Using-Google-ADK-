"""
Socratic Science Storyteller Agent
Educational AI agent for children using question-driven learning
Enhanced with multiple educational APIs
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import requests
from typing import Optional, Dict, Any, List

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Import ADK components
from google.generativeai.types import GenerationConfig, HarmCategory, HarmBlockThreshold


# Agent Configuration
AGENT_NAME = "socratic_storyteller_agent"
AGENT_DESCRIPTION = """A friendly science storyteller that helps children learn through 
interactive stories and Socratic questions. Uses real educational sources like NASA, 
Wikipedia, and science databases."""


# System Instructions
SYSTEM_INSTRUCTIONS = """You are a Socratic Science Storyteller designed to help children 
and young learners explore science, technology, and medicine through interactive storytelling 
and question-driven learning.

YOUR CORE PRINCIPLES:
1. **Storytelling First**: Turn scientific concepts into engaging stories with characters, 
   scenarios, and adventures
2. **Socratic Method**: Guide learning through thoughtful questions rather than direct answers
3. **Age-Appropriate**: Adapt complexity and vocabulary based on the child's age
4. **Safety First**: Only educational content, nothing explicit or inappropriate
5. **Encourage Curiosity**: Make children excited to explore and ask more questions

YOUR APPROACH:
- Start by asking the child's age or grade level (if not provided)
- When given a topic, create a short story or scenario around it
- Ask guiding questions that help them discover concepts themselves
- Use analogies and metaphors children can relate to
- Celebrate their thinking and encourage exploration
- If they're stuck, provide hints through smaller questions

YOU HAVE ACCESS TO THESE EDUCATIONAL SOURCES:
- NASA Image Library (for space, planets, astronomy)
- Wikipedia (for general science topics)
- Open Science APIs (for animals, nature, environment)

When you have access to real data from these sources, incorporate it naturally into 
your stories and explanations!

TONE AND STYLE:
- Warm, encouraging, and enthusiastic
- Use simple language but don't talk down to them
- Include fun elements: characters, adventures, "what if" scenarios
- End responses with an engaging question to continue the conversation

TOPICS YOU COVER:
- Space and astronomy (with NASA data)
- Human body and medicine
- Animals and nature
- Technology and engineering
- Physics and chemistry basics
- Environmental science
- Any STEM topic appropriate for children

SAFETY GUARDRAILS:
- Only educational content
- No medical advice (explain concepts, don't diagnose)
- No dangerous experiments
- Age-appropriate complexity
- If topic is inappropriate, gently redirect to a related educational topic

Remember: You're not just teaching—you're sparking a lifelong love of learning!"""


# ============================================================================
# EDUCATIONAL API TOOLS
# ============================================================================

def search_nasa_images(query: str) -> Optional[Dict[str, Any]]:
    """
    Search NASA Image and Video Library for space-related educational content.
    Free API, no authentication required.
    """
    try:
        url = "https://images-api.nasa.gov/search"
        params = {
            "q": query,
            "media_type": "image",
            "year_start": "2015"
        }
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            items = data.get('collection', {}).get('items', [])
            if items:
                first_item = items[0]
                item_data = first_item.get('data', [{}])[0]
                return {
                    "title": item_data.get('title', ''),
                    "description": item_data.get('description', '')[:300],  # Limit length
                    "date": item_data.get('date_created', ''),
                    "keywords": item_data.get('keywords', [])[:5],
                }
    except Exception as e:
        print(f"NASA API error: {e}")
    return None


def search_wikipedia_summary(topic: str) -> Optional[str]:
    """
    Get a simplified summary from Wikipedia.
    Uses the Wikipedia API - free, no authentication required.
    """
    try:
        url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + topic.replace(" ", "_")
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Get the extract (summary) - usually 1-2 paragraphs
            extract = data.get('extract', '')
            # Limit to first 400 characters for children
            if len(extract) > 400:
                extract = extract[:400] + "..."
            return extract
    except Exception as e:
        print(f"Wikipedia API error: {e}")
    return None


def get_animal_facts(animal_name: str) -> Optional[Dict[str, Any]]:
    """
    Get fun animal facts from a free animal API.
    Great for questions about animals and nature.
    """
    try:
        # Using the free Animal Facts API
        url = f"https://api.api-ninjas.com/v1/animals?name={animal_name}"
        # Note: This API has a free tier with limited requests
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                animal = data[0]
                return {
                    "name": animal.get('name', ''),
                    "locations": animal.get('locations', []),
                    "characteristics": animal.get('characteristics', {}),
                }
    except Exception as e:
        print(f"Animal API error: {e}")
    return None


def search_educational_content(topic: str, topic_type: str = "general") -> Dict[str, Any]:
    """
    Smart router that chooses the best API based on the topic.
    
    Args:
        topic: The subject to search for
        topic_type: "space", "animal", "general", etc.
    
    Returns:
        Combined results from relevant APIs
    """
    results = {
        "topic": topic,
        "sources": []
    }
    
    # Route to appropriate APIs based on topic type
    if topic_type == "space" or any(word in topic.lower() for word in ["space", "planet", "star", "moon", "mars", "nasa", "astronaut"]):
        nasa_data = search_nasa_images(topic)
        if nasa_data:
            results["sources"].append({
                "source": "NASA",
                "data": nasa_data
            })
    
    if topic_type == "animal" or any(word in topic.lower() for word in ["animal", "dog", "cat", "lion", "bird", "fish"]):
        animal_data = get_animal_facts(topic)
        if animal_data:
            results["sources"].append({
                "source": "Animal Database",
                "data": animal_data
            })
    
    # Always try Wikipedia as a fallback for general knowledge
    wiki_summary = search_wikipedia_summary(topic)
    if wiki_summary:
        results["sources"].append({
            "source": "Wikipedia",
            "data": {"summary": wiki_summary}
        })
    
    return results


# ============================================================================
# AGENT CONFIGURATION
# ============================================================================

generation_config = GenerationConfig(
    temperature=0.8,  # Creative but controlled
    top_p=0.95,
    top_k=40,
    max_output_tokens=1500,  # Increased for richer stories
    candidate_count=1,
)

# Safety Settings - Stricter for children
safety_settings = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}

# ADK Agent Definition
root_agent = {
    "model": os.getenv("ROOT_AGENT_MODEL", "gemini-2.0-flash-exp"),
    "system_instruction": SYSTEM_INSTRUCTIONS,
    "generation_config": generation_config,
    "safety_settings": safety_settings,
}


# ============================================================================
# SESSION LIFECYCLE HOOKS
# ============================================================================

def on_message(message: str, session_id: str) -> Dict[str, Any]:
    """
    Pre-process incoming messages and fetch relevant educational data.
    This enriches the conversation with real facts!
    """
    print(f"[Session {session_id}] Processing message: {message[:50]}...")
    
    # Detect topic and fetch relevant data
    context = {}
    
    # Check for space topics
    if any(word in message.lower() for word in ["space", "planet", "mars", "moon", "star", "astronaut", "rocket"]):
        print("  → Detected space topic, fetching NASA data...")
        nasa_data = search_nasa_images(message)
        if nasa_data:
            context["nasa_data"] = nasa_data
    
    # Check for animal topics
    if any(word in message.lower() for word in ["animal", "lion", "elephant", "dog", "cat", "bird"]):
        print("  → Detected animal topic, searching animal database...")
        # Extract animal name (simple approach)
        for word in ["lion", "elephant", "dog", "cat", "bird", "whale", "dolphin"]:
            if word in message.lower():
                animal_data = get_animal_facts(word)
                if animal_data:
                    context["animal_data"] = animal_data
                break
    
    return {
        "original_message": message,
        "context": context,
        "session_id": session_id
    }


def on_response(response: str, session_id: str) -> str:
    """
    Post-process responses for additional safety and formatting.
    """
    print(f"[Session {session_id}] Response generated successfully")
    
    # Optional: Add citation when educational sources were used
    # This teaches children about reliable sources
    
    return response


# Export what ADK needs
__all__ = [
    'root_agent', 
    'AGENT_NAME', 
    'AGENT_DESCRIPTION',
    'on_message',
    'on_response',
    'search_educational_content',  # Make available for testing
]