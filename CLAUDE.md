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

### Discord MCP Integration Testing
```bash
# Test Discord functionality using MCP (Model Context Protocol)
# This allows real-time validation of Discord bot features during development

# Prerequisites: Install and configure Discord MCP server
# Check Discord server info and channels
claude --mcp-server discord get-server-info <guild_id>

# Test message sending to specific channels
claude --mcp-server discord send-message <channel_id> "Test message"

# Monitor channel activity
claude --mcp-server discord read-messages <channel_id> --limit 10

# Test forum post creation (for structured content)
claude --mcp-server discord create-forum-post <forum_channel_id> "Test Title" "Test content"

# Validate bot reactions and interactions
claude --mcp-server discord add-reaction <channel_id> <message_id> "✅"

# Integration with development workflow:
# 1. Start the bot: uv run python -m src.main
# 2. Use MCP Discord commands to test bot responses
# 3. Verify Obsidian vault integration through Discord interactions
# 4. Check log output for debugging
```

## Architecture

### Core System Design
The application follows a **layered architecture**:
1. **Bot Layer** (`src/bot/`): Discord interface and command handling
2. **Processing Layer** (`src/ai/`): AI analysis and content processing
3. **Business Logic Layer** (`src/tasks/`, `src/finance/`): Domain-specific functionality
4. **Integration Layer** (`src/obsidian/`, `src/garmin/`, `src/audio/`): External service integrations
5. **Security Layer** (`src/security/`): Authentication and access control
6. **Monitoring Layer** (`src/monitoring/`): Health checks and observability
7. **Storage Layer**: File system operations and data persistence

### Key Architectural Patterns
- **Dependency Injection**: Constructor-based dependency management
- **Factory Pattern**: Client creation and configuration
- **Strategy Pattern**: Pluggable processing methods
- **Template Method Pattern**: Common processing workflows
- **Repository Pattern**: Data access abstraction
- **Observer Pattern**: Event-driven notifications

### Module Structure
```
src/
├── config/              # Settings and configuration management
│   ├── settings.py         # Main settings configuration
│   └── secure_settings.py  # Secure settings with encryption
├── utils/               # Shared utilities and logging
│   ├── logger.py           # Structured logging setup
│   └── mixins.py           # Utility mixins
├── security/            # Security and authentication
│   ├── secret_manager.py   # Secret management
│   └── access_logger.py    # Access logging
├── bot/                 # Discord bot implementation
│   ├── client.py           # Main Discord client
│   ├── handlers.py         # Message event handlers
│   ├── commands/           # Command modules
│   │   ├── basic_commands.py   # Basic bot commands
│   │   ├── config_commands.py  # Configuration commands
│   │   └── stats_commands.py   # Statistics commands
│   ├── mixins/             # Reusable bot mixins
│   │   └── command_base.py     # Command base class
│   ├── message_processor.py # Message processing logic
│   ├── notification_system.py # Notification management
│   ├── review_system.py    # Review and feedback system
│   ├── channel_config.py   # Channel configuration
│   ├── config_manager.py   # Configuration management
│   ├── backup_system.py    # Backup management
│   ├── models.py           # Bot data models
│   └── mock_client.py      # Mock client for testing
├── ai/                  # AI processing and analysis
│   ├── processor.py        # Main AI processor
│   ├── gemini_client.py    # Google Gemini API client
│   ├── note_analyzer.py    # Note analysis and categorization
│   ├── vector_store.py     # Vector storage for similarity
│   ├── url_processor.py    # URL content processing
│   ├── models.py           # AI data models
│   └── mock_processor.py   # Mock processor for testing
├── obsidian/            # Obsidian vault integration
│   ├── core/               # Core vault operations
│   │   ├── vault_manager.py    # Vault management
│   │   └── file_operations.py  # File operations
│   ├── search/             # Search functionality
│   │   ├── note_search.py      # Note search engine
│   │   └── search_models.py    # Search data models
│   ├── backup/             # Backup management
│   │   ├── backup_manager.py   # Backup operations
│   │   └── backup_models.py    # Backup data models
│   ├── analytics/          # Vault analytics
│   │   ├── vault_statistics.py # Vault stats
│   │   └── stats_models.py     # Statistics models
│   ├── interfaces.py       # Abstract interfaces
│   ├── models.py           # Obsidian data models
│   ├── local_data_manager.py # Local data management
│   ├── refactored_file_manager.py # Modern file operations
│   ├── template_system.py  # Advanced templating
│   ├── daily_integration.py # Daily note features
│   ├── organizer.py        # Vault organization
│   ├── github_sync.py      # GitHub synchronization
│   └── metadata.py         # Metadata management
├── tasks/               # Task management system
│   ├── task_manager.py     # Task management
│   ├── schedule_manager.py # Schedule management
│   ├── report_generator.py # Task reports
│   ├── reminder_system.py  # Task reminders
│   ├── commands.py         # Task commands
│   └── models.py           # Task data models
├── finance/             # Financial management
│   ├── expense_manager.py  # Expense tracking
│   ├── budget_manager.py   # Budget management
│   ├── subscription_manager.py # Subscription tracking
│   ├── report_generator.py # Financial reports
│   ├── reminder_system.py  # Financial reminders
│   ├── message_handler.py  # Finance message processing
│   ├── commands.py         # Finance commands
│   └── models.py           # Finance data models
├── audio/               # Voice processing
│   ├── speech_processor.py # Speech-to-text conversion
│   └── models.py           # Audio data models
├── garmin/              # Garmin Connect integration
│   ├── client.py           # Garmin API client
│   ├── cache.py            # Data caching
│   ├── formatter.py        # Data formatting
│   └── models.py           # Garmin data models
├── health_analysis/     # Health data processing
│   ├── analyzer.py         # Health data analysis
│   ├── integrator.py       # Data integration
│   ├── scheduler.py        # Health data scheduling
│   └── models.py           # Health data models
├── monitoring/          # Application monitoring
│   └── health_server.py    # Health check server
└── main.py              # Application entry point
```

