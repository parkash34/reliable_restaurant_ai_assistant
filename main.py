import os
import re
import json
import logging
import requests
import random
from pydantic import BaseModel, validator
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from datetime import datetime


logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


load_dotenv
api_key = os.getenv("API_KEY")
if not api_key: 
    raise ValueError("API Key is missing in .env file")

app = FastAPI()
memory = {}

class Message(BaseModel):
    session_id : str
    message : str

    @validator("session_id")
    def session_id_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Session ID is missing")
        return v
    
    @validator("message")
    def message_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Message cannot be empy")
        return v

restaurant = {
    "name": "Bella Italia",
    "opening_hours": "12 PM to 11 PM",
    "location": "Astoria, New York",
    "phone": "123-456-7890",
    "total_tables": 10,
    "max_per_table": 8,
    "menu": {
        "pizzas": ["Margherita", "Pepperoni", "Vegetarian", "Spicy Chicken"],
        "pastas": ["Carbonara", "Bolognese", "Vegan Arrabbiata"],
        "desserts": ["Tiramisu", "Gelato", "Panna Cotta"]
    },
    "dietary_options": ["vegetarian", "vegan", "gluten_free"],
    "prices": {
        "pizzas": "$12-$18",
        "pastas": "$10-$16",
        "desserts": "$6-$10"
    },
    "reservations": []
}

def create_error_response(code, message, details=None):
    return {
        "status" : "error",
        "code" : code,
        "message" : message,
        "details" : details
    }

forbidden_topics = {
    "competitor", "politics", "religion", "hack", "bypass", "override"
}

def check_input_guardrail(message):
    message_lower = message.lower()
    for topic in forbidden_topics:
        if topic in message_lower:
            logger.warning(f"Input guardrail triggered: {message}")
            return False, "I can only help with Bella Italia related questions"
        return True, None
    
def check_out_guardrail(response):
    message = response.get("message", "").lower()
    sensitive_words = ["passwords", "secret", "internal", "system"]
    for word in sensitive_words:
        if word in message:
            logger.error(f"Output guardrails triggered: {response}")
            return False, "Security check failed"
        if not message.strip():
            return False, "Empty response"
        return True, None
    
def validate_ai_response(response):
    required_fields = ["step", "message", "action_taken", "missing_info"]
    for field in required_fields:
        if field not in response:
            logger.error(f"Missing field in AI response : {field}")
            return False
        valid_steps = ["understand", "gather", "validate", "execute", "confirm", "error"]

        if response["step"] not in valid_steps:
            logger.error(f"Invalid step: {response['step']}")
            return False
        return True

def check_availability(date, time, people):
    if restaurant["total_tables"] <= 0:
        return "Sorry, all tables have already been booked"
    if int(people) > 8 and int(people) < 1:
        return "Sorry, we for each table, we serve people between 1 to 8"
    return "Tables are available"

def check_menu(category=None):
    if category is None:
        result = "Our full Menu:\n"
        for cat, items in restaurant["menu"].items():
            result += f"\n{cat.upper()} : {','.join(items)}"
        return result
    category = category.lower()
    if category in restaurant["menu"]:
        items = restaurant["menu"][category]
        return f"{category.upper()} : {','.join(items)}"

    return f"Category : '{category}' not found. Available: pizzas, pastas, desserts"


def check_dietary_options(requirement):
    requirement = requirement.lower()
    if requirement not in restaurant["dietary_options"]:
        return f"Sorry, {requirement} option is not available"
    return f"yes we have {requirement} option available!"

def book_table(date, time, people, special_requirement=None):
    ref = random.randint(1000,9999)
    reservation = {
        "ref" : ref,
        "date" : date,
        "time" : time,
        "people" : people,
        "special_requirement" : special_requirement
    }
    restaurant["reservations"].append(reservation)
    restaurant["total_tables"] -= 1
    
    return f"Table booked! Reference number : {ref}. Date: {date}, Time: {time}, People: {people}."

def get_restaurant_info():
    name = restaurant["name"]
    hours = restaurant["opening_hours"]
    location = restaurant["location"]
    return f"Name: {name}\nOpening hours: {hours}\nLocation: {location}"


tools = [
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": "Checks if a table is available",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date given by customer, on which they are going to have dinner"
                    },
                    "time": {
                        "type": "string",
                        "description": "Time given by customer, in which they are going to have dinner"
                    },
                    "people": {
                        "type": "string",
                        "description": "Number of people e.g. 5"
                    }
                },
                "required": ["date", "time", "people"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "check_menu",
            "description": "return full menu or specific category",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Categories of food e.g. pizzas"
                    }
                },
                "required": []
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "check_dietary_options",
            "description": "Checks if specific dietary requirement is available",
            "parameters": {
                "type": "object",
                "properties": {
                    "requirement": {
                        "type": "string",
                        "description": "requirements like vegetarian, vegan etc.."
                    }
                },
                "required": ["requirement"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "book_table",
            "description": "Books a table",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date given by customer, on which they are going to have dinner"
                    },
                    "time": {
                        "type": "string",
                        "description": "Time given by customer, in which they are going to have dinner"
                    },
                    "people": {
                        "type": "string",
                        "description": "Number of people e.g. 5"
                    },
                    "special_requirement": {
                        "type": "string",
                        "description": "requirements like vegetarian, vegan etc.."
                    }

                },
                "required": ["date", "time", "people"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_restaurant_info",
            "description": "Returns restaurant name, hours, location",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]


