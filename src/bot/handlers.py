"""
Message handlers for Discord bot
"""

from datetime import datetime
from typing import Any

import discord

from ..ai import AIProcessor, ProcessingSettings
from ..ai.mock_processor import MockAIProcessor
from ..ai.models import AIProcessingResult
from ..ai.note_analyzer import AdvancedNoteAnalyzer
from ..audio import SpeechProcessor
from ..obsidian import ObsidianFileManager, TemplateEngine
from ..obsidian.daily_integration import DailyNoteIntegration
from ..utils.mixins import LoggerMixin
from .channel_config import ChannelCategory, ChannelConfig
from .message_processor import MessageProcessor


class MessageHandler(LoggerMixin):
    """Handle Discord message processing and routing"""

    ai_processor: AIProcessor | MockAIProcessor
    obsidian_manager: ObsidianFileManager | None
    note_template: None  # 古いテンプレートシステムは無効化
    daily_integration: DailyNoteIntegration | None
    template_engine: TemplateEngine | None
    note_analyzer: AdvancedNoteAnalyzer | None
    speech_processor: SpeechProcessor | None

    def set_monitoring_systems(
        self, system_metrics: Any, api_usage_monitor: Any
    ) -> None:
        """監視システムの設定"""
        self.system_metrics = system_metrics
        self.api_usage_monitor = api_usage_monitor

    def __init__(self, channel_config: ChannelConfig) -> None:
        self.channel_config = channel_config
        self.message_processor = MessageProcessor()

        # AI 処理システムの初期化（モック対応）
        processing_settings = ProcessingSettings(
            min_text_length=30,
            max_text_length=4000,
            enable_summary=True,
            enable_tags=True,
            enable_categorization=True,
        )

        # モードに応じて AI プロセッサーを初期化
        from ..config import get_settings

        settings = get_settings()

        if settings.is_mock_mode:
            self.logger.info("Initializing AI processor in MOCK mode")
            self.ai_processor = MockAIProcessor(settings=processing_settings)
        else:
            self.logger.info("Initializing AI processor in PRODUCTION mode")
            self.ai_processor = AIProcessor(settings=processing_settings)

        # Obsidian ファイル管理システムの初期化
        try:
            self.obsidian_manager = ObsidianFileManager()
            self.note_template = None  # 古いテンプレートシステムは無効化
            self.daily_integration = DailyNoteIntegration(self.obsidian_manager)
            self.template_engine = TemplateEngine(self.obsidian_manager.vault_path)

            # 高度なノート分析システムの初期化
            self.note_analyzer = AdvancedNoteAnalyzer(
                obsidian_file_manager=self.obsidian_manager,
                ai_processor=self.ai_processor,
            )

            self.logger.info(
                "Obsidian components with advanced AI features initialized"
            )
        except Exception as e:
            self.obsidian_manager = None
            self.note_template = None
            self.daily_integration = None
            self.template_engine = None
            self.note_analyzer = None
            self.logger.error("Failed to initialize Obsidian manager", error=str(e))

        # 音声処理システムの初期化（モック対応）
        try:
            if settings.is_mock_mode:
                self.logger.info("Speech processor disabled in mock mode")
                self.speech_processor = None
            else:
                self.speech_processor = SpeechProcessor()
                self.logger.info("Speech processor initialized")
        except Exception as e:
            self.speech_processor = None
            self.logger.error("Failed to initialize speech processor", error=str(e))

        self.logger.info(
            "Message handler initialized",
            ai_mock_mode=settings.is_mock_mode,
            obsidian_enabled=self.obsidian_manager is not None,
            speech_enabled=self.speech_processor is not None,
        )

    async def initialize(self) -> None:
        """非同期初期化処理"""
        if self.template_engine:
            try:
                await self.template_engine.create_default_templates()
                self.logger.info("Default templates created")
            except Exception as e:
                self.logger.error("Failed to create default templates", error=str(e))

    async def process_message(self, message: discord.Message) -> dict[str, Any] | None:
        """
        Process incoming Discord message and extract metadata

        Args:
            message: Discord message object

        Returns:
            Dictionary containing processed message data or None if ignored
        """
        processing_start = datetime.now()

        # Skip bot messages
        if message.author.bot:
            return None

        # Check if channel is monitored
        if not self.channel_config.is_monitored_channel(message.channel.id):
            return None

        channel_info = self.channel_config.get_channel_info(message.channel.id)

        # Record message processing for monitoring
        if hasattr(self, "system_metrics"):
            self.system_metrics.record_message_processed()

        self.logger.info(
            "Processing message",
            channel_id=message.channel.id,
            channel_name=channel_info.name,
            category=channel_info.category.value,
            author=str(message.author),
            message_id=message.id,
        )

        # Extract comprehensive metadata using the message processor
        metadata = self.message_processor.extract_metadata(message)

        # AI 処理を実行（テキストがある場合のみ）
        ai_result: AIProcessingResult | None = None
        if message.content and len(message.content.strip()) > 20:
            try:
                result = await self.ai_processor.process_text(
                    text=message.content, message_id=message.id
                )
                ai_result = result if isinstance(result, AIProcessingResult) else None

                # Record AI request metrics
                if hasattr(self, "system_metrics"):
                    processing_time = (
                        datetime.now() - processing_start
                    ).total_seconds() * 1000
                    self.system_metrics.record_ai_request(True, int(processing_time))

                if hasattr(self, "api_usage_monitor"):
                    # Estimate token usage (rough calculation)
                    estimated_tokens = len(message.content.split()) * 1.3
                    self.api_usage_monitor.track_gemini_usage(
                        int(estimated_tokens), True
                    )

                self.logger.info(
                    "AI processing completed",
                    message_id=message.id,
                    has_summary=getattr(ai_result, "summary", None) is not None,
                    has_tags=getattr(ai_result, "tags", None) is not None,
                    has_category=getattr(ai_result, "category", None) is not None,
                    total_time_ms=getattr(ai_result, "total_processing_time_ms", 0),
                )

            except Exception as e:
                # Record AI request failure
                if hasattr(self, "system_metrics"):
                    processing_time = (
                        datetime.now() - processing_start
                    ).total_seconds() * 1000
                    self.system_metrics.record_ai_request(False, int(processing_time))
                    self.system_metrics.record_error("ai_processing", str(e))

                if hasattr(self, "api_usage_monitor"):
                    estimated_tokens = (
                        len(message.content.split()) * 1.3 if message.content else 0
                    )
                    self.api_usage_monitor.track_gemini_usage(
                        int(estimated_tokens), False
                    )

                self.logger.error(
                    "AI processing failed",
                    message_id=message.id,
                    error=str(e),
                    exc_info=True,
                )

        # Combine with channel information
        message_data = {
            "metadata": metadata,
            "ai_processing": ai_result.model_dump() if ai_result else None,
            "channel_info": {
                "name": channel_info.name,
                "category": channel_info.category.value,
                "description": channel_info.description,
            },
            "processing_timestamp": datetime.now().isoformat(),
        }

        # Route message based on channel category
        await self._route_message_by_category(
            message_data, channel_info.category, message
        )

        return message_data

    async def _update_feedback_message(
        self, message: discord.Message | None, content: str
    ) -> None:
        """フィードバックメッセージを更新"""
        if not message:
            return

        try:
            await message.edit(content=content)
        except Exception as e:
            self.logger.warning(
                "Failed to update feedback message", error=str(e), message_id=message.id
            )

    async def _route_message_by_category(
        self,
        message_data: dict[str, Any],
        category: ChannelCategory,
        original_message: discord.Message | None = None,
    ) -> None:
        """Route message processing based on channel category"""

        if category == ChannelCategory.CAPTURE:
            await self._handle_capture_message(message_data, original_message)
        elif category == ChannelCategory.SYSTEM:
            await self._handle_system_message(message_data)
        else:
            self.logger.warning("Unknown channel category", category=category.value)

    async def _handle_capture_message(
        self,
        message_data: dict[str, Any],
        original_message: discord.Message | None = None,
    ) -> None:
        """Handle messages from capture channels"""
        self.logger.info(
            "Handling capture message",
            channel_name=message_data["channel_info"]["name"],
        )

        # AI 処理結果を取得
        ai_processing = message_data.get("ai_processing")

        if ai_processing:
            self.logger.info(
                "Processing capture message with AI results",
                has_summary=ai_processing.get("summary") is not None,
                has_tags=ai_processing.get("tags") is not None,
                has_category=ai_processing.get("category") is not None,
            )

            # 要約とタグをログ出力（デバッグ用）
            if ai_processing.get("summary"):
                summary_text = ai_processing["summary"]["summary"]
                self.logger.debug(
                    "Generated summary",
                    summary=(
                        summary_text[:100] + "..."
                        if len(summary_text) > 100
                        else summary_text
                    ),
                )

            if ai_processing.get("tags"):
                tags = ai_processing["tags"]["tags"]
                self.logger.debug("Generated tags", tags=tags)

            if ai_processing.get("category"):
                category = ai_processing["category"]["category"]
                confidence = ai_processing["category"]["confidence_score"]
                self.logger.debug(
                    "Generated category", category=category, confidence=confidence
                )

        # Obsidian ノートの生成と保存（新しい TemplateEngine を使用）
        if self.obsidian_manager and self.template_engine:
            try:
                # AI 処理結果を AIProcessingResult オブジェクトに変換
                ai_result: AIProcessingResult | None = None
                if ai_processing:
                    ai_result = AIProcessingResult.model_validate(ai_processing)

                # 新しい TemplateEngine で Obsidian ノートを生成
                note = await self.template_engine.generate_note_from_template(
                    template_name="daily_note",
                    message_data=message_data,
                    ai_result=ai_result,
                )

                if note:
                    # Vault の初期化（初回のみ）
                    await self.obsidian_manager.initialize_vault()

                    # 高度な AI 分析を実行（ノート分析器が利用可能な場合）
                    enhanced_content = note.content
                    if self.note_analyzer and note.content:
                        try:
                            self.logger.info(
                                "Running advanced AI analysis on note content",
                                note_title=note.title,
                            )

                            # Discord メタデータを構築
                            discord_metadata = (
                                {
                                    "channel_name": message_data["channel_info"][
                                        "name"
                                    ],
                                    "channel_category": message_data["channel_info"][
                                        "category"
                                    ],
                                    "timestamp": message_data["metadata"]["basic"][
                                        "timestamp"
                                    ],
                                    "user_id": message_data["metadata"]["basic"][
                                        "author"
                                    ]["id"],
                                }
                                if original_message
                                else None
                            )

                            # 包括的なノート分析を実行
                            analysis_result = await self.note_analyzer.analyze_note_content(
                                content=note.content,
                                title=note.title,
                                file_path=str(
                                    note.file_path.relative_to(
                                        self.obsidian_manager.vault_path
                                    )
                                ),
                                include_url_processing=True,
                                include_related_notes=True,
                                discord_metadata=discord_metadata,  # Discord メタデータを渡す
                            )

                            # 分析結果から強化されたコンテンツを取得
                            if analysis_result.get("enhanced_content", {}).get(
                                "content"
                            ):
                                enhanced_content = analysis_result["enhanced_content"][
                                    "content"
                                ]
                                self.logger.info(
                                    "Enhanced note content with AI analysis",
                                    has_related_notes=bool(
                                        analysis_result.get("related_notes", {}).get(
                                            "results"
                                        )
                                    ),
                                    has_internal_links=bool(
                                        analysis_result.get("internal_links", {}).get(
                                            "suggestions"
                                        )
                                    ),
                                    has_discord_analysis=bool(
                                        analysis_result.get("discord_analysis")
                                    ),
                                )

                        except Exception as e:
                            self.logger.warning(
                                "Failed to run advanced AI analysis",
                                note_title=note.title,
                                error=str(e),
                            )

                    # 強化されたコンテンツでノートを更新
                    if enhanced_content != note.content:
                        note.content = enhanced_content

                    # ノートを保存
                    saved_file_path = await self.obsidian_manager.save_note(note)
                    self.logger.info(
                        "Note saved successfully",
                        title=note.title,
                        file_path=str(saved_file_path),
                        content_length=len(enhanced_content),
                    )

                    # Daily Integration の実行
                    if self.daily_integration:
                        try:
                            # メモ保存を Activity Log に追加するためのメッセージデータを構築
                            activity_data = {
                                "metadata": {
                                    "content": {
                                        "raw_content": f"📝 {note.title} - Saved memo from Discord #{message_data['channel_info']['name']}"
                                    },
                                    "timing": message_data["metadata"].get(
                                        "timing", {}
                                    ),
                                }
                            }
                            await self.daily_integration.add_activity_log_entry(
                                activity_data
                            )
                        except Exception as e:
                            self.logger.warning(
                                "Failed to add daily integration entry", error=str(e)
                            )

            except Exception as e:
                self.logger.error("Failed to create Obsidian note", error=str(e))

    async def _handle_daily_note_integration(
        self, message_data: dict[str, Any], channel_info: Any
    ) -> None:
        """デイリーノート統合の処理"""
        try:
            from ..config import get_settings

            settings = get_settings()

            channel_id = channel_info.id

            # Activity Log チャンネルの処理
            if (
                self.daily_integration
                and hasattr(settings, "channel_activity_log")
                and settings.channel_activity_log
                and channel_id == settings.channel_activity_log
            ):
                success = await self.daily_integration.add_activity_log_entry(
                    message_data
                )
                if success:
                    self.logger.info("Activity log entry added to daily note")
                else:
                    self.logger.warning("Failed to add activity log entry")

            # Daily Tasks チャンネルの処理
            elif (
                self.daily_integration
                and hasattr(settings, "channel_daily_tasks")
                and settings.channel_daily_tasks
                and channel_id == settings.channel_daily_tasks
            ):
                success = await self.daily_integration.add_daily_task_entry(
                    message_data
                )
                if success:
                    self.logger.info("Daily task entry added to daily note")
                else:
                    self.logger.warning("Failed to add daily task entry")

        except Exception as e:
            self.logger.error(
                "Error in daily note integration",
                channel_name=channel_info.name,
                error=str(e),
                exc_info=True,
            )

    async def _handle_audio_attachments(
        self,
        message_data: dict[str, Any],
        channel_info: Any,
        original_message: discord.Message | None = None,
    ) -> None:
        """音声添付ファイルの処理（リアルタイムフィードバック付き）"""
        try:
            metadata = message_data.get("metadata", {})
            attachments = metadata.get("attachments", [])

            # 音声ファイルをフィルタリング
            audio_attachments = [
                att
                for att in attachments
                if att.get("file_category") == "audio"
                or (
                    self.speech_processor
                    and self.speech_processor.is_audio_file(att.get("filename", ""))
                )
            ]

            if not audio_attachments:
                return

            self.logger.info(
                "Processing audio attachments",
                count=len(audio_attachments),
                channel=channel_info.name,
            )

            for attachment in audio_attachments:
                await self._process_single_audio_attachment(
                    attachment, message_data, channel_info, original_message
                )

        except Exception as e:
            self.logger.error(
                "Error processing audio attachments",
                channel_name=channel_info.name,
                error=str(e),
                exc_info=True,
            )

    async def _handle_document_attachments(
        self,
        message_data: dict[str, Any],
        channel_info: Any,
        original_message: Any,
    ) -> None:
        """Handle document, image, and other file attachments"""

        try:
            attachments = message_data.get("attachments", [])
            if not attachments:
                return

            # Filter out audio attachments (already handled)
            audio_extensions = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".wma"}
            document_attachments = [
                att
                for att in attachments
                if not any(
                    att.get("filename", "").lower().endswith(ext)
                    for ext in audio_extensions
                )
            ]

            if not document_attachments:
                return

            self.logger.info(
                f"Processing {len(document_attachments)} document attachment(s)",
                channel=channel_info.name if channel_info else "unknown",
            )

            for attachment in document_attachments:
                filename = attachment.get("filename", "unknown_file")
                file_size = attachment.get("size", 0)

                # Add attachment info to message data for obsidian integration
                if "file_attachments" not in message_data:
                    message_data["file_attachments"] = []

                message_data["file_attachments"].append(
                    {
                        "filename": filename,
                        "url": attachment.get("url"),
                        "size": file_size,
                        "type": "document",
                    }
                )

                self.logger.debug(
                    "Added document attachment to processing queue",
                    filename=filename,
                    size=file_size,
                )

        except Exception as e:
            self.logger.error(
                "Failed to handle document attachments",
                error=str(e),
                exc_info=True,
            )

    async def _process_single_audio_attachment(
        self,
        attachment: dict[str, Any],
        message_data: dict[str, Any],
        channel_info: Any,
        original_message: discord.Message | None = None,
    ) -> None:
        """単一の音声添付ファイルを処理（リアルタイムフィードバック付き）"""
        feedback_message = None

        try:
            attachment_url = attachment.get("url")
            filename = attachment.get("filename", "audio.mp3")

            if not attachment_url:
                self.logger.warning(
                    "No URL found for audio attachment", filename=filename
                )
                return

            # Discord へのリアルタイムフィードバックを開始
            if original_message:
                try:
                    feedback_message = await original_message.reply(
                        f"🎤 音声ファイル `{filename}` の文字起こしを開始します..."
                    )
                except Exception as e:
                    self.logger.warning("Failed to send feedback message", error=str(e))

            # 音声ファイルをダウンロード
            audio_data = await self._download_attachment(attachment_url)
            if not audio_data:
                await self._update_feedback_message(
                    feedback_message,
                    f"❌ 音声ファイル `{filename}` のダウンロードに失敗しました。",
                )
                return

            # 音声を文字起こし
            if not self.speech_processor:
                await self._update_feedback_message(
                    feedback_message,
                    "❌ 音声処理システムが初期化されていません。",
                )
                return

            audio_result = await self.speech_processor.process_audio_file(
                file_data=audio_data, filename=filename, channel_name=channel_info.name
            )

            # 結果に応じてフィードバックを更新
            if audio_result.success and audio_result.transcription:
                self.logger.info(
                    "Audio transcription completed",
                    filename=filename,
                    transcript_length=len(audio_result.transcription.transcript),
                    confidence=audio_result.transcription.confidence,
                )

                # 成功メッセージ
                success_msg = (
                    f"✅ 音声文字起こしが完了しました！\n"
                    f"📝 **ファイル**: `{filename}`\n"
                    f"📊 **信頼度**: {audio_result.transcription.confidence:.2f}\n"
                    f"📄 ノートが Obsidian に保存されました。"
                )
                await self._update_feedback_message(feedback_message, success_msg)

                # 文字起こし結果をメッセージデータに追加
                await self._integrate_audio_transcription(
                    message_data, audio_result, channel_info
                )
            else:
                self.logger.warning(
                    "Audio transcription failed or used fallback",
                    filename=filename,
                    error=audio_result.error_message,
                    fallback_used=audio_result.fallback_used,
                )

                # エラーまたはフォールバックメッセージ
                if audio_result.fallback_used:
                    fallback_msg = (
                        f"⚠️ 音声文字起こしが制限されました\n"
                        f"📝 **ファイル**: `{filename}`\n"
                        f"📊 **理由**: {audio_result.fallback_reason}\n"
                        f"📁 音声ファイルは Obsidian に保存されました。"
                    )
                    await self._update_feedback_message(feedback_message, fallback_msg)
                else:
                    error_msg = (
                        f"❌ 音声文字起こしに失敗しました\n"
                        f"📝 **ファイル**: `{filename}`\n"
                        f"⚠️ **エラー**: {audio_result.error_message or '不明なエラー'}"
                    )
                    await self._update_feedback_message(feedback_message, error_msg)

                # フォールバック結果も統合
                if audio_result.transcription:
                    await self._integrate_audio_transcription(
                        message_data, audio_result, channel_info
                    )

        except Exception as e:
            self.logger.error(
                "Error processing single audio attachment",
                filename=attachment.get("filename", "unknown"),
                error=str(e),
                exc_info=True,
            )

            # 予期しないエラーのフィードバック
            error_msg = (
                f"❌ 音声処理中に予期しないエラーが発生しました\n"
                f"📝 **ファイル**: `{attachment.get('filename', 'unknown')}`\n"
                f"⚠️ **エラー**: {str(e)}"
            )
            await self._update_feedback_message(feedback_message, error_msg)

    async def _download_attachment(self, url: str) -> bytes | None:
        """添付ファイルをダウンロード"""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session, session.get(url) as response:
                if response.status == 200:
                    return await response.read()
                self.logger.error(
                    "Failed to download attachment",
                    url=url,
                    status=response.status,
                )
                return None

        except Exception as e:
            self.logger.error(
                "Error downloading attachment", url=url, error=str(e), exc_info=True
            )
            return None

    async def _integrate_audio_transcription(
        self, message_data: dict[str, Any], audio_result: Any, channel_info: Any
    ) -> None:
        """音声文字起こし結果を Obsidian ノートに統合"""
        try:
            if not self.obsidian_manager or not self.template_engine:
                return

            # 音声処理結果をメッセージデータに追加
            metadata = message_data.get("metadata", {})
            content_info = metadata.get("content", {})

            # 既存のコンテンツに音声文字起こし結果を追加
            original_content = content_info.get("raw_content", "")
            transcription_text = audio_result.transcription.transcript

            # 音声セクションを追加
            audio_section = f"\n\n## 🎤 音声文字起こし\n\n{transcription_text}"

            if audio_result.transcription.confidence > 0.0:
                confidence_level = audio_result.transcription.confidence_level.value
                audio_section += f"\n\n**信頼度**: {audio_result.transcription.confidence:.2f} ({confidence_level})"

            if audio_result.fallback_used:
                audio_section += f"\n\n**注意**: {audio_result.fallback_reason}"
                if audio_result.saved_file_path:
                    audio_section += f"\n**保存先**: `{audio_result.saved_file_path}`"

            # コンテンツを更新
            enhanced_content = original_content + audio_section
            content_info["raw_content"] = enhanced_content
            content_info["has_audio_transcription"] = True
            content_info["audio_confidence"] = audio_result.transcription.confidence

            # AI で処理する場合は、音声文字起こし結果も含めて処理
            if original_content.strip() or transcription_text.strip():
                # 通常の AI 処理フローに任せる（ AIProcessor が音声テキストも処理する）
                pass

            self.logger.info(
                "Audio transcription integrated into message",
                channel=channel_info.name,
                transcript_length=len(transcription_text),
                fallback_used=audio_result.fallback_used,
            )

        except Exception as e:
            self.logger.error(
                "Error integrating audio transcription", error=str(e), exc_info=True
            )

    async def _handle_system_message(self, message_data: dict[str, Any]) -> None:
        """Handle messages from system channels"""
        self.logger.info(
            "Handling system message", channel_name=message_data["channel_info"]["name"]
        )

        # Process system-related messages
        try:
            content = message_data.get("content", "").strip()

            # Detect bot commands (starting with / or !)
            if content.startswith(("//", "!!")):
                command = content.split()[0] if content.split() else ""
                self.logger.info("Bot command detected", command=command)
                # Add command tag for future processing
                if "tags" not in message_data["metadata"]:
                    message_data["metadata"]["tags"] = []
                message_data["metadata"]["tags"].append("command")

            # Detect configuration updates
            config_keywords = ["config", "setting", "configure", "設定", "環境設定"]
            if any(keyword in content.lower() for keyword in config_keywords):
                self.logger.info("Configuration-related content detected")
                # Add config tag for future processing
                if "tags" not in message_data["metadata"]:
                    message_data["metadata"]["tags"] = []
                message_data["metadata"]["tags"].append("config")

            # Log system notifications for monitoring
            if (
                content and len(content) > 10
            ):  # Avoid logging empty or very short messages
                self.logger.debug("System message logged", content_length=len(content))

        except Exception as e:
            self.logger.error("Error processing system message", error=str(e))