## Technology Stack

### Core Dependencies
- **Discord.py**: Discord API integration
- **Google Generative AI**: Gemini API for AI processing
- **Google Cloud Speech**: Speech-to-text processing
- **Google Cloud Secret Manager**: Secure credential storage
- **Garmin Connect**: Fitness and health data integration
- **Pydantic**: Data validation and settings management
- **aiofiles/aiohttp**: Async file and HTTP operations
- **structlog + rich**: Structured logging with rich output
- **scikit-learn + numpy**: Machine learning for content analysis
- **beautifulsoup4 + requests**: Web scraping and URL processing
- **python-dateutil**: Advanced date/time handling
- **tenacity**: Retry logic for external APIs
- **asyncio-throttle**: Rate limiting for API calls

### Development Tools
- **uv**: Fast Python package manager
- **ruff**: Linting and formatting (replaces black, isort, flake8)
- **mypy**: Static type checking
- **pytest + pytest-asyncio**: Testing framework
- **pre-commit**: Git hooks for code quality

## Code Style Guidelines

### Formatting (Ruff Configuration)
- Line length: 88 characters (Black compatible)
- Python 3.13+ target
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

# ✅ SIMPLIFIED CHANNEL ARCHITECTURE (2025 年更新)
# Discord チャンネル数を 5 チャンネルまで削減し、 AI によるコンテンツ自動分類を実現
#
# 必須チャンネル (3 つ):
# - #memo            (統合入力チャンネル - 全てのコンテンツはここから)
# - #notifications   (システム通知)
# - #commands        (ボットコマンド)
#
# オプションチャンネル (2 つ):
# - #voice           (音声メモ専用)
# - #files           (ファイル共有専用)
#
# 🎯 MAJOR ARCHITECTURAL CHANGE:
# • 旧システム: 17+ の専用チャンネル (inbox, money, tasks, health, etc.)
# • 新システム: 最大 5 チャンネル + AI 自動分類
#
# 🤖 AI CONTENT CLASSIFICATION:
# #memo チャンネルに投稿された全てのコンテンツは AI により自動分類され、
# Obsidian の適切なフォルダに保存されます:
# • 💰 Finance → "1500 ランチ", "¥3000 本" → 💰 Finance フォルダ
# • ✅ Tasks → "TODO: 資料作成", "期限: 明日まで" → ✅ Tasks フォルダ
# • 🏃 Health → "体重 70kg", "ランニング 5km" → 🏃 Health フォルダ
# • 📚 Learning → "Python 学習", "読書メモ" → 📚 Learning フォルダ
# • 📝 Quick Notes → 短いメモ → 📝 Quick Notes フォルダ
# • 📋 Memos → その他全般 → 📋 Memos フォルダ
#
# 🔧 BACKWARD COMPATIBILITY REMOVED:
# • 全ての旧チャンネル ID 設定を削除
# • レガシー API メソッドを削除
# • シンプルな 2 カテゴリ構造 (CAPTURE/SYSTEM) に統一

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
- **Channel Management**: Simplified to 5 channels max (2025 年更新) - AI handles all categorization
- **Content Organization**: Obsidian-first approach with AI-powered folder assignment
- **Backward Compatibility**: All legacy channel APIs removed for simplified architecture

## Git Workflow

This project uses a simplified **main-only workflow** for direct development:

### Simple Development Workflow
```bash
# Direct development on main branch
git add .
git commit -m "feat: implement new feature"
git push origin main
```

### Commit Message Convention
Following [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation updates
- `refactor:` - Code refactoring
- `test:` - Test additions/modifications
- `chore:` - Build/tool changes
