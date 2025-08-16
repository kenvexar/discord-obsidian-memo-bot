"""
AI処理統合システム
"""

import asyncio
import hashlib
import time
from datetime import datetime, timedelta
from typing import Any

from ..utils.mixins import LoggerMixin

from .gemini_client import GeminiAPIError, GeminiClient
from .models import (
    AIModelConfig,
    AIProcessingResult,
    ProcessingCache,
    ProcessingRequest,
    ProcessingSettings,
    ProcessingStats,
)


class AIProcessor(LoggerMixin):
    """AI処理統合システム"""

    def __init__(
        self,
        model_config: AIModelConfig | None = None,
        settings: ProcessingSettings | None = None,
    ):
        """
        AI処理システムの初期化

        Args:
            model_config: AIモデル設定
            settings: 処理設定
        """
        self.settings = settings or ProcessingSettings()
        self.model_config = model_config or AIModelConfig()
        self.gemini_client = GeminiClient(self.model_config)

        # キャッシュとステータス管理
        self._cache: dict[str, ProcessingCache] = {}
        self.stats = ProcessingStats()
        self._processing_queue: list[ProcessingRequest] = []
        self._is_processing = False

        self.logger.info(
            "AI Processor initialized",
            cache_duration=self.settings.cache_duration_hours,
            model=self.model_config.model_name,
        )

    def _generate_content_hash(self, text: str) -> str:
        """テキストのハッシュ値を生成"""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    def _is_text_processable(self, text: str) -> bool:
        """テキストが処理可能かチェック"""
        text_length = len(text.strip())

        if text_length < self.settings.min_text_length:
            self.logger.debug(
                "Text too short for processing",
                length=text_length,
                min_length=self.settings.min_text_length,
            )
            return False

        if text_length > self.settings.max_text_length:
            self.logger.warning(
                "Text too long for processing",
                length=text_length,
                max_length=self.settings.max_text_length,
            )
            return False

        return True

    def _get_from_cache(self, content_hash: str) -> AIProcessingResult | None:
        """キャッシュから結果を取得"""
        if content_hash not in self._cache:
            return None

        cache_entry = self._cache[content_hash]

        # 期限切れチェック
        if cache_entry.is_expired():
            del self._cache[content_hash]
            self.logger.debug("Cache entry expired", content_hash=content_hash)
            return None

        # アクセス情報更新
        cache_entry.access()

        # キャッシュヒット
        result = cache_entry.result
        result.cache_hit = True

        self.logger.debug(
            "Cache hit",
            content_hash=content_hash,
            access_count=cache_entry.access_count,
        )

        return result

    def _save_to_cache(self, content_hash: str, result: AIProcessingResult) -> None:
        """結果をキャッシュに保存"""
        expires_at = datetime.now() + timedelta(
            hours=self.settings.cache_duration_hours
        )

        cache_entry = ProcessingCache(
            content_hash=content_hash,
            result=result,
            created_at=datetime.now(),
            expires_at=expires_at,
        )

        self._cache[content_hash] = cache_entry

        self.logger.debug(
            "Result cached",
            content_hash=content_hash,
            expires_at=expires_at.isoformat(),
        )

    def _clean_expired_cache(self) -> None:
        """期限切れキャッシュを削除"""
        expired_keys = [key for key, cache in self._cache.items() if cache.is_expired()]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            self.logger.info(f"Cleaned {len(expired_keys)} expired cache entries")

    async def process_text(
        self, text: str, message_id: int, force_reprocess: bool = False
    ) -> AIProcessingResult:
        """
        テキストのAI処理を実行

        Args:
            text: 処理対象のテキスト
            message_id: メッセージID
            force_reprocess: 強制再処理フラグ

        Returns:
            AI処理結果
        """
        start_time = time.time()

        # テキストの前処理
        cleaned_text = text.strip()
        content_hash = self._generate_content_hash(cleaned_text)

        # 処理可能性チェック
        if not self._is_text_processable(cleaned_text):
            return AIProcessingResult(
                message_id=message_id,
                processed_at=datetime.now(),
                total_processing_time_ms=int((time.time() - start_time) * 1000),
                errors=["Text is not processable (too short/long or invalid)"],
            )

        # キャッシュチェック
        if not force_reprocess:
            cached_result = self._get_from_cache(content_hash)
            if cached_result:
                # メッセージIDを更新
                cached_result.message_id = message_id
                cached_result.processed_at = datetime.now()

                # 統計更新
                self.stats.update_stats(cached_result)

                return cached_result

        # AI処理実行
        errors = []
        warnings: list[str] = []
        summary = None
        tags = None
        category = None

        try:
            self.logger.info(
                "Starting AI processing",
                message_id=message_id,
                text_length=len(cleaned_text),
                content_hash=content_hash,
            )

            # 並列AI処理
            if (
                self.settings.enable_summary
                or self.settings.enable_tags
                or self.settings.enable_categorization
            ):
                summary_result, tags_result, category_result = await asyncio.wait_for(
                    self.gemini_client.process_all(cleaned_text),
                    timeout=self.settings.timeout_seconds,
                )

                # 結果の割り当て
                if self.settings.enable_summary:
                    summary = summary_result
                if self.settings.enable_tags:
                    tags = tags_result
                if self.settings.enable_categorization:
                    category = category_result

        except asyncio.TimeoutError:
            error_msg = (
                f"Processing timeout after {self.settings.timeout_seconds} seconds"
            )
            errors.append(error_msg)
            self.logger.error(error_msg, message_id=message_id)

        except GeminiAPIError as e:
            error_msg = f"Gemini API error: {str(e)}"
            errors.append(error_msg)
            self.logger.error(
                error_msg,
                message_id=message_id,
                error_code=getattr(e, "error_code", None),
            )

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg, message_id=message_id, exc_info=True)

        # 結果作成
        total_time = int((time.time() - start_time) * 1000)

        result = AIProcessingResult(
            message_id=message_id,
            processed_at=datetime.now(),
            summary=summary,
            tags=tags,
            category=category,
            total_processing_time_ms=total_time,
            cache_hit=False,
            errors=errors,
            warnings=warnings,
        )

        # 成功した場合はキャッシュに保存
        if not errors:
            self._save_to_cache(content_hash, result)

        # 統計更新
        self.stats.update_stats(result)

        self.logger.info(
            "AI processing completed",
            message_id=message_id,
            total_time_ms=total_time,
            has_errors=bool(errors),
            cached=False,
        )

        return result

    async def process_batch(
        self, requests: list[ProcessingRequest]
    ) -> list[AIProcessingResult]:
        """
        バッチ処理

        Args:
            requests: 処理リクエストのリスト

        Returns:
            処理結果のリスト
        """
        self.logger.info(f"Starting batch processing for {len(requests)} requests")

        # 優先度でソート
        sorted_requests = sorted(
            requests, key=lambda r: (r.priority.value, r.requested_at), reverse=True
        )

        results = []

        for request in sorted_requests:
            try:
                result = await self.process_text(
                    text=request.text_content,
                    message_id=request.message_id,
                    force_reprocess=request.force_reprocess,
                )
                results.append(result)

            except Exception as e:
                self.logger.error(
                    "Batch processing item failed",
                    message_id=request.message_id,
                    error=str(e),
                )

                # エラー結果を作成
                error_result = AIProcessingResult(
                    message_id=request.message_id,
                    processed_at=datetime.now(),
                    total_processing_time_ms=0,
                    errors=[f"Batch processing failed: {str(e)}"],
                )
                results.append(error_result)

        self.logger.info(f"Batch processing completed: {len(results)} results")
        return results

    def add_to_queue(self, request: ProcessingRequest) -> None:
        """処理キューに追加"""
        self._processing_queue.append(request)
        self.logger.debug(
            "Request added to queue",
            message_id=request.message_id,
            queue_size=len(self._processing_queue),
        )

    async def process_queue(self) -> list[AIProcessingResult]:
        """キューの処理"""
        if self._is_processing or not self._processing_queue:
            return []

        self._is_processing = True

        try:
            # キューをコピーしてクリア
            requests_to_process = self._processing_queue.copy()
            self._processing_queue.clear()

            # バッチ処理実行
            results = await self.process_batch(requests_to_process)

            return results

        finally:
            self._is_processing = False

    def get_stats(self) -> ProcessingStats:
        """処理統計を取得"""
        # 期限切れキャッシュをクリーンアップ
        self._clean_expired_cache()

        return self.stats

    def get_cache_info(self) -> dict[str, Any]:
        """キャッシュ情報を取得"""
        self._clean_expired_cache()

        total_entries = len(self._cache)
        total_hits = sum(cache.access_count for cache in self._cache.values())

        return {
            "total_entries": total_entries,
            "total_cache_hits": total_hits,
            "cache_hit_rate": self.stats.cache_hits / max(self.stats.total_requests, 1),
            "oldest_entry": min(
                (cache.created_at for cache in self._cache.values()), default=None
            ),
            "newest_entry": max(
                (cache.created_at for cache in self._cache.values()), default=None
            ),
        }

    def clear_cache(self) -> int:
        """キャッシュをクリア"""
        cleared_count = len(self._cache)
        self._cache.clear()
        self.logger.info(f"Cache cleared: {cleared_count} entries removed")
        return cleared_count

    async def generate_embeddings(self, text: str) -> list[float] | None:
        """
        テキストの埋め込みベクトルを生成

        Args:
            text: 対象テキスト

        Returns:
            埋め込みベクトル（失敗時はNone）
        """
        try:
            self.logger.debug("Generating embeddings", text_length=len(text))

            # Geminiクライアントで埋め込み生成
            if hasattr(self.gemini_client, "generate_embeddings"):
                embedding = await self.gemini_client.generate_embeddings(text)
                if embedding and isinstance(embedding, list):
                    return list(embedding)

            # フォールバック: 簡単なハッシュベースのダミー埋め込み
            text_hash = hashlib.sha256(text.encode()).hexdigest()
            embedding = [
                float(int(text_hash[i : i + 2], 16)) / 255.0 for i in range(0, 32, 2)
            ]

            self.logger.warning("Using fallback embedding generation")
            return embedding

        except Exception as e:
            self.logger.error("Failed to generate embeddings", error=str(e))
            return None

    async def summarize_url_content(self, url: str, content: str) -> str | None:
        """
        URL内容を要約

        Args:
            url: 対象URL
            content: ウェブページの内容

        Returns:
            要約テキスト（失敗時はNone）
        """
        try:
            self.logger.debug(
                "Summarizing URL content", url=url, content_length=len(content)
            )

            # プロンプト作成
            prompt = f"""以下のウェブページの内容を日本語で簡潔に要約してください：

URL: {url}

内容:
{content[:2000]}...  # 最初の2000文字のみ

要約は以下の形式で：
- 主要なポイントを3-5行で
- 重要なキーワードを含める
- 読みやすい文章で"""

            summary = await self.gemini_client.generate_summary(prompt)

            if summary:
                self.logger.debug("URL content summarized successfully", url=url)
                return summary.summary.strip()

            return None

        except Exception as e:
            self.logger.error("Failed to summarize URL content", url=url, error=str(e))
            return None

    async def generate_internal_links(
        self, content: str, related_notes: list[dict[str, Any]]
    ) -> list[str]:
        """
        内部リンクを生成

        Args:
            content: 新規ノートの内容
            related_notes: 関連ノートのリスト

        Returns:
            内部リンクのリスト
        """
        try:
            self.logger.debug(
                "Generating internal links",
                content_length=len(content),
                related_notes_count=len(related_notes),
            )

            if not related_notes:
                return []

            # 関連ノート情報を整理
            note_info = []
            for note in related_notes[:10]:  # 上位10件まで
                title = note.get("title", "Untitled")
                similarity = note.get("similarity_score", 0.0)
                preview = note.get("content_preview", "")[:100]

                note_info.append(f"- {title} (類似度: {similarity:.2f}): {preview}")

            # プロンプト作成
            prompt = f"""以下の新しいノートの内容に基づいて、関連する既存のノートへの内部リンクを提案してください：

新しいノートの内容:
{content[:1000]}...

関連する既存のノート:
{chr(10).join(note_info)}

以下の条件で内部リンクを提案してください：
1. 最も関連性の高い3-5個のノートを選択
2. [[ノート名]]の形式でリンクを作成
3. 簡潔な説明を付ける
4. 関連性が低いものは除外

出力形式:
- [[ノート名1]] - 説明
- [[ノート名2]] - 説明"""

            response = await self.gemini_client.generate_summary(prompt)

            if not response:
                return []

            # レスポンスからリンクを抽出
            links = []
            response_text = (
                response.summary if hasattr(response, "summary") else str(response)
            )
            for line in response_text.split("\n"):
                if "[[" in line and "]]" in line:
                    links.append(line.strip())

            self.logger.debug("Internal links generated", links_count=len(links))
            return links

        except Exception as e:
            self.logger.error("Failed to generate internal links", error=str(e))
            return []

    async def health_check(self) -> dict[str, Any]:
        """ヘルスチェック"""
        try:
            # シンプルなテストリクエスト
            test_text = "Hello, this is a test message for health check."
            start_time = time.time()

            await self.gemini_client.generate_summary(test_text)

            response_time = int((time.time() - start_time) * 1000)

            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "model": self.model_config.model_name,
                "cache_entries": len(self._cache),
                "queue_size": len(self._processing_queue),
                "total_requests": self.stats.total_requests,
                "success_rate": self.stats.successful_requests
                / max(self.stats.total_requests, 1),
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "model": self.model_config.model_name,
            }