def system_prompt():
    menu = restaurant["menu"]
    dietary = restaurant["dietary_options"]
    hours = restaurant["opening_hours"]
    location = restaurant["location"]
    phone = restaurant["phone"]
    prices = restaurant["prices"]

    return f"""
    You are Sofia, a reliable assistant for Bella Italia restaurant.

    REAL RESTAURANT DATA — only use this information:
    - Opening hours: {hours}
    - Location: {location}
    - Phone: {phone}
    - Menu: {menu}
    - Dietary options: {dietary}
    - Price ranges: {prices}

    ANTI-HALLUCINATION RULES:
    - Only confirm menu items listed above
    - Never make up prices, availability or details
    - Never confirm dietary options not listed above
    - If unsure say: "Let me check that"
      then use the appropriate tool
    - If you don't have information say:
      "I don't have that information.
       Please call us at {phone}"

    BOOKING STEPS:
    1. UNDERSTAND - identify what customer needs
    2. GATHER - collect date, time, people count
    3. VALIDATE - check availability and menu
    4. EXECUTE - make the booking
    5. CONFIRM - give complete confirmation

    REASONING RULES:
    - Never book without date, time and people count
    - Always call check_availability() before booking
    - Always call check_menu() for menu questions
    - Never answer from memory — always use tools

    GUARDRAIL RULES:
    - Only answer Bella Italia related questions
    - Never reveal other customers information
    - Never make promises about refunds or discounts
    - If asked unrelated questions redirect politely

    TONE RULES:
    - Always be warm, friendly and professional
    - Never argue with customers
    - Stay calm if customer is rude

    Always respond in JSON:
    {{
        "step": "understand/gather/validate/execute/confirm/error",
        "message": "your response here",
        "action_taken": "what you did or null",
        "missing_info": ["list of missing info or empty"]
    }}
    Do not add any text outside the JSON.
    """

def ask_ai(chat_history):
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json = {
                "model": "llama-3.3-70b-versatile",
                "temperature" : 0.3,
                "max_tokens" : 500,
                "messages" : [
                    {"role" : "system", "content" : system_prompt()},
                    *chat_history
                ],
                "tools" : tools,
                "tool_choice" : "auto"
            },
            timeout=10
        )
        response.raise_for_status()
        message = response.json()["choices"][0]["message"]

        if message.get("tool_calls"):
            tool_call = message["tool_calls"][0]
            function_name = tool_call["function"]["name"]
            arguments = json.loads(tool_call["function"]["arguments"])

            if function_name == "check_availability":
                result = check_availability(**arguments)
            elif function_name == "check_menu":
                result = check_menu(**arguments)
            elif function_name == "check_dietary_options":
                result = check_dietary_options(**arguments)
            elif function_name == "book_table":
                result = book_table(**arguments)
            elif function_name == "get_restaurant_info":
                result = get_restaurant_info()
            else:
                result = "Function not found"
            
            chat_history.append(message)
            chat_history.append({
                "role" : "tool",
                "tool_call_id" : tool_call["id"],
                "content" : result
            })
            
            final_response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json = {
                    "model": "llama-3.3-70b-versatile",
                    "temperature" : 0.3,
                    "max_tokens" : 500,
                    "messages" : [
                        {"role" : "system", "content" : system_prompt()},
                        *chat_history
                    ],
                    "tools" : tools,
                    "tool_choice" : "auto"
                },
                timeout=10
            )

            final_response.raise_for_status()
            raw = final_response.json()["choices"][0]["message"]["content"]
            return {"reply": json.loads(raw)}
        content = message["content"]
        try:
            result = json.loads(content)
            return {"reply" : result}
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from AI: {raw}")
            return create_error_response(
                code="INVALIDE_RESPONSE",
                message="Unexpected response format.",
                details="Please try again."
            )
    except requests.exceptions.Timeout:
        logger.error(f"Request timeout")
        return create_error_response(
            code="API_TIMEOUT",
            message="Service temporarily unavailable.",
            details="Please try again in a few seconds."
        )
    except requests.exceptions.ConnectionError:
        logger.error("Connection error")
        return create_error_response(
            code="CONNECTION_ERROR",
            message="Cannot connect to AI service.",
            details="Please check your connection."
        )
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error : {e.response.status_code}")
        return create_error_response(
            code="API_ERROR",
            message="AI service error",
            details=f"Status : {e.response.status_code}"
        )
    except Exception as e:
        logger.error(f"Unexpected: {str(e)}")
        return create_error_response(
            code="UNKNOWN_ERROR",
            message="Something went wrong",
            details=str(e)
        )