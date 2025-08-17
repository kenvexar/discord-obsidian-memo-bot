# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Discord-Obsidian Memo Bot is a personal knowledge management system that uses Discord as an interface for AI-powered memo processing and automatic Obsidian note saving. The bot captures messages, processes them with Google Gemini AI, and organizes them into structured Obsidian notes.

### Core Features
- **Message Processing**: Automatic Discord message capture with AI analysis and metadata extraction
- **Voice Memo Processing**: Google Cloud Speech-to-Text integration for automatic transcription
- **Obsidian Integration**: Structured note generation with automatic folder classification and vault organization
- **Daily Note Integration**: Automatic integration with Activity Log and Daily Tasks
- **Template System**: Flexible templates with placeholder replacement
- **Finance Management**: Expense tracking and subscription management
- **Task Management**: Task creation, tracking, and productivity reviews
- **Health Data Integration**: Garmin Connect integration (optional)

## Development Commands

### Package Management
```bash
# Install dependencies (recommended)
uv sync

# Install development dependencies
uv sync --dev

# Add new package
uv add <package-name>

# Add development package
uv add --dev <package-name>
```

### Testing
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/unit/test_obsidian.py

# Run with coverage
uv run pytest --cov=src

# Run integration tests
uv run pytest tests/integration/

# Run async tests with verbose output
uv run pytest tests/unit/test_ai_processing.py -v
```

### Code Quality
```bash
# Format and lint (run this before commits)
uv run ruff check src/ --fix && uv run ruff format src/

# Type checking
uv run mypy src/

# Run all quality checks
uv run ruff check src/ --fix && uv run ruff format src/ && uv run mypy src/

# Pre-commit hooks (optional setup)
uv run pre-commit install
uv run pre-commit run --all-files
```

### Application Execution
```bash
# Start the bot
uv run python -m src.main

# Run with debug mode
uv run python -m src.main --debug
```

### Individual Feature Testing
```bash
# Test advanced AI features
uv run python test_advanced_ai.py

# Test Garmin integration
uv run python test_garmin_integration.py

# Test health data analysis
uv run python test_health_analysis.py
```

## Architecture

### Core System Design
The application follows a **layered architecture**:
1. **Bot Layer** (`src/bot/`): Discord interface and command handling
2. **Processing Layer** (`src/ai/`): AI analysis and content processing
3. **Integration Layer** (`src/obsidian/`, `src/garmin/`, `src/audio/`): External service integrations
4. **Storage Layer**: File system operations and data persistence

### Key Architectural Patterns
- **Dependency Injection**: Constructor-based dependency management
- **Factory Pattern**: Client creation and configuration
- **Strategy Pattern**: Pluggable processing methods
- **Template Method Pattern**: Common processing workflows

### Module Structure
```
src/
├── config/              # Settings and configuration management
├── utils/               # Shared utilities and logging
├── bot/                 # Discord bot implementation
│   ├── client.py        # Main Discord client
│   ├── handlers.py      # Message event handlers
│   ├── commands.py      # Slash commands
│   └── message_processor.py # Message processing logic
├── ai/                  # AI processing and analysis
│   ├── processor.py     # Main AI processor
│   ├── gemini_client.py # Google Gemini API client
│   ├── note_analyzer.py # Note analysis and categorization
│   └── vector_store.py  # Vector storage for similarity
├── obsidian/            # Obsidian vault integration
│   ├── file_manager.py  # File operations
│   ├── template_system.py # Advanced templating
│   ├── daily_integration.py # Daily note features
│   └── organizer.py     # Vault organization
├── audio/               # Voice processing
│   └── speech_processor.py # Speech-to-text conversion
├── garmin/              # Garmin Connect integration
│   ├── client.py        # Garmin API client
│   └── cache.py         # Data caching
└── health_analysis/     # Health data processing
    ├── analyzer.py      # Health data analysis
    └── integrator.py    # Data integration
```

## Technology Stack

### Core Dependencies
- **Discord.py**: Discord API integration
- **Google Generative AI**: Gemini API for AI processing
- **Google Cloud Speech**: Speech-to-text processing
- **Pydantic**: Data validation and settings management
- **aiofiles/aiohttp**: Async file and HTTP operations
- **structlog + rich**: Structured logging with rich output

### Development Tools
- **uv**: Fast Python package manager
- **ruff**: Linting and formatting (replaces black, isort, flake8)
- **mypy**: Static type checking
- **pytest + pytest-asyncio**: Testing framework
- **pre-commit**: Git hooks for code quality

## Code Style Guidelines

### Formatting (Ruff Configuration)
- Line length: 88 characters (Black compatible)
- Python 3.10+ target
- Double quotes for strings
- 4-space indentation
- Enabled rules: pyupgrade, flake8-bugbear, flake8-simplify, isort

### Type Checking (mypy)
- All functions must have type hints
- `disallow_untyped_defs = true`
- Pydantic plugin enabled
- Test files have relaxed type checking

### Design Principles
1. **Async First**: All I/O operations use async/await
2. **Type Safety**: Complete type hints throughout
3. **Error Handling**: Structured exception handling with proper logging
4. **Configuration**: Environment-based settings with Pydantic
5. **Separation of Concerns**: Each module has single responsibility

## Environment Setup

### Required Environment Variables
```env
# Core Discord & AI
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_GUILD_ID=your_guild_id
GEMINI_API_KEY=your_gemini_api_key
OBSIDIAN_VAULT_PATH=/path/to/your/obsidian/vault

# Channel Configuration (create these channels in Discord)
# Note: The bot automatically discovers channels by name - no IDs needed!
# Create Discord channels with these exact names:
#
# Required channels:
# - #inbox           (Main text memos)
# - #notifications   (System notifications)
# - #commands        (Bot commands)
#
# Optional channels:
# - #voice           (Voice memos)
# - #files           (File uploads)
# - #money           (Expense tracking)
# - #finance-reports (Financial analytics)
# - #tasks           (Task management)
# - #productivity-reviews (Daily reviews)
# ... and many more (see docs/EASY_SETUP.md for full list)

# Optional: Voice Recognition
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

## Testing Strategy

### Test Structure
- **Unit Tests** (`tests/unit/`): Individual component testing
- **Integration Tests** (`tests/integration/`): Cross-component testing
- **Feature Tests**: Specific functionality validation

### Key Test Files
- `test_message_processor.py`: Message handling logic
- `test_obsidian.py`: Obsidian integration
- `test_bot.py`: Discord bot functionality
- `test_ai_processing.py`: AI processing workflows

### Async Testing
All tests use `pytest-asyncio` with `asyncio_mode = "auto"` for seamless async testing.

## Important Notes

- **Package Manager**: Always use `uv` instead of pip for consistency
- **Python Version**: Requires Python 3.13+ (project uses 3.13)
- **API Limits**: Respects Google Gemini free tier limits (1500/day, 15/minute)
- **Security**: Uses `SecretStr` for sensitive data, gitleaks pre-commit hook for secret detection
- **Voice Processing**: Optional feature with 60-minute monthly limit (Google Cloud Speech-to-Text free tier)
- **Channel Management**: Bot automatically discovers channels by name - no channel ID configuration required
