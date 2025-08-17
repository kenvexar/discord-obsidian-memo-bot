"""
Advanced note analyzer with semantic search and AI-powered features
"""

import re
from datetime import datetime
from typing import Any, Union

from ..obsidian.file_manager import ObsidianFileManager
from ..utils.mixins import LoggerMixin
from .mock_processor import MockAIProcessor
from .processor import AIProcessor
from .url_processor import URLContentExtractor
from .vector_store import SemanticSearchResult, VectorStore

# Settings loaded lazily to avoid circular imports


class AdvancedNoteAnalyzer(LoggerMixin):
    """高度なノート分析システム"""

    def __init__(
        self,
        obsidian_file_manager: "ObsidianFileManager",
        ai_processor: Union["AIProcessor", "MockAIProcessor"],
    ):
        """
        初期化

        Args:
            obsidian_file_manager: Obsidianファイルマネージャー
            ai_processor: AI処理システム
        """
        self.file_manager = obsidian_file_manager
        self.ai_processor = ai_processor

        # コンポーネントの初期化
        self.vector_store = VectorStore(
            obsidian_file_manager=obsidian_file_manager, ai_processor=ai_processor
        )
        self.url_extractor = URLContentExtractor()

        # 設定
        self.max_related_notes = 10
        self.min_similarity_threshold = 0.3
        self.max_internal_links = 5

        self.logger.info("Advanced note analyzer initialized")

    async def analyze_note_content(
        self,
        content: str,
        title: str,
        file_path: str | None = None,
        include_url_processing: bool = True,
        include_related_notes: bool = True,
    ) -> dict[str, Any]:
        """
        ノート内容の包括的な分析

        Args:
            content: ノート内容
            title: ノートタイトル
            file_path: ファイルパス（オプション）
            include_url_processing: URL処理を含むかどうか
            include_related_notes: 関連ノート分析を含むかどうか

        Returns:
            分析結果
        """
        try:
            self.logger.info(
                "Starting comprehensive note analysis",
                title=title,
                content_length=len(content),
                file_path=file_path,
            )

            analysis_results = {}

            # 1. URL内容処理と要約
            if include_url_processing:
                url_results = await self._process_urls_in_content(content)
                analysis_results["url_processing"] = url_results

                # URL要約をコンテンツに統合
                if url_results.get("summaries"):
                    content = await self._integrate_url_summaries(
                        content, url_results["summaries"]
                    )

            # 2. 関連ノート分析
            related_notes = []
            if include_related_notes:
                related_notes = await self._find_related_notes(
                    content, exclude_file=file_path
                )
                analysis_results["related_notes"] = {
                    "results": [
                        {
                            "file_path": note.file_path,
                            "title": note.title,
                            "similarity_score": note.similarity_score,
                            "content_preview": note.content_preview,
                        }
                        for note in related_notes
                    ]
                }

            # 3. 内部リンク提案
            internal_links = []
            if related_notes:
                internal_links = await self._generate_internal_links(
                    content, related_notes
                )
                analysis_results["internal_links"] = {"suggestions": internal_links}

            # 4. コンテンツの最終統合
            enhanced_content = await self._enhance_content_with_links(
                content, internal_links, analysis_results.get("url_processing", {})
            )
            analysis_results["enhanced_content"] = {"content": enhanced_content}

            # 5. ベクトルストアにノートを追加（新規ノートの場合）
            if file_path and enhanced_content:
                await self._add_to_vector_store(file_path, title, enhanced_content)

            analysis_results.update(
                {
                    "original_content": {"content": content},
                    "title": {"value": title},
                    "file_path": {"path": file_path or ""},
                    "analyzed_at": {"timestamp": datetime.now().isoformat()},
                    "content_stats": self._get_content_stats(content),
                }
            )

            self.logger.info(
                "Note analysis completed",
                title=title,
                related_notes_count=len(related_notes),
                internal_links_count=len(internal_links),
                urls_processed=len(
                    analysis_results.get("url_processing", {}).get("processed_urls", [])
                ),
            )

            return analysis_results

        except Exception as e:
            self.logger.error(
                "Failed to analyze note content",
                title=title,
                error=str(e),
                exc_info=True,
            )
            return {
                "error": str(e),
                "title": title,
                "file_path": file_path,
                "analyzed_at": datetime.now().isoformat(),
            }

    async def search_related_notes(
        self, query: str, limit: int = 10, min_similarity: float = 0.1
    ) -> list[dict[str, Any]]:
        """
        関連ノートを検索

        Args:
            query: 検索クエリ
            limit: 結果数制限
            min_similarity: 最小類似度

        Returns:
            検索結果
        """
        try:
            results = await self.vector_store.search_similar_notes(
                query_text=query, limit=limit, min_similarity=min_similarity
            )

            return [
                {
                    "file_path": result.file_path,
                    "title": result.title,
                    "similarity_score": result.similarity_score,
                    "content_preview": result.content_preview,
                    "metadata": result.metadata,
                }
                for result in results
            ]

        except Exception as e:
            self.logger.error("Failed to search related notes", error=str(e))
            return []

    async def rebuild_vector_index(self, force: bool = False) -> dict[str, Any]:
        """
        ベクトルインデックスを再構築

        Args:
            force: 強制再構築

        Returns:
            再構築結果
        """
        try:
            self.logger.info("Starting vector index rebuild", force=force)

            start_time = datetime.now()
            await self.vector_store.build_index(force_rebuild=force)
            end_time = datetime.now()

            duration = (end_time - start_time).total_seconds()
            stats = await self.vector_store.get_embedding_stats()

            result = {
                "success": True,
                "duration_seconds": duration,
                "stats": stats,
                "rebuilt_at": end_time.isoformat(),
            }

            self.logger.info(
                "Vector index rebuild completed",
                duration=duration,
                embeddings=stats.get("total_embeddings", 0),
            )

            return result

        except Exception as e:
            self.logger.error(
                "Failed to rebuild vector index", error=str(e), exc_info=True
            )
            return {
                "success": False,
                "error": str(e),
                "attempted_at": datetime.now().isoformat(),
            }

    async def _process_urls_in_content(self, content: str) -> dict[str, Any]:
        """コンテンツ内のURLを処理"""
        try:
            # URLを抽出・処理
            url_results = await self.url_extractor.process_urls_in_text(
                content, max_urls=3
            )

            if not url_results.get("processed_urls"):
                return url_results

            # 各URLの内容を要約
            summaries = []
            for url_data in url_results["processed_urls"]:
                try:
                    summary = await self.ai_processor.summarize_url_content(
                        url_data["url"], url_data["content"]
                    )

                    if summary:
                        summaries.append(
                            {
                                "url": url_data["url"],
                                "title": url_data["title"],
                                "summary": summary,
                                "original_content_length": url_data["content_length"],
                            }
                        )

                except Exception as e:
                    self.logger.warning(
                        "Failed to summarize URL content",
                        url=url_data["url"],
                        error=str(e),
                    )

            url_results["summaries"] = summaries
            return url_results

        except Exception as e:
            self.logger.error("Failed to process URLs in content", error=str(e))
            return {"error": str(e)}

    async def _integrate_url_summaries(
        self, content: str, summaries: list[dict[str, Any]]
    ) -> str:
        """URL要約をコンテンツに統合（有効なURLがない場合はスキップ）"""
        try:
            if not summaries:
                return content

            # 既存のURL要約セクションをチェックして重複を避ける
            if "## 📎 URL要約" in content:
                self.logger.debug("URL要約セクションが既に存在するため、スキップします")
                return content

            # 有効な要約のみをフィルタリング
            valid_summaries = []
            for summary_data in summaries:
                summary_text = summary_data.get("summary", "").strip()
                url = summary_data.get("url", "").strip()

                # 有効なURLかチェック（Discord無効リンクなどを除外）
                is_valid_url = (
                    url
                    and not url.endswith("/channels/")  # Discord無効リンク
                    and "discord.com/channels/" not in url  # Discord不完全リンク
                    and summary_text
                    and not summary_text.startswith(
                        "Discordの会話の要約が提供されていません"
                    )
                    and "URLへのアクセス権限がない" not in summary_text
                    and "箇条書き3点による要約を作成できません" not in summary_text
                    and "URLから情報を取得して要約することはできません"
                    not in summary_text
                    and "提供されたテキストからは" not in summary_text
                    and "不足しているため、正確な要約はできません" not in summary_text
                )

                if is_valid_url:
                    valid_summaries.append(summary_data)

            # 有効な要約がない場合はセクションを追加しない
            if not valid_summaries:
                self.logger.debug("有効なURL要約がないため、セクションを追加しません")
                return content

            # コンテンツの末尾にURL要約セクションを追加
            url_section_parts = ["\n\n## 📎 URL要約\n"]

            for summary_data in valid_summaries:
                url_section_parts.append(
                    f"### {summary_data['title']}\n"
                    f"🔗 {summary_data['url']}\n\n"
                    f"{summary_data['summary']}\n"
                )

            return content + "".join(url_section_parts)

        except Exception as e:
            self.logger.warning("Failed to integrate URL summaries", error=str(e))
            return content

    async def _find_related_notes(
        self, content: str, exclude_file: str | None = None
    ) -> list[SemanticSearchResult]:
        """関連ノートを検索"""
        try:
            exclude_files = {exclude_file} if exclude_file else set()

            results = await self.vector_store.search_similar_notes(
                query_text=content,
                limit=self.max_related_notes,
                min_similarity=self.min_similarity_threshold,
                exclude_files=exclude_files,
            )

            return results

        except Exception as e:
            self.logger.error("Failed to find related notes", error=str(e))
            return []

    async def _generate_internal_links(
        self, content: str, related_notes: list[SemanticSearchResult]
    ) -> list[str]:
        """内部リンクを生成"""
        try:
            if not related_notes:
                return []

            # SemanticSearchResultを辞書形式に変換
            related_notes_dict = [
                {
                    "title": note.title,
                    "similarity_score": note.similarity_score,
                    "content_preview": note.content_preview,
                    "file_path": note.file_path,
                }
                for note in related_notes[: self.max_internal_links]
            ]

            links = await self.ai_processor.generate_internal_links(
                content, related_notes_dict
            )

            return links

        except Exception as e:
            self.logger.error("Failed to generate internal links", error=str(e))
            return []

    async def _enhance_content_with_links(
        self,
        content: str,
        internal_links: list[str],
        url_processing_results: dict[str, Any],
    ) -> str:
        """コンテンツにリンクを追加して強化"""
        try:
            enhanced_content = content

            # URL要約が既に追加されているかチェック
            if url_processing_results.get("summaries"):
                url_summaries = url_processing_results["summaries"]
                enhanced_content = await self._integrate_url_summaries(
                    content, url_summaries
                )

            # 内部リンクセクションを追加
            if internal_links:
                links_section = "\n\n## 🔗 関連ノート\n\n"
                links_section += "\n".join(internal_links)
                enhanced_content += links_section

            return enhanced_content

        except Exception as e:
            self.logger.warning("Failed to enhance content with links", error=str(e))
            return content

    async def _add_to_vector_store(
        self, file_path: str, title: str, content: str
    ) -> None:
        """ベクトルストアにノートを追加"""
        try:
            await self.vector_store.add_note_embedding(
                file_path=file_path, title=title, content=content
            )

        except Exception as e:
            self.logger.warning(
                "Failed to add note to vector store", file_path=file_path, error=str(e)
            )

    def _get_content_stats(self, content: str) -> dict[str, Any]:
        """コンテンツの統計情報を取得"""
        try:
            lines = content.split("\n")
            words = content.split()

            # 見出し数をカウント
            headers = re.findall(r"^#{1,6}\s+.+$", content, re.MULTILINE)

            # リンク数をカウント
            markdown_links = re.findall(r"\[([^\]]+)\]\([^)]+\)", content)
            wiki_links = re.findall(r"\[\[([^\]]+)\]\]", content)

            return {
                "character_count": len(content),
                "word_count": len(words),
                "line_count": len(lines),
                "header_count": len(headers),
                "markdown_link_count": len(markdown_links),
                "wiki_link_count": len(wiki_links),
                "total_link_count": len(markdown_links) + len(wiki_links),
            }

        except Exception as e:
            self.logger.warning("Failed to get content stats", error=str(e))
            return {}

    async def get_system_stats(self) -> dict[str, Any]:
        """システム統計情報を取得"""
        try:
            vector_stats = await self.vector_store.get_embedding_stats()

            return {
                "vector_store": vector_stats,
                "analyzer_config": {
                    "max_related_notes": self.max_related_notes,
                    "min_similarity_threshold": self.min_similarity_threshold,
                    "max_internal_links": self.max_internal_links,
                },
                "system_status": "operational",
                "last_updated": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error("Failed to get system stats", error=str(e))
            return {"error": str(e)}
