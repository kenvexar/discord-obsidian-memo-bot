"""
AI処理モジュール
"""

from .gemini_client import GeminiAPIError, GeminiClient, RateLimitExceeded
from .models import (
    AIModelConfig,
    AIProcessingResult,
    CategoryResult,
    ProcessingCategory,
    ProcessingPriority,
    ProcessingRequest,
    ProcessingSettings,
    ProcessingStats,
    SummaryResult,
    TagResult,
)
from .note_analyzer import AdvancedNoteAnalyzer
from .processor import AIProcessor
from .url_processor import URLContentExtractor

# 高度なAI機能
from .vector_store import NoteEmbedding, SemanticSearchResult, VectorStore

__all__ = [
    # クライアント
    "GeminiClient",
    "GeminiAPIError",
    "RateLimitExceeded",
    # モデル
    "AIModelConfig",
    "AIProcessingResult",
    "CategoryResult",
    "ProcessingCategory",
    "ProcessingPriority",
    "ProcessingRequest",
    "ProcessingSettings",
    "ProcessingStats",
    "SummaryResult",
    "TagResult",
    # プロセッサ
    "AIProcessor",
    # 高度なAI機能
    "VectorStore",
    "NoteEmbedding",
    "SemanticSearchResult",
    "URLContentExtractor",
    "AdvancedNoteAnalyzer",
]
