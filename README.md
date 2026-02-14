# AI Life Companion

An intelligent AI-powered life companion application with multiple specialized characters, personality-aware context, and proactive clarification.

## Features

### Core Features
- **Multi-Character System**: 8+ specialized AI characters (Coach, Psychologist, Sage, etc.)
- **Life Companion Interface**: Domain-specific character interactions
- **Personality Profiling**: 40-question assessment with Big Five traits
- **Explicit Context Management**: Track user goals, preferences, and values
- **Proactive Clarification**: Smart question generation when uncertainty detected

### Admin Features
- **Analytics Dashboard**: Real-time metrics, charts, export to CSV
- **AI Budget Management**: Daily limits, cost tracking, circuit breaker
- **User Management**: Role-based access (guest, user, paid, admin, developer)
- **Background Tasks**: Scheduled maintenance and expansion tasks

### Technical Features
- **Dual-Layer History**: Raw data + analytical interpretation
- **Smart Response System**: Context-aware AI responses
- **Multi-User Authentication**: JWT-based with session management
- **PythonAnywhere Deployment**: Auto-deploy with webhook support

## Quick Start

### Prerequisites
- Python 3.9+
- SQLite (included)
- API keys for AI providers

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/ai-model-compare.git
cd ai-model-compare

# Install dependencies
pip install -r requirements.txt

# Create .env file with API keys
cp .env.example .env
# Edit .env with your keys
```

### Environment Variables

```env
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
SECRET_KEY=your_secret_key_for_jwt
```

### Running Locally

```bash
python app.py
# Open http://localhost:5000
```

## Project Structure

```
├── app.py                      # Main Flask application
├── integrated_database.py      # User/session management
├── smart_response/             # AI response system
│   ├── handler.py              # Smart response handler
│   ├── ai_budget_manager.py    # Cost control
│   ├── proactive_clarification.py  # Question generation
│   ├── dual_layer_history.py   # History management
│   └── developer_analytics.py  # Metrics tracking
├── templates/                  # HTML templates
│   ├── chatchat.html          # Main chat interface
│   ├── domain_characters.html  # Life companion
│   └── admin_analytics.html    # Analytics dashboard
├── static/                     # JavaScript/CSS
│   ├── multi_user_app.js      # Main app logic
│   ├── auth_helper.js         # Authentication
│   └── explicit_context_ui.js  # Context management
└── tests/                      # Test suites
    └── test_comprehensive.py   # Playwright tests
```

## Key Documentation

| Document | Description |
|----------|-------------|
| `ARCHITECTURE_OVERVIEW.md` | System architecture |
| `CHARACTER_SPECTRUM_SYSTEM.md` | Character trait system |
| `INTELLIGENT_CONTEXT_ARCHITECTURE.md` | Context management |
| `SYSTEM_DESIGN_PRINCIPLES.md` | Design guidelines |

## API Endpoints

### Authentication
- `POST /login` - User login
- `POST /logout` - User logout
- `GET /api/session` - Get session info

### Chat
- `POST /api/chat/<character>` - Send message
- `GET /api/history/<character>` - Get history

### Admin
- `GET /api/admin/statistics` - System stats
- `GET /api/ai-budget/status` - Budget info
- `GET /api/developer/ai-calls` - AI call logs

## Testing

```bash
# Run comprehensive tests
python tests/test_comprehensive.py

# Run specific feature tests
python test_new_features_playwright.py
```

## Deployment

### PythonAnywhere
```bash
python deploy_anywhere.py
```

### Manual
1. Push to GitHub
2. Pull on server
3. Reload web app

## User Roles

| Role | Permissions |
|------|-------------|
| guest | Limited messages/day |
| user | Standard access |
| paid | Unlimited messages |
| administrator | Full admin access |
| developer | Admin + dev tools |

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## License

Private - All rights reserved

---

Last updated: 2026-01-08

Last updated: 2026-02-14 16:45:42