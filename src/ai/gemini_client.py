"""
Google Gemini API クライアント
"""

import asyncio
import time
from typing import Any

try:
    import google.genai  # noqa: F401

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

from ..config.settings import get_settings
from ..utils.mixins import LoggerMixin
from .models import (
    AIModelConfig,
    APIUsageInfo,
    CategoryResult,
    ProcessingCategory,
    SummaryResult,
    TagResult,
)


class GeminiAPIError(Exception):
    """Gemini API関連のエラー"""

    def __init__(
        self, message: str, error_code: str | None = None, retryable: bool = False
    ):
        super().__init__(message)
        self.error_code = error_code
        self.retryable = retryable


class RateLimitExceeded(GeminiAPIError):
    """レート制限エラー"""

    def __init__(self, retry_after: int | None = None):
        super().__init__("Rate limit exceeded", retryable=True)
        self.retry_after = retry_after


class GeminiClient(LoggerMixin):
    """Google Gemini API クライアント（新しいgoogle-genai SDK使用）"""

    # プロンプトテンプレート
    SUMMARY_PROMPT = """あなたは優秀なアシスタントです。以下のDiscordでの会話を、重要なポイントを箇条書き3つにまとめてください。

テキスト:
---
{text}
---

要約（箇条書き3点）:"""

    TAG_GENERATION_PROMPT = """あなたは情報を整理する専門家です。以下のテキストから最も重要なキーワードを5つ抽出し、Obsidianで使えるように '#' をつけたタグ形式で、カンマ区切りで出力してください。

例: #Python, #AI, #プログラミング

テキスト:
---
{text}
---

タグ:"""

    CLASSIFICATION_PROMPT = """あなたはタスク管理のスペシャリストです。以下のテキストの内容を分析し、最も関連性の高いカテゴリを以下の選択肢から一つだけ選んでください。

カテゴリ: [仕事, 学習, プロジェクト, 生活, アイデア, その他]

テキスト:
---
{text}
---

カテゴリ:"""

    def __init__(self, model_config: AIModelConfig | None = None):
        """
        Geminiクライアントの初期化

        Args:
            model_config: AIモデル設定
        """
        self.model_config = model_config or AIModelConfig()
        self.api_usage = APIUsageInfo()
        self._client: Any | None = None
        self._last_request_time = 0
        self._min_request_interval = 4.0  # 15 RPM = 4秒間隔

        # APIキーの検証
        settings = get_settings()
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment variables")

        self._initialize_client()

    def _initialize_client(self) -> None:
        """Gemini APIクライアントの初期化"""
        if not GENAI_AVAILABLE:
            raise ImportError(
                "google-genai is not installed. "
                "Please install it with: pip install google-genai"
            )

        try:
            # APIクライアント初期化
            settings = get_settings()
            from google import genai

            self._client = genai.Client(
                api_key=settings.gemini_api_key.get_secret_value()
            )

            self.logger.info(
                "Gemini client initialized",
                model=self.model_config.model_name,
                temperature=self.model_config.temperature,
            )

        except Exception as e:
            self.logger.error("Failed to initialize Gemini client", error=str(e))
            raise GeminiAPIError(f"Failed to initialize Gemini client: {str(e)}") from e

    async def _rate_limit_check(self) -> None:
        """レート制限チェックと待機"""
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time

        if time_since_last_request < self._min_request_interval:
            wait_time = self._min_request_interval - time_since_last_request
            self.logger.debug(f"Rate limiting: waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)

        self._last_request_time = int(time.time())

    async def _call_gemini_api(self, prompt: str, retry_count: int = 3) -> str:
        """
        Gemini APIを呼び出す共通関数

        Args:
            prompt: 送信するプロンプト
            retry_count: リトライ回数

        Returns:
            APIレスポンステキスト

        Raises:
            GeminiAPIError: API呼び出しエラー
        """
        if not self._client:
            raise GeminiAPIError("Gemini client not initialized")

        await self._rate_limit_check()

        for attempt in range(retry_count + 1):
            try:
                self.logger.debug(
                    "Calling Gemini API", attempt=attempt + 1, prompt_length=len(prompt)
                )

                # トークン数を事前にチェック
                token_count = await self._count_tokens(prompt)
                if token_count > self.model_config.max_tokens:
                    raise GeminiAPIError(
                        f"Prompt too long: {token_count} tokens (max: {self.model_config.max_tokens})"
                    )

                # API呼び出し（新しいSDKの設定）
                from google.genai import types

                generation_config = types.GenerateContentConfig(
                    temperature=self.model_config.temperature,
                    top_p=self.model_config.top_p,
                    top_k=self.model_config.top_k,
                    max_output_tokens=self.model_config.max_tokens,
                )

                response = await self._client.aio.models.generate_content(
                    model=self.model_config.model_name,
                    contents=prompt,
                    config=generation_config,
                )

                if not response.text:
                    raise GeminiAPIError("Empty response from Gemini API")

                # 使用量を更新
                self.api_usage.add_usage(token_count)

                self.logger.debug(
                    "Gemini API call successful",
                    response_length=len(response.text),
                    tokens_used=token_count,
                )

                return response.text.strip() if response.text else ""

            except Exception as e:
                error_msg = str(e)

                # レート制限エラーの検出
                if "429" in error_msg or "rate limit" in error_msg.lower():
                    if attempt < retry_count:
                        wait_time = (2**attempt) * 2  # エクスポネンシャルバックオフ
                        self.logger.warning(
                            "Rate limit hit, retrying",
                            attempt=attempt + 1,
                            wait_time=wait_time,
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    raise RateLimitExceeded() from e

                # その他のAPIエラー
                self.logger.error(
                    "Gemini API call failed", attempt=attempt + 1, error=error_msg
                )

                if attempt == retry_count:
                    raise GeminiAPIError(
                        f"API call failed after {retry_count + 1} attempts: {error_msg}"
                    ) from e

                # リトライ前の待機
                await asyncio.sleep(1 * (attempt + 1))

        raise GeminiAPIError("Unexpected error in API call")

    async def _count_tokens(self, text: str) -> int:
        """
        テキストのトークン数をカウント

        Args:
            text: カウント対象のテキスト

        Returns:
            トークン数
        """
        try:
            if self._client:
                response = await self._client.aio.models.count_tokens(
                    model=self.model_config.model_name,
                    contents=text,
                )
                return int(response.total_tokens)
            # フォールバック: 概算計算
            return len(text.encode("utf-8")) // 4
        except Exception as e:
            self.logger.warning("Failed to count tokens, using fallback", error=str(e))
            return len(text.encode("utf-8")) // 4

    async def generate_summary(self, text: str) -> SummaryResult:
        """
        テキストの要約を生成

        Args:
            text: 要約対象のテキスト

        Returns:
            要約結果
        """
        start_time = time.time()

        try:
            prompt = self.SUMMARY_PROMPT.format(text=text)
            response_text = await self._call_gemini_api(prompt)

            # 箇条書きポイントを抽出
            key_points = []
            for line in response_text.split("\n"):
                line = line.strip()
                if line and (
                    line.startswith("・")
                    or line.startswith("-")
                    or line.startswith("*")
                ):
                    # 記号を除去してポイントを抽出
                    point = line.lstrip("・-*").strip()
                    if point:
                        key_points.append(point)

            processing_time = int((time.time() - start_time) * 1000)

            return SummaryResult(
                summary=response_text,
                key_points=key_points,
                processing_time_ms=processing_time,
                model_used=self.model_config.model_name,
            )

        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            self.logger.error("Failed to generate summary", error=str(e))

            return SummaryResult(
                summary=f"要約生成中にエラーが発生しました: {str(e)}",
                key_points=[],
                processing_time_ms=processing_time,
                model_used=self.model_config.model_name,
            )

    async def extract_tags(self, text: str) -> TagResult:
        """
        テキストからタグを抽出

        Args:
            text: タグ抽出対象のテキスト

        Returns:
            タグ抽出結果
        """
        start_time = time.time()

        try:
            prompt = self.TAG_GENERATION_PROMPT.format(text=text)
            response_text = await self._call_gemini_api(prompt)

            # タグを抽出して正規化
            raw_tags = [tag.strip() for tag in response_text.split(",")]
            tags = []
            raw_keywords = []

            for tag in raw_tags:
                if tag:
                    # #を除去してキーワードを取得
                    keyword = tag.lstrip("#").strip()
                    if keyword:
                        raw_keywords.append(keyword)
                        # 正規化されたタグを追加
                        formatted_tag = f"#{keyword}"
                        tags.append(formatted_tag)

            processing_time = int((time.time() - start_time) * 1000)

            return TagResult(
                tags=tags[:5],  # 最大5個まで
                raw_keywords=raw_keywords[:5],
                processing_time_ms=processing_time,
                model_used=self.model_config.model_name,
            )

        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            self.logger.error("Failed to extract tags", error=str(e))

            return TagResult(
                tags=[],
                raw_keywords=[],
                processing_time_ms=processing_time,
                model_used=self.model_config.model_name,
            )

    async def classify_category(self, text: str) -> CategoryResult:
        """
        テキストのカテゴリを分類

        Args:
            text: 分類対象のテキスト

        Returns:
            カテゴリ分類結果
        """
        start_time = time.time()

        try:
            prompt = self.CLASSIFICATION_PROMPT.format(text=text)
            response_text = await self._call_gemini_api(prompt)

            # カテゴリ名を正規化
            category_text = response_text.lower().strip()

            # カテゴリマッピング
            category_mapping = {
                "仕事": ProcessingCategory.WORK,
                "work": ProcessingCategory.WORK,
                "学習": ProcessingCategory.LEARNING,
                "learning": ProcessingCategory.LEARNING,
                "プロジェクト": ProcessingCategory.PROJECT,
                "project": ProcessingCategory.PROJECT,
                "生活": ProcessingCategory.LIFE,
                "life": ProcessingCategory.LIFE,
                "アイデア": ProcessingCategory.IDEA,
                "idea": ProcessingCategory.IDEA,
                "その他": ProcessingCategory.OTHER,
                "other": ProcessingCategory.OTHER,
            }

            # マッチするカテゴリを探索
            detected_category = ProcessingCategory.OTHER
            confidence = 0.5

            for key, cat in category_mapping.items():
                if key in category_text:
                    detected_category = cat
                    confidence = 0.8
                    break

            processing_time = int((time.time() - start_time) * 1000)

            return CategoryResult(
                category=detected_category,
                confidence_score=confidence,
                reasoning=f"分類根拠: {response_text}",
                processing_time_ms=processing_time,
                model_used=self.model_config.model_name,
            )

        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            self.logger.error("Failed to classify category", error=str(e))

            return CategoryResult(
                category=ProcessingCategory.OTHER,
                confidence_score=0.0,
                reasoning=f"分類エラー: {str(e)}",
                processing_time_ms=processing_time,
                model_used=self.model_config.model_name,
            )

    async def process_all(
        self, text: str
    ) -> tuple[SummaryResult, TagResult, CategoryResult]:
        """
        すべてのAI処理を並列実行

        Args:
            text: 処理対象のテキスト

        Returns:
            要約、タグ、カテゴリの結果タプル
        """
        self.logger.info("Starting parallel AI processing", text_length=len(text))

        # 並列実行
        summary_task = self.generate_summary(text)
        tags_task = self.extract_tags(text)
        category_task = self.classify_category(text)

        try:
            summary, tags, category = await asyncio.gather(
                summary_task, tags_task, category_task, return_exceptions=True
            )

            # 例外処理
            if isinstance(summary, Exception):
                self.logger.error("Summary generation failed", error=str(summary))
                summary = SummaryResult(
                    summary="要約生成に失敗しました",
                    processing_time_ms=0,
                    model_used=self.model_config.model_name,
                )

            if isinstance(tags, Exception):
                self.logger.error("Tag extraction failed", error=str(tags))
                tags = TagResult(
                    tags=[],
                    raw_keywords=[],
                    processing_time_ms=0,
                    model_used=self.model_config.model_name,
                )

            if isinstance(category, Exception):
                self.logger.error("Category classification failed", error=str(category))
                category = CategoryResult(
                    category=ProcessingCategory.OTHER,
                    confidence_score=0.0,
                    processing_time_ms=0,
                    model_used=self.model_config.model_name,
                )

            # 型チェック（例外ではない場合のみ処理時間を記録）
            summary_time = (
                summary.processing_time_ms if isinstance(summary, SummaryResult) else 0
            )
            tags_time = tags.processing_time_ms if isinstance(tags, TagResult) else 0
            category_time = (
                category.processing_time_ms
                if isinstance(category, CategoryResult)
                else 0
            )

            self.logger.info(
                "Parallel AI processing completed",
                summary_time=summary_time,
                tags_time=tags_time,
                category_time=category_time,
            )

            # 例外がない場合のみ正常な結果を返す
            if (
                isinstance(summary, SummaryResult)
                and isinstance(tags, TagResult)
                and isinstance(category, CategoryResult)
            ):
                return summary, tags, category
            # 例外があった場合はエラーを発生
            raise GeminiAPIError("One or more parallel processing tasks failed")

        except Exception as e:
            self.logger.error("Parallel processing failed", error=str(e))
            raise GeminiAPIError(f"Parallel processing failed: {str(e)}") from e

    def get_usage_info(self) -> APIUsageInfo:
        """API使用量情報を取得"""
        return self.api_usage

    def reset_usage_info(self) -> None:
        """API使用量情報をリセット"""
        self.api_usage = APIUsageInfo()
        self.logger.info("API usage info reset")
