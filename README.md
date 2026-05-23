# Blog App

A polished Flask-based blogging platform with authentication, markdown authoring, tags, comments, likes, bookmarks, and admin analytics.

## Features

- User authentication with role support (`reader`, `author`, `admin`)
- Markdown editor with live preview
- Image uploads for post thumbnails
- Tags and search filtering
- Comments with nested replies
- Like and bookmark support
- Post views tracking
- Admin analytics dashboard
- REST-style JSON endpoints for posts
- Rate limiting on auth routes
- Environment-based configuration via `.env`
- Docker + Docker Compose support
- GitHub Actions CI with tests

## Tech Stack

- Python 3
- Flask
- Flask-Login
- Flask-WTF
- Flask-SQLAlchemy
- Flask-Limiter
- Flask-Mail
- SQLite (development)
- Bootstrap 5
- Chart.js
- Markdown preview via marked.js

## Setup

1. Copy the example configuration:

   ```bash
   copy .env.example .env
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:

   ```bash
   python run.py
   ```

4. Visit `http://127.0.0.1:5000`

## Docker

Build and run with Docker:

```bash
docker compose up --build
```

## Testing

Run the test suite:

```bash
pytest
```

## API Endpoints

- `GET /api/posts` — list latest posts
- `GET /api/posts/<post_id>` — post detail

## Notes

- Use `.env` to store secrets and mail settings.
- Images are saved to `static/uploads`.
- The admin dashboard is available for users with `admin` role.
