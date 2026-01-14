"""
Socratic Science Storyteller Agent
Educational AI agent for children using question-driven learning
Production-ready with multiple educational APIs and robust error handling
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import requests
from typing import Optional, Dict, Any, List
from functools import lru_cache

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Verify API key is loaded
if not os.getenv("GOOGLE_API_KEY"):
    logger.error("GOOGLE_API_KEY not found in .env file!")
else:
    logger.info("API key loaded successfully")


# ============================================================================
# AGENT METADATA
# ============================================================================

AGENT_NAME = "Socratic Science Storyteller"
AGENT_DESCRIPTION = """An interactive educational agent that helps children explore STEM 
topics through storytelling and Socratic questioning. Uses real data from NASA, Wikipedia, 
and educational databases to create engaging, age-appropriate learning experiences."""

AGENT_VERSION = "1.0.0"


# ============================================================================
# SYSTEM INSTRUCTIONS
# ============================================================================

SYSTEM_INSTRUCTIONS = """You are a Socratic Science Storyteller, an expert educational AI 
designed to help children and young learners explore science, technology, engineering, and 
medicine through interactive storytelling and question-driven learning.

🎯 YOUR MISSION:
Transform complex scientific concepts into engaging stories that spark curiosity and 
deep understanding in young minds.

📚 CORE TEACHING PRINCIPLES:

1. **Storytelling First**
   - Every concept becomes an adventure with characters and plot
   - Use narrative arcs: setup, challenge, discovery, resolution
   - Make abstract ideas concrete through relatable scenarios
   - Example: "Imagine you're a tiny explorer traveling through a human body..."

2. **Socratic Method**
   - Guide discovery through thoughtful questions, not direct answers
   - Ask "What do you think...?" before explaining
   - Build on their responses with follow-up questions
   - Celebrate their thinking process, not just correct answers
   - If stuck, provide hints through smaller questions

3. **Age-Appropriate Adaptation**
   - ALWAYS ask the child's age first if not provided
   - Ages 5-7: Simple metaphors, basic concepts, lots of imagery
   - Ages 8-10: More detail, introduce scientific vocabulary, cause-effect
   - Ages 11-13: Complex systems, multiple perspectives, critical thinking
   - Ages 14+: Abstract concepts, real-world applications, ethical dimensions

4. **Data-Driven Learning**
   - When you have access to real data (NASA images, Wikipedia facts, animal data), 
     integrate it naturally into stories
   - Cite sources simply: "Scientists at NASA discovered..." or "Did you know that..."
   - Use specific facts to make stories more vivid and memorable

5. **Safety & Trust**
   - Only educational content - no medical diagnosis or dangerous experiments
   - Age-appropriate complexity and vocabulary
   - Redirect inappropriate topics gently to related educational content
   - Build confidence through encouragement

🎨 YOUR COMMUNICATION STYLE:

**Tone**: Warm, enthusiastic, encouraging (like a favorite teacher or mentor)
**Language**: Clear and simple, but never condescending
**Structure**: 
- Start with context and connection
- Present information through story or analogy
- End with an engaging question to continue learning

**Example Flow**:
Child: "Why is the sky blue?"
You: "Great question! Before I tell you a story about it, how old are you? That helps me 
make the story just right for you! While you're thinking, imagine you're a detective trying 
to solve the mystery of the blue sky. What clues might you look for?"

🔬 TOPICS YOU EXCEL AT:

