"""
Speech processing and transcription using Google Cloud Speech-to-Text API
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any

import aiofiles
import aiohttp
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.utils.mixins import LoggerMixin

from ..config import get_settings
from .models import (
    AudioFormat,
    AudioProcessingResult,
    SpeechAPIUsage,
    TranscriptionResult,
)


class RetryableAPIError(Exception):
    """リトライ可能なAPIエラー"""

    pass


class NonRetryableAPIError(Exception):
    """リトライ不可能なAPIエラー"""

    pass


class SpeechProcessor(LoggerMixin):
    """音声処理と統合文字起こしシステム（複数エンジン対応）"""

    def __init__(self) -> None:
        """初期化処理"""
        self.usage_tracker = SpeechAPIUsage()
        self.supported_formats = {
            "mp3": AudioFormat.MP3,
            "wav": AudioFormat.WAV,
            "flac": AudioFormat.FLAC,
            "ogg": AudioFormat.OGG,
            "m4a": AudioFormat.M4A,
            "webm": AudioFormat.WEBM,
        }

        # 文字起こしエンジンの優先順位と利用可能性確認
        self.transcription_engines: list[dict[str, Any]] = []
        self._setup_transcription_engines()

        # API利用可能性フラグ
        self.api_available = (
            len(
                [
                    e
                    for e in self.transcription_engines
                    if e["name"] != "file_save_fallback"
                ]
            )
            > 0
        )

        self.logger.info(
            "音声処理システム初期化完了",
            available_engines=[engine["name"] for engine in self.transcription_engines],
            primary_engine=(
                self.transcription_engines[0]["name"]
                if self.transcription_engines
                else "none"
            ),
        )

    def _setup_transcription_engines(self) -> None:
        """文字起こしエンジンのセットアップと利用可能性確認"""
        self.transcription_engines = []

        # Google Cloud Speech-to-Text API
        if self._check_google_speech_api_availability():
            self.transcription_engines.append(
                {
                    "name": "google_cloud_speech",
                    "method": self._transcribe_audio,  # 実際に存在するメソッドを使用
                    "priority": 1,
                }
            )

        # ローカル Whisper モデル（簡易フォールバック）
        # 注意: _transcribe_with_local_whisperメソッドは未実装のため、コメントアウト
        # if self._check_local_whisper_availability():
        #     self.transcription_engines.append({
        #         'name': 'local_whisper',
        #         'method': self._transcribe_with_local_whisper,
        #         'priority': 2
        #     })

        # 最終フォールバック：ファイル保存のみ
        self.transcription_engines.append(
            {"name": "file_save_fallback", "method": None, "priority": 999}  # 特別処理
        )

        if not self.transcription_engines:
            self.logger.warning("文字起こしエンジンが利用できません")

    def _check_google_speech_api_availability(self) -> bool:
        """グーグルSpeech API の利用可能性を確認"""
        try:
            settings = get_settings()
            # APIキーまたは認証情報の確認
            if (
                hasattr(settings, "google_cloud_speech_api_key")
                and settings.google_cloud_speech_api_key
            ):
                return True

            if (
                hasattr(settings, "google_application_credentials")
                and settings.google_application_credentials
            ):
                credentials_path = Path(settings.google_application_credentials)
                if credentials_path.exists():
                    return True

            # 環境変数からの確認
            if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
                return True

            if os.environ.get("GOOGLE_CLOUD_SPEECH_API_KEY"):
                return True

            self.logger.debug("Google Cloud Speech API credentials not found")
            return False

        except Exception as e:
            self.logger.error(
                "Error checking Google Speech API availability", error=str(e)
            )
            return False

    def _check_local_whisper_availability(self) -> bool:
        """ローカル Whisper の利用可能性を確認"""
        try:
            # whisper パッケージの確認
            import importlib.util

            if importlib.util.find_spec("whisper") is not None:
                self.logger.info("Local Whisper model available")
                return True
            else:
                return False
        except ImportError:
            self.logger.debug(
                "Local Whisper not available (whisper package not installed)"
            )
            return False
        except Exception as e:
            self.logger.debug("Error checking local Whisper availability", error=str(e))
            return False

    async def process_audio_file(
        self, file_data: bytes, filename: str, channel_name: str | None = None
    ) -> AudioProcessingResult:
        """
        音声ファイルを処理して文字起こしを実行

        Args:
            file_data: 音声ファイルのバイナリデータ
            filename: ファイル名
            channel_name: Discord チャンネル名

        Returns:
            音声処理結果
        """
        start_time = datetime.now()

        try:
            # ファイル形式の検証
            audio_format = self._detect_audio_format(filename)
            if not audio_format:
                return self._create_error_result(
                    filename=filename,
                    file_size=len(file_data),
                    error="Unsupported audio format",
                    processing_time_ms=0,
                )

            # 音声品質の事前検証
            quality_check = await self._validate_audio_quality(file_data, audio_format)
            if not quality_check["valid"]:
                return self._create_error_result(
                    filename=filename,
                    file_size=len(file_data),
                    error=quality_check["error"],
                    processing_time_ms=int(
                        (datetime.now() - start_time).total_seconds() * 1000
                    ),
                )

            self.logger.info(
                "Processing audio file",
                filename=filename,
                size_bytes=len(file_data),
                format=audio_format.value,
            )

            # API制限の確認
            if self.usage_tracker.is_limit_exceeded:
                return await self._handle_fallback(
                    file_data=file_data,
                    filename=filename,
                    audio_format=audio_format,
                    reason="API limit exceeded",
                    start_time=start_time,
                )

            # 音声の長さを推定（概算）
            estimated_duration = self._estimate_audio_duration(file_data, audio_format)

            # API利用可能性の確認
            if not self.api_available:
                return await self._handle_fallback(
                    file_data=file_data,
                    filename=filename,
                    audio_format=audio_format,
                    reason="API not available",
                    start_time=start_time,
                )

            # Google Cloud Speech-to-Text APIで文字起こし
            transcription_result = await self._transcribe_audio(file_data, audio_format)

            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

            # 使用量を追跡
            if estimated_duration:
                duration_minutes = estimated_duration / 60.0
                self.usage_tracker.add_usage(duration_minutes, success=True)

            return AudioProcessingResult(
                success=True,
                transcription=transcription_result,
                original_filename=filename,
                file_size_bytes=len(file_data),
                audio_format=audio_format,
                duration_seconds=estimated_duration,
                processing_time_ms=processing_time,
                api_usage_minutes=duration_minutes if estimated_duration else 0.0,
            )

        except Exception as e:
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

            self.logger.error(
                "Audio processing failed",
                filename=filename,
                error=str(e),
                exc_info=True,
            )

            # エラーの場合はフォールバック
            return await self._handle_fallback(
                file_data=file_data,
                filename=filename,
                audio_format=audio_format or AudioFormat.MP3,
                reason=f"Processing error: {str(e)}",
                start_time=start_time,
            )

    def _detect_audio_format(self, filename: str) -> AudioFormat | None:
        """ファイル名から音声フォーマットを検出"""
        try:
            extension = Path(filename).suffix.lower().lstrip(".")
            return self.supported_formats.get(extension)
        except Exception as e:
            self.logger.warning(
                "Failed to detect audio format", filename=filename, error=str(e)
            )
            return None

    def _estimate_audio_duration(
        self, file_data: bytes, audio_format: AudioFormat
    ) -> float | None:
        """音声ファイルの長さを推定（簡易版）"""
        try:
            # 簡易的な推定（実際の実装では音声ライブラリを使用）
            # ファイルサイズベースの概算
            size_mb = len(file_data) / (1024 * 1024)

            # フォーマットに基づく概算（非常に大まかな推定）
            if audio_format in [AudioFormat.MP3, AudioFormat.M4A]:
                # 圧縮形式: 1MBあたり約1分程度
                estimated_duration = size_mb * 60
            elif audio_format in [AudioFormat.WAV, AudioFormat.FLAC]:
                # 非圧縮形式: より短い
                estimated_duration = size_mb * 10
            else:
                # その他
                estimated_duration = size_mb * 30

            # 現実的な範囲に制限
            return max(1.0, min(estimated_duration, 600.0))  # 1秒〜10分

        except Exception as e:
            self.logger.warning("Failed to estimate audio duration", error=str(e))
            return None

    async def _transcribe_audio(
        self, file_data: bytes, audio_format: AudioFormat
    ) -> TranscriptionResult:
        """Google Cloud Speech-to-Text APIで音声を文字起こし"""
        try:
            # Google Cloud Speech APIを使用（実際の実装）
            settings = get_settings()
            if (
                hasattr(settings, "google_cloud_speech_api_key")
                and settings.google_cloud_speech_api_key
            ):
                from typing import cast

                result = await self._transcribe_with_rest_api(file_data, audio_format)
                return cast(TranscriptionResult, result)
            else:
                return await self._transcribe_with_client_library(
                    file_data, audio_format
                )

        except (RetryableAPIError, NonRetryableAPIError) as e:
            self.logger.error("API transcription failed after retries", error=str(e))
            # APIエラーの場合は詳細なエラー情報を含める
            error_msg = self._get_user_friendly_error_message(str(e))
            return TranscriptionResult.create_from_confidence(
                transcript=f"[{error_msg}]",
                confidence=0.0,
                processing_time_ms=0,
                model_used="error",
            )
        except Exception as e:
            self.logger.error(
                "Unexpected transcription error", error=str(e), exc_info=True
            )
            # その他のエラー
            return TranscriptionResult.create_from_confidence(
                transcript="[音声の文字起こしに失敗しました]",
                confidence=0.0,
                processing_time_ms=0,
                model_used="error",
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(RetryableAPIError),
    )
    async def _transcribe_with_rest_api(
        self, file_data: bytes, audio_format: AudioFormat
    ) -> TranscriptionResult:
        """REST APIを使用して音声を文字起こし（リトライ機能付き）"""
        import base64

        start_time = datetime.now()

        try:
            # ファイルをBase64エンコード
            encoded_audio = base64.b64encode(file_data).decode("utf-8")

            # APIリクエストペイロード
            request_data = {
                "config": {
                    "encoding": self._get_encoding_for_format(audio_format),
                    "sampleRateHertz": 16000,
                    "languageCode": "ja-JP",
                    "enableWordTimeOffsets": True,
                    "enableAutomaticPunctuation": True,
                    "model": "latest_short",
                },
                "audio": {"content": encoded_audio},
            }

            # API キーを使用してリクエスト
            settings = get_settings()
            if settings.google_cloud_speech_api_key is None:
                raise ValueError("Google Cloud Speech API key is not configured")
            api_key = settings.google_cloud_speech_api_key.get_secret_value()
            url = f"https://speech.googleapis.com/v1/speech:recognize?key={api_key}"

            async with (
                aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as session,
                session.post(url, json=request_data) as response,
            ):
                # HTTPステータスコードに基づく分岐処理
                if response.status == 200:
                    result = await response.json()
                elif response.status == 429:  # Rate limit
                    self.logger.warning("API rate limit exceeded")
                    raise NonRetryableAPIError("API rate limit exceeded")
                elif response.status >= 500:  # Server errors
                    error_text = await response.text()
                    self.logger.warning(
                        "API server error - will retry",
                        status=response.status,
                        error=error_text,
                    )
                    raise RetryableAPIError(
                        f"Server error: {response.status} - {error_text}"
                    )
                elif response.status == 400:  # Bad request
                    error_text = await response.text()
                    self.logger.error(
                        "API bad request - will not retry",
                        status=response.status,
                        error=error_text,
                    )
                    raise NonRetryableAPIError(
                        f"Bad request: {response.status} - {error_text}"
                    )
                else:
                    error_text = await response.text()
                    self.logger.warning(
                        "API client error - will retry once",
                        status=response.status,
                        error=error_text,
                    )
                    raise RetryableAPIError(
                        f"Client error: {response.status} - {error_text}"
                    )

            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

            # レスポンスを解析
            if "results" in result and result["results"]:
                alternative = result["results"][0]["alternatives"][0]
                transcript = alternative.get("transcript", "")
                confidence = alternative.get("confidence", 0.0)

                self.logger.info(
                    "Speech API transcription successful",
                    transcript_length=len(transcript),
                    confidence=confidence,
                    processing_time_ms=processing_time,
                )

                return TranscriptionResult.create_from_confidence(
                    transcript=transcript,
                    confidence=confidence,
                    processing_time_ms=processing_time,
                    model_used="google-speech-latest_short",
                    words=alternative.get("words", []),
                    alternatives=result["results"][0].get("alternatives", []),
                )
            else:
                # 結果なし
                self.logger.info("No speech detected in audio")
                return TranscriptionResult.create_from_confidence(
                    transcript="[音声が検出されませんでした]",
                    confidence=0.0,
                    processing_time_ms=processing_time,
                    model_used="google-speech-latest_short",
                )

        except (RetryableAPIError, NonRetryableAPIError):
            # これらは既に適切にログ出力されているので、再発生させる
            raise
        except Exception as e:
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            self.logger.error(
                "Unexpected error in REST API transcription",
                error=str(e),
                exc_info=True,
            )

            return TranscriptionResult.create_from_confidence(
                transcript=f"[予期しないエラー: {str(e)}]",
                confidence=0.0,
                processing_time_ms=processing_time,
                model_used="google-speech-error",
            )

    async def _transcribe_with_client_library(
        self, file_data: bytes, audio_format: AudioFormat
    ) -> TranscriptionResult:
        """クライアントライブラリを使用して音声を文字起こし"""
        start_time = datetime.now()

        try:
            # Google Cloud Speech クライアントライブラリの使用
            # 注意: 実際の実装では google-cloud-speech ライブラリが必要
            # ここでは簡易的な実装を提供

            self.logger.info(
                "Using client library for transcription (mock implementation)"
            )

            # モック実装（実際の実装では Google Cloud Speech Client を使用）
            await self._simulate_processing_delay()

            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

            return TranscriptionResult.create_from_confidence(
                transcript="[クライアントライブラリによる音声文字起こしの結果がここに表示されます]",
                confidence=0.85,
                processing_time_ms=processing_time,
                model_used="google-speech-client-library",
            )

        except Exception as e:
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            self.logger.error("Client library transcription failed", error=str(e))

            return TranscriptionResult.create_from_confidence(
                transcript=f"[クライアントライブラリエラー: {str(e)}]",
                confidence=0.0,
                processing_time_ms=processing_time,
                model_used="google-speech-error",
            )

    async def _simulate_processing_delay(self) -> None:
        """処理の遅延をシミュレート"""
        import asyncio

        await asyncio.sleep(1)  # 1秒の遅延をシミュレート

    def _get_encoding_for_format(self, audio_format: AudioFormat) -> str:
        """音声フォーマットからエンコーディング名を取得"""
        format_mapping = {
            AudioFormat.MP3: "MP3",
            AudioFormat.WAV: "LINEAR16",
            AudioFormat.FLAC: "FLAC",
            AudioFormat.OGG: "OGG_OPUS",
            AudioFormat.M4A: "MP3",  # M4Aは通常AACだが、MP3として処理
            AudioFormat.WEBM: "WEBM_OPUS",
        }
        return format_mapping.get(audio_format, "LINEAR16")

    async def _handle_fallback(
        self,
        file_data: bytes,
        filename: str,
        audio_format: AudioFormat,
        reason: str,
        start_time: datetime,
    ) -> AudioProcessingResult:
        """フォールバック処理: 音声ファイルを保存して手動処理用リンクを生成"""
        try:
            # 音声ファイルを保存
            saved_path = await self._save_audio_file_for_manual_processing(
                file_data, filename
            )

            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

            # フォールバック結果を作成
            fallback_transcript = (
                f"[音声ファイルが保存されました: {saved_path}]\n"
                f"制限理由: {reason}\n"
                f"手動で文字起こしを行うか、API制限がリセットされるまでお待ちください。"
            )

            transcription = TranscriptionResult.create_from_confidence(
                transcript=fallback_transcript,
                confidence=0.0,
                processing_time_ms=processing_time,
                model_used="fallback-file-save",
            )

            return AudioProcessingResult(
                success=False,
                transcription=transcription,
                original_filename=filename,
                file_size_bytes=len(file_data),
                audio_format=audio_format,
                processing_time_ms=processing_time,
                fallback_used=True,
                fallback_reason=reason,
                saved_file_path=saved_path,
            )

        except Exception as e:
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

            return self._create_error_result(
                filename=filename,
                file_size=len(file_data),
                error=f"Fallback failed: {str(e)}",
                processing_time_ms=processing_time,
            )

    async def _save_audio_file_for_manual_processing(
        self, file_data: bytes, filename: str
    ) -> str:
        """手動処理用に音声ファイルを保存"""
        try:
            # Obsidian vault内のaudioフォルダに保存
            settings = get_settings()

            audio_dir = Path(settings.obsidian_vault_path) / "06_Attachments" / "Audio"
            audio_dir.mkdir(parents=True, exist_ok=True)

            # ユニークなファイル名を生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = Path(filename).stem[:50]  # ファイル名を制限
            extension = Path(filename).suffix or ".mp3"

            saved_filename = f"{timestamp}_{safe_filename}{extension}"
            saved_path = audio_dir / saved_filename

            # ファイルを保存
            async with aiofiles.open(saved_path, "wb") as f:
                await f.write(file_data)

            self.logger.info(
                "Audio file saved for manual processing",
                filename=filename,
                saved_path=str(saved_path),
            )

            return str(saved_path)

        except Exception as e:
            self.logger.error("Failed to save audio file", error=str(e), exc_info=True)
            raise

    def _create_error_result(
        self, filename: str, file_size: int, error: str, processing_time_ms: int
    ) -> AudioProcessingResult:
        """エラー結果を作成"""
        return AudioProcessingResult(
            success=False,
            transcription=None,
            error_message=error,
            original_filename=filename,
            file_size_bytes=file_size,
            audio_format=AudioFormat.MP3,  # デフォルト値
            processing_time_ms=processing_time_ms,
        )

    def get_usage_stats(self) -> dict[str, Any]:
        """API使用量統計を取得"""
        return {
            "monthly_usage_minutes": self.usage_tracker.monthly_usage_minutes,
            "monthly_limit_minutes": self.usage_tracker.monthly_limit_minutes,
            "usage_percentage": self.usage_tracker.usage_percentage,
            "remaining_minutes": self.usage_tracker.remaining_minutes,
            "is_limit_exceeded": self.usage_tracker.is_limit_exceeded,
            "total_requests": self.usage_tracker.total_requests,
            "successful_requests": self.usage_tracker.successful_requests,
            "failed_requests": self.usage_tracker.failed_requests,
            "last_updated": self.usage_tracker.last_updated.isoformat(),
        }

    def reset_monthly_usage(self) -> None:
        """月間使用量をリセット"""
        self.usage_tracker.reset_monthly_usage()
        self.logger.info("Monthly usage reset")

    def _get_user_friendly_error_message(self, error_msg: str) -> str:
        """ユーザーフレンドリーなエラーメッセージに変換"""
        if "API rate limit exceeded" in error_msg or "429" in error_msg:
            return "今月のAPI利用上限に達しました。来月までお待ちいただくか、手動での文字起こしをお願いします"
        elif "Server error" in error_msg or "5" in error_msg[:1]:
            return "APIサーバーで一時的な問題が発生しています。しばらくしてからもう一度お試しください"
        elif "Bad request" in error_msg or "400" in error_msg:
            return "音声ファイルの形式に問題があります。サポートされている形式（MP3、WAV、FLAC等）をご利用ください"
        elif "timeout" in error_msg.lower():
            return "処理時間が長すぎるため、タイムアウトしました。短い音声ファイルでお試しください"
        else:
            return (
                "一時的なエラーが発生しました。しばらくしてからもう一度お試しください"
            )

    async def _validate_audio_quality(
        self, file_data: bytes, audio_format: AudioFormat
    ) -> dict[str, Any]:
        """音声品質の事前検証"""
        try:
            from io import BytesIO

            from pydub import AudioSegment

            # 音声セグメントを作成
            audio_segment = AudioSegment.from_file(
                BytesIO(file_data), format=audio_format.value
            )

            # 長さの検証
            duration_ms = len(audio_segment)
            if duration_ms < 500:  # 0.5秒未満
                return {
                    "valid": False,
                    "error": "音声が短すぎます（0.5秒未満）。文字起こしには最低0.5秒以上の音声が必要です。",
                    "duration_ms": duration_ms,
                }

            if duration_ms > 60 * 60 * 1000:  # 1時間以上
                return {
                    "valid": False,
                    "error": "音声が長すぎます（1時間以上）。API制限のため、60分以内の音声をご利用ください。",
                    "duration_ms": duration_ms,
                }

            # 音量レベルの検証（無音チェック）
            try:
                dBFS = audio_segment.dBFS
                if dBFS < -60:  # ほぼ無音
                    return {
                        "valid": False,
                        "error": "音声レベルが非常に低い、または無音状態です。マイクの設定をご確認ください。",
                        "duration_ms": duration_ms,
                        "dBFS": dBFS,
                    }

                # 非常に低い音量の警告
                if dBFS < -40:
                    self.logger.warning(
                        "Low audio volume detected", dBFS=dBFS, duration_ms=duration_ms
                    )

            except Exception as e:
                # 音量チェックが失敗してもスキップして続行
                self.logger.debug("Audio volume check failed", error=str(e))

            # チャンネル数の確認
            channels = audio_segment.channels
            if channels > 2:
                self.logger.info(
                    "Multi-channel audio detected, will be processed as-is",
                    channels=channels,
                )

            # サンプルレートの確認
            frame_rate = audio_segment.frame_rate
            if frame_rate < 8000:
                return {
                    "valid": False,
                    "error": f"サンプルレート（{frame_rate}Hz）が低すぎます。8kHz以上の音声をご利用ください。",
                    "duration_ms": duration_ms,
                    "frame_rate": frame_rate,
                }

            self.logger.info(
                "Audio quality validation passed",
                duration_ms=duration_ms,
                dBFS=getattr(audio_segment, "dBFS", "unknown"),
                channels=channels,
                frame_rate=frame_rate,
            )

            return {
                "valid": True,
                "duration_ms": duration_ms,
                "channels": channels,
                "frame_rate": frame_rate,
                "dBFS": getattr(audio_segment, "dBFS", None),
            }

        except ImportError:
            self.logger.warning(
                "pydub not available, skipping audio quality validation"
            )
            return {"valid": True}  # pydub が利用できない場合はスキップ

        except Exception as e:
            self.logger.error(
                "Audio quality validation failed", error=str(e), exc_info=True
            )
            # 検証に失敗した場合は処理を継続
            return {"valid": True, "warning": f"音声品質検証エラー: {str(e)}"}

    def is_audio_file(self, filename: str) -> bool:
        """ファイルが音声ファイルかどうかを判定"""
        return self._detect_audio_format(filename) is not None
