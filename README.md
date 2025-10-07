# MapleMetrics - Financial Agent Django Application

A Django-based financial analysis application using LangGraph ReAct agents with MCP tools.

## Features

- **Django REST API** for financial agent queries
- **LangGraph ReAct Agent** with multiple MCP tools:
  - Charting capabilities
  - Yahoo Finance integration
  - Tavily search integration
- **Structured and unstructured output** endpoints
- **Conversation threading** for context management

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` with your actual keys:
- `OPENAI_KEY`: Your OpenAI API key
- `TAVILY_API_KEY`: Your Tavily API key
- `DJANGO_SECRET_KEY`: Generate a secure secret key

### 3. Database Migration

```bash
python manage.py migrate
```

### 4. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 5. Run the Server

```bash
python manage.py runserver
```

The server will start at `http://localhost:8000`

## API Endpoints

### 1. Health Check
```
GET /api/agent/health/
```

### 2. Agent Query (Unstructured)
```
POST /api/agent/query/
Content-Type: application/json

{
  "prompt": "What is Apple's current stock price?",
  "thread_id": "user123"  // optional
}
```

### 3. Agent Query (Structured)
```
POST /api/agent/query/structured/
Content-Type: application/json

{
  "prompt": "Analyze Tesla's performance and create a chart",
  "thread_id": "user123"  // optional
}
```

Response includes:
- `user_output`: Main response
- `insights_summary`: Key insights (if available)
- `charting_url`: Chart URL (if generated)

## Example Usage

```python
import requests

# Query the agent
response = requests.post(
    'http://localhost:8000/api/agent/query/',
    json={
        'prompt': 'What is the current price of AAPL?',
        'thread_id': 'session1'
    }
)

print(response.json())
```

## Development

### Run Tests
```bash
python manage.py test
```

### Access Admin Panel
Navigate to `http://localhost:8000/admin/` after creating a superuser.

## Project Structure

```
maplemetrics/
├── manage.py
├── maplemetrics/          # Django project settings
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── agent/                 # Financial agent app
│   ├── __init__.py
│   ├── apps.py
│   ├── views.py
│   ├── urls.py
│   ├── serializers.py
│   ├── test_client.py    # Agent implementation
│   └── misc.py           # Helper utilities
├── requirements.txt
└── .env
```

## License

MIT