**Space & Astronomy**: Planets, stars, black holes, space exploration (with NASA data)
**Biology**: Human body, animals, plants, ecosystems, evolution
**Physics**: Forces, energy, light, sound, motion, electricity
**Chemistry**: Elements, reactions, states of matter, atoms
**Medicine**: How the body works, diseases, treatments (explain, don't diagnose)
**Technology**: Computers, robots, AI, engineering, inventions
**Environment**: Climate, conservation, renewable energy, sustainability

🛡️ SAFETY GUARDRAILS:

✓ Educational content only
✓ No medical advice or diagnosis
✓ No instructions for dangerous experiments
✓ No explicit or inappropriate content
✓ If asked something inappropriate, respond: "That's an interesting question, but I think 
  we can explore something even more fascinating about [related safe topic]. Let me tell 
  you a story about..."

💡 SPECIAL FEATURES:

- **Multi-modal learning**: Describe visuals when discussing images or diagrams
- **Curiosity loops**: Each answer should spark a new question
- **Real-world connections**: Link concepts to everyday experiences
- **Growth mindset**: Praise effort and thinking, not just correctness
- **Cultural awareness**: Use diverse examples and perspectives

Remember: You're not just teaching facts—you're building lifelong learners who love asking 
"why" and "how." Every interaction should leave them more curious than when they started!"""


# ============================================================================
# EDUCATIONAL API TOOLS
# ============================================================================

@lru_cache(maxsize=100)
def search_nasa_images(query: str) -> Optional[Dict[str, Any]]:
    """
    Search NASA Image and Video Library for space-related educational content.
    Results are cached to avoid repeated API calls.
    
    Args:
        query: Search term (e.g., "mars rover", "jupiter")
    
    Returns:
        Dict with title, description, date, keywords, or None if error
    """
    try:
        logger.info(f"Searching NASA API for: {query}")
        url = "https://images-api.nasa.gov/search"
        params = {
            "q": query,
            "media_type": "image",
            "year_start": "2015"  # Recent images only
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        items = data.get('collection', {}).get('items', [])
        
        if items:
            # Get the first (most relevant) result
            first_item = items[0]
            item_data = first_item.get('data', [{}])[0]
            
            result = {
                "title": item_data.get('title', 'Untitled'),
                "description": item_data.get('description', '')[:500],  # Limit length
                "date": item_data.get('date_created', 'Unknown date'),
                "keywords": item_data.get('keywords', [])[:8],
                "source": "NASA Image Library"
            }
            
            logger.info(f"NASA API success: Found '{result['title']}'")
            return result
        else:
            logger.warning(f"NASA API: No results for '{query}'")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"NASA API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in NASA search: {e}")
        return None


@lru_cache(maxsize=100)
def search_wikipedia_summary(topic: str) -> Optional[str]:
    """
    Get a simplified summary from Wikipedia.
    Results are cached to avoid repeated API calls.
    
    Args:
        topic: Topic to search (e.g., "photosynthesis", "albert einstein")
    
    Returns:
        Summary text (max 500 chars), or None if error
    """
    try:
        logger.info(f"Searching Wikipedia for: {topic}")
        # Clean up the topic for URL
        topic_clean = topic.strip().replace(" ", "_")
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic_clean}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        extract = data.get('extract', '')
        
        if extract:
            # Limit to 500 characters for children
            if len(extract) > 500:
                extract = extract[:500].rsplit('.', 1)[0] + '.'  # Cut at sentence boundary
            
            logger.info(f"Wikipedia API success: Found summary for '{topic}'")
            return extract
        else:
            logger.warning(f"Wikipedia API: No summary for '{topic}'")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Wikipedia API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in Wikipedia search: {e}")
        return None


@lru_cache(maxsize=50)
def get_animal_facts(animal_name: str) -> Optional[Dict[str, Any]]:
    """
    Get scientific facts about animals from educational API.
    Results are cached to avoid repeated API calls.
    
    Args:
        animal_name: Name of animal (e.g., "lion", "elephant")
    
    Returns:
        Dict with name, locations, characteristics, or None if error
    """
    try:
        logger.info(f"Searching animal database for: {animal_name}")
        url = f"https://api.api-ninjas.com/v1/animals?name={animal_name}"
        
        # Note: This API has a free tier with limited requests
        # For production, you might want to add an API key
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data and len(data) > 0:
            animal = data[0]
            result = {
                "name": animal.get('name', animal_name),
                "locations": animal.get('locations', []),
                "characteristics": animal.get('characteristics', {}),
                "source": "Animal Science Database"
            }
            
            logger.info(f"Animal API success: Found data for '{animal_name}'")
            return result
        else:
            logger.warning(f"Animal API: No data for '{animal_name}'")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Animal API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in animal search: {e}")
        return None


def enrich_message_with_data(message: str) -> Dict[str, Any]:
    """
    Analyze the user's message and fetch relevant educational data.
    This enriches the AI's response with real facts.
    
    Args:
        message: User's input message
    
    Returns:
        Dict containing original message and fetched context data
    """
    context = {
        "sources_used": [],
        "data": {}
    }
    
    message_lower = message.lower()
    
    # Detect space/astronomy topics
    space_keywords = ["space", "planet", "star", "moon", "mars", "jupiter", "saturn", 
                      "neptune", "uranus", "venus", "mercury", "sun", "solar system",
                      "astronaut", "rocket", "nasa", "telescope", "galaxy", "comet", 
                      "asteroid", "black hole"]
    
    if any(keyword in message_lower for keyword in space_keywords):
        logger.info("Space topic detected")
        nasa_data = search_nasa_images(message)
        if nasa_data:
            context["sources_used"].append("NASA")
            context["data"]["nasa"] = nasa_data
    
    # Detect animal topics
    animal_keywords = ["animal", "lion", "elephant", "tiger", "bear", "wolf", "dog", 
                      "cat", "bird", "eagle", "penguin", "whale", "dolphin", "shark",
                      "snake", "lizard", "frog", "butterfly", "bee"]
    
    detected_animal = None
    for keyword in animal_keywords:
        if keyword in message_lower:
            detected_animal = keyword
            break
    
    if detected_animal:
        logger.info(f"Animal topic detected: {detected_animal}")
        animal_data = get_animal_facts(detected_animal)
        if animal_data:
            context["sources_used"].append("Animal Database")
            context["data"]["animal"] = animal_data
    
    # For most topics, try Wikipedia as general knowledge source
    if not context["sources_used"]:  # Only if no other sources found
        # Extract potential topic (simple heuristic)
        words = message.split()
        if len(words) >= 2:
            potential_topic = " ".join(words[:3])  # First 3 words
            wiki_data = search_wikipedia_summary(potential_topic)
            if wiki_data:
                context["sources_used"].append("Wikipedia")
                context["data"]["wikipedia"] = wiki_data
    
    return {
        "original_message": message,
        "context": context
    }


# ============================================================================
# AGENT CONFIGURATION
# ============================================================================

# Model configuration
MODEL_NAME = os.getenv("ROOT_AGENT_MODEL", "gemini-2.0-flash-exp")

# Generation parameters - optimized for creative but accurate educational content
generation_config = {
    "temperature": 0.8,  # Creative storytelling but controlled
    "top_p": 0.95,       # Diverse vocabulary
    "top_k": 40,         # Reasonable randomness
    "max_output_tokens": 2000,  # Longer for rich stories
    "candidate_count": 1
}

# Safety settings - Extra strict for children's content
safety_settings = [
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_LOW_AND_ABOVE"  # Strictest setting for children
    },
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    }
]

# Root agent configuration - this is what ADK uses
root_agent = {
    "model": MODEL_NAME,
    "system_instruction": SYSTEM_INSTRUCTIONS,
    "generation_config": generation_config,
    "safety_settings": safety_settings
}


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'root_agent',
    'AGENT_NAME',
    'AGENT_DESCRIPTION',
    'AGENT_VERSION',
    'enrich_message_with_data',
    'search_nasa_images',
    'search_wikipedia_summary',
    'get_animal_facts'
]


# Log agent initialization
logger.info(f"✓ {AGENT_NAME} v{AGENT_VERSION} initialized successfully")
logger.info(f"✓ Model: {MODEL_NAME}")
logger.info(f"✓ Educational APIs: NASA, Wikipedia, Animal Database")