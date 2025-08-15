"""
Audio processing module for Discord-Obsidian Memo Bot
"""

from .models import AudioProcessingResult, TranscriptionResult
from .speech_processor import SpeechProcessor

__all__ = [
    "SpeechProcessor",
    "AudioProcessingResult",
    "TranscriptionResult",
]
