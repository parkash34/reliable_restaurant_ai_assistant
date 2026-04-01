# SafeGuard — Reliable Restaurant AI Assistant

A production-ready AI restaurant assistant built with FastAPI and Groq AI.
SafeGuard focuses on reliability, safety and accuracy through hallucination
control, multi-layer validation, prompt guardrails and professional error handling.

## Features

- Hallucination control — real restaurant data injected into system prompt
- Multi-layer validation — Pydantic, function level and output validation
- Input guardrails — blocks forbidden topics and suspicious requests
- Output guardrails — prevents sensitive data leakage
- Professional error handling — structured errors with logging
- Multi-step booking — 5 step reasoning process
- Session memory — each customer has separate conversation history
- Structured JSON responses — consistent format for all replies

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| FastAPI | Backend web framework |
| Groq API | AI language model provider |
| LLaMA 3.3 70B | AI model |
| Pydantic | Data validation with custom validators |
| python-dotenv | Environment variable management |
| logging | Professional error logging |

## Project Structure
```
safeguard/
│
├── env/               
├── main.py            
├── .env               
└── requirements.txt   
```

## Setup

1. Clone the repository
```
git clone https://github.com/yourusername/safeguard
```

2. Create and activate virtual environment
```
python -m venv env
env\Scripts\activate
```

3. Install dependencies
```
pip install -r requirements.txt
```

4. Create `.env` file and add your Groq API key
```
API_KEY=your_groq_api_key_here
```

5. Run the server
```
uvicorn main:app --reload
```

## API Endpoint

### POST /book

**Request:**
```json
{
    "session_id": "user_1",
    "message": "I want to book a table for 4 tonight at 7 PM"
}
```

**Response:**
```json
{
    "reply": {
        "step": "confirm",
        "message": "Your table for 4 is booked at 7 PM tonight!",
        "action_taken": "booked table",
        "missing_info": []
    }
}
```

**Error Response:**
```json
{
    "status": "error",
    "code": "API_TIMEOUT",
    "message": "Service temporarily unavailable.",
    "details": "Please try again in a few seconds."
}
```

## Reliability Features

### Hallucination Control
Real restaurant data is injected directly into the system prompt.
The AI only answers based on provided data and admits uncertainty
instead of making up information.

### Validation Layers
- Pydantic validators — empty session ID and message rejected automatically
- Function level — people count validated between 1 and 8
- Output validation — AI response structure verified before returning
- Output guardrails — sensitive words blocked from responses

### Guardrails
- Input guardrails — forbidden topics blocked before reaching AI
- Prompt guardrails — strict rules in system prompt for topic and tone
- Output guardrails — response checked for sensitive information

### Error Handling
- Structured error responses with error codes
- Full logging with timestamps for all errors
- Graceful handling of timeouts, connection errors and API failures

## Booking Flow
```
User sends message
↓
Input guardrail check
↓
AI follows 5 step process:
1. UNDERSTAND — identify request
2. GATHER — collect date, time, people
3. VALIDATE — check availability
4. EXECUTE — book the table
5. CONFIRM — send confirmation
↓
Output validation and guardrail check
↓
Structured JSON response returned
```

## Available Tools

| Tool | Description |
|---|---|
| `check_availability` | Checks table availability |
| `check_menu` | Returns full menu or category |
| `check_dietary_options` | Checks dietary requirements |
| `book_table` | Books a table with reference number |
| `get_restaurant_info` | Returns restaurant details |

## Environment Variables
```
API_KEY=your_groq_api_key_here
```

## Notes

- Never commit your .env file to GitHub
- Conversation history resets when server restarts
- Assistant only handles Bella Italia related questions

## 👤 Author

**Ohm Parkash** — [LinkedIn](https://www.linkedin.com/in/om-parkash34/) · [GitHub](https://github.com/parkash34)





