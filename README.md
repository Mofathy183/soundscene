# 🎧 SoundScene

**Micro Podcast / Song Storytelling Platform**  
Share stories. Drop theories. Celebrate music — one voice clip at a time.

[![License](https://img.shields.io/github/license/Mofathy183/soundscene)](./LICENSE)
[![Build](https://img.shields.io/github/actions/workflow/status/Mofathy183/soundscene/ci.yml)](./.github/workflows/ci.yml)
[![Linting](https://img.shields.io/badge/code%20style-ruff-blue)](https://github.com/astral-sh/ruff)
[![Typing](https://img.shields.io/badge/typing-mypy-informational)](https://github.com/python/mypy)

---

## 🌟 Concept

> SoundScene is your social space for short-form audio.  
> Upload clips (≤2 minutes) to tell stories, drop fan theories, or review songs.  
> It’s like audio Twitter — made for entertainment lovers.

---

## 🔥 Key Features

- 🎙️ Upload voice notes or music snippets (up to 2 mins)
- ✍️ Add captions, genres, and tags
- ❤️ Like, 💬 comment, and 🔁 share content
- 📈 Discover trending or genre-specific content
- 🔍 Tag and genre-based content filtering

---

## 🧱 Tech Stack

### ✅ Backend – `Django + GraphQL + PostgreSQL`

| Tool | Description |
|------|-------------|
| **Django** | Core backend framework |
| **Graphene-Django** | For GraphQL APIs |
| **PostgreSQL** | Relational DB for structured data |
| **DRF (optional)** | For file upload/admin if needed |
| **django-storages + AWS S3 / Cloudinary** | Audio file hosting |
| **JWT Auth** | Auth via `django-graphql-jwt` |
| **UV** | Fast Python packaging (written in Rust) |
| **mypy** | Static typing and code quality |
| **ruff** | Fast Python linter & formatter |

#### 🧪 Dev Tools
- **uv** — dependency resolution & virtualenv in one
- **mypy** — static type checking
- **ruff** — linting & style enforcement

---

### ✅ Frontend – `Angular (v20+)`

| Tool | Description |
|------|-------------|
| **Angular** | SPA Framework |
| **Apollo Angular** | GraphQL client integration |
| **Ngx-Audio-Player** | Custom audio playback UI |
| **Drag-and-Drop Uploads** | For voice/music clip uploads |
| **Modular Components** | Reusable UI + service-based architecture |

---

## ⚙️ Project Structure (Monorepo Friendly)
```bash
soundscene/
│
├── .github/                  # GitHub Actions CI
│   └── workflows/
│       └── ci.yml
│
├── backend/                  # Django + GraphQL backend
│   ├── gql/                  # GraphQL schema entrypoint
│   │   ├── __init__.py
│   │   └── schema.py
│   ├── soundscene/           # Django project config
│   ├── users/                # Django app for user logic
│   │   ├── migrations/
│   │   ├── schema/           # GraphQL types & mutations
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── managers.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── services.py
│   │   ├── signals.py
│   │   ├── utility.py
│   │   ├── validators.py
│   │   └── tests/
│   │       └── __init__.py
│   ├── .env, .env.*          # Environment config files
│   │   ├── .env.db.local     # DB config used when running locally (PostgreSQL)
│   │   ├── .env.db.docker    # DB config used when running inside Docker container
│   ├── Dockerfile            # Dockerfile for backend
│   ├── manage.py             # Django management script
│   ├── main.py               # Entrypoint if using ASGI
│   ├── pyproject.toml        # Project metadata for uv
│   ├── mypy.ini              # Type checking config
│   ├── ruff.toml             # Linting config
│   ├── uv.lock               # Dependency lockfile (uv)
│   ├── pytest.ini, conftest.py  # Testing config
│   └── .dockerignore         # Backend Docker ignore file
│
├── frontend/                 # Angular frontend
│   ├── .vscode/              # VS Code settings
│   ├── node_modules/
│   ├── public/               # Static files
│   ├── src/
│   │   └── app/              # Angular app root
│   │       ├── index.html
│   │       ├── main.ts
│   │       └── styles.css
│   ├── angular.json          # Angular config
│   ├── package.json          # Frontend dependencies
│   ├── tsconfig.*.json       # TypeScript config
│   └── Dockerfile (planned)  # Placeholder for frontend Dockerfile
│
├── docker-compose.yml        # Root Docker Compose file
├── README.md                 # Project readme
├── .gitignore                # Root gitignore
└── .editorconfig             # Editor config
```


---

## 🚀 Getting Started

### 1. Clone the Repo

```bash
git clone https://github.com/Mofathy183/soundscene.git
cd soundscene
```

## 2. Run with Docker

### Make sure Docker is installed, then:
```bash
docker-compose up --build
```
This will:
- 🔧 Build and run the backend using your custom Dockerfile
- 🐘 Launch a PostgreSQL container
- ♻️ Mount your backend code for live reloading



## Setup Backend

### 1. Install with uv:

```bash
cd backend
uv venv
# Uses uv to install locked dependencies from uv.lock or requirements.lock
uv sync --locked
```

### 2. Setup environment variables files:
#### .env
```bash
# File: backend/.env

# Optional: Python path override
PYTHONPATH=.

# Django Core Settings
DJANGO_SECRET_KEY=your-secret-key
DEBUG=True

# Comma-separated list of allowed hosts
ALLOWED_HOSTS=localhost,db
```
#### .env.db.local
```bash
# File: backend/.env.db.local

DJANGO_ENV=local

# Local PostgreSQL DB Configuration
POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```
#### .env.db.docker
```bash
# File: backend/.env.db.docker

DJANGO_ENV=docker

# Docker PostgreSQL DB Configuration
POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

### 3. Run migrations and start server:
```bash
uv run manage.py makemigrations  
uv run manage.py migrate
uv run manage.py runserver 
```

### 4. Testing:
```bash
pytest

# If you drop and recreate the database,
# this command will rebuild the test DB
pytest --reuse-db --create-db
```

### 5. Code Quality:
#### Lint
```bash
ruff format .

ruff check .
```

#### Type Check
```bash
mypy .
```

## 📦 Deployment Tips
Use docker-compose.prod.yml for production environments (optional)

Host backend with services like Render, Railway, or Fly.io

Deploy frontend with Vercel, Netlify, or Firebase

Use AWS S3 or Cloudinary for production audio uploads


## 🤝 Contributing
### Fork the project
1. Create a feature branch:
   ```bash
   git checkout -b feat/awesome-feature
    ```
2. Commit your changes:
    ```bash
    git commit -m '✨ Add awesome feature'
    ```
3. Push to GitHub:
    ```bash
    git push origin feat/awesome-feature
    ```

## 📄 License
This project is licensed under the MIT License

## 🙌 Acknowledgements
- [Graphene](https://graphene-python.org/)
- [Apollo Angular](https://apollo-angular.com/)
- [ruff](https://github.com/astral-sh/ruff)
- [mypy](https://github.com/python/mypy)
- [uv](https://github.com/astral-sh/uv)


## 📬 Contact
### Have feedback or ideas?
📧 Reach out: [mofathy1833@gmail.com](mailto:mofathy1833@gmail.com)

---

### ✅ What I improved:
- Cleaned up formatting and indentation
- Added missing "Project Structure" section
- Clarified Docker usage
- Added licensing and contribution details
- Smoothed out environment variable instructions
- Added spacing for readability

Let me know if you'd like:
- GitHub Actions CI file
- `.dockerignore` templates
- A badge generator for versioning or Docker



