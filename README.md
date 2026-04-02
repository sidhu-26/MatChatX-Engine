# 🏏 MatChatX

**Real-time, ephemeral, match-based chat system** built with Django Channels + Redis.

Users join live match chat rooms without authentication, send messages via WebSockets, and all chat data automatically expires after the match ends.

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Django 6.0 |
| WebSockets | Django Channels (ASGI) |
| ASGI Server | Daphne |
| Message Broker | Redis (Pub/Sub + Channel Layer) |
| Chat Storage | Redis (ephemeral, auto-expiring) |
| Match Metadata | PostgreSQL |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL
- Redis

### Setup

```bash
# Clone and enter project
cd MatChatX

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env  # Edit with your credentials

# Create database
createdb MATCHATX

# Run migrations
python manage.py migrate

# Seed test data
python manage.py seed_matches

# Create a LIVE match for testing
python manage.py create_live_match

# Start the server (ASGI/Daphne)
daphne -b 0.0.0.0 -p 8000 core.asgi:application
```

---

## 📡 API Endpoints

### `GET /matches/live/`

Returns all currently LIVE matches.

**Response:**
```json
{
  "count": 1,
  "matches": [
    {
      "id": "da8d43ca-7752-4621-841c-aad4956f4c41",
      "team_1": "CSK",
      "team_2": "MI",
      "start_time": "2026-04-02T12:30:00+00:00",
      "end_time": "2026-04-02T15:30:00+00:00",
      "status": "LIVE",
      "display_name": "CSK vs MI"
    }
  ]
}
```

### `GET /api/health/`

Health check endpoint.

---

## 🔌 WebSocket Chat

### Connect

```
ws://localhost:8000/ws/chat/<match_id>/
```

### 1. Join (first message after connect)

```json
{
  "username": "Siddaarth",
  "team_supported": "CSK"
}
```

**Response — Chat History:**
```json
{
  "type": "chat_history",
  "messages": [...],
  "count": 5
}
```

### 2. Send Message

```json
{
  "username": "Siddaarth",
  "team": "CSK",
  "message": "Dhoni 🔥"
}
```

### 3. Receive Message (broadcast)

```json
{
  "type": "chat_message",
  "username": "Siddaarth",
  "team": "CSK",
  "message": "Dhoni 🔥",
  "timestamp": "2026-04-02T18:30:00+00:00"
}
```

### Error Responses

```json
{
  "type": "error",
  "code": "MATCH_CLOSED",
  "message": "Match is no longer live. Chat is closed."
}
```

Error codes: `INVALID_JSON`, `MISSING_USERNAME`, `MISSING_TEAM`, `EMPTY_MESSAGE`, `MESSAGE_TOO_LONG`, `RATE_LIMITED`, `MATCH_CLOSED`

---

## 🧪 Testing with wscat

```bash
# Install wscat
npm install -g wscat

# Connect to a live match
wscat -c ws://localhost:8000/ws/chat/<match_id>/

# Send join payload
> {"username": "Siddaarth", "team_supported": "CSK"}

# Send a message
> {"username": "Siddaarth", "team": "CSK", "message": "Dhoni 🔥"}
```

---

## 📁 Project Structure

```
MatChatX/
├── core/
│   ├── asgi.py          # ASGI config (HTTP + WebSocket routing)
│   ├── settings.py      # Redis + Channels + PostgreSQL config
│   ├── urls.py          # Root URL configuration
│   └── health.py        # Health check endpoint
├── matches/
│   ├── models.py        # Match model (PostgreSQL)
│   ├── views.py         # /matches/live/ API
│   ├── services.py      # Match lifecycle logic
│   ├── urls.py          # URL routing
│   └── management/
│       └── commands/
│           ├── seed_matches.py
│           ├── create_live_match.py
│           └── update_match_status.py
├── chat/
│   ├── consumers.py     # WebSocket consumer (full async)
│   ├── routing.py       # WebSocket URL routing
│   ├── services.py      # Redis service layer
│   └── validators.py    # Payload validation + profanity filter
├── .env                 # Environment variables
├── .gitignore
├── manage.py
└── requirements.txt
```

---

## ⚙️ Management Commands

| Command | Description |
|---------|-----------|
| `python manage.py seed_matches` | Seed IPL match fixtures |
| `python manage.py create_live_match` | Create a LIVE match for testing |
| `python manage.py update_match_status` | Manually trigger status transitions |

---

## 🔧 Configuration (.env)

| Variable | Default | Description |
|----------|---------|-----------|
| `SECRET_KEY` | - | Django secret key |
| `DEBUG` | `True` | Debug mode |
| `DB_NAME` | `MATCHATX` | PostgreSQL database name |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for chat storage |
| `CHANNEL_REDIS_URL` | `redis://localhost:6379/1` | Redis for channel layer |
| `CHAT_MAX_MESSAGES` | `15` | Max messages kept per match |
| `MATCH_BUFFER_MINUTES` | `30` | Buffer before/after match |
| `RATE_LIMIT_MESSAGES` | `10` | Max messages per window |
| `RATE_LIMIT_WINDOW_SECONDS` | `10` | Rate limit window |