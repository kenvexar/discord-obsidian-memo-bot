"""
Obsidian metadata management
"""

from datetime import datetime
from typing import Any

from ..utils import LoggerMixin
from .file_manager import ObsidianFileManager
from .models import ObsidianNote, VaultStats


class MetadataManager(LoggerMixin):
    """Obsidian metadata management and analysis"""

    def __init__(self, file_manager: ObsidianFileManager):
        """
        Initialize metadata manager

        Args:
            file_manager: File manager instance
        """
        self.file_manager = file_manager
        self.logger.info("Metadata manager initialized")

    async def update_note_metadata(
        self, note: ObsidianNote, updates: dict[str, Any]
    ) -> bool:
        """
        ノートのメタデータを更新

        Args:
            note: 更新対象ノート
            updates: 更新内容

        Returns:
            更新成功可否
        """
        try:
            # フロントマターの更新
            for key, value in updates.items():
                if hasattr(note.frontmatter, key):
                    setattr(note.frontmatter, key, value)
                else:
                    self.logger.warning(
                        "Unknown frontmatter field",
                        field=key,
                        note_path=str(note.file_path),
                    )

            # 更新時刻の設定
            note.frontmatter.modified = datetime.now().isoformat()
            note.modified_at = datetime.now()

            # ファイル保存
            success = await self.file_manager.update_note(note)

            if success:
                self.logger.info(
                    "Note metadata updated",
                    note_path=str(note.file_path),
                    updates=list(updates.keys()),
                )

            return success

        except Exception as e:
            self.logger.error(
                "Failed to update note metadata",
                note_path=str(note.file_path),
                error=str(e),
                exc_info=True,
            )
            return False

    async def bulk_update_metadata(
        self, filters: dict[str, Any], updates: dict[str, Any], limit: int = 100
    ) -> dict[str, Any]:
        """
        条件に合致するノートのメタデータを一括更新

        Args:
            filters: 対象ノートの条件
            updates: 更新内容
            limit: 処理上限数

        Returns:
            更新結果
        """
        try:
            self.logger.info(
                "Starting bulk metadata update",
                filters=filters,
                updates=list(updates.keys()),
                limit=limit,
            )

            results: dict[str, Any] = {
                "processed": 0,
                "updated": 0,
                "errors": 0,
                "updated_notes": [],
            }

            # 条件に合致するノートを検索
            notes = await self.file_manager.search_notes(
                query=filters.get("query"),
                folder=filters.get("folder"),
                status=filters.get("status"),
                tags=filters.get("tags"),
                date_from=filters.get("date_from"),
                date_to=filters.get("date_to"),
                limit=limit,
            )

            for note in notes:
                results["processed"] += 1

                try:
                    success = await self.update_note_metadata(note, updates)

                    if success:
                        results["updated"] += 1
                        results["updated_notes"].append(
                            {
                                "title": note.title,
                                "path": str(
                                    note.file_path.relative_to(
                                        self.file_manager.vault_path
                                    )
                                ),
                            }
                        )
                    else:
                        results["errors"] += 1

                except Exception as e:
                    results["errors"] += 1
                    self.logger.error(
                        "Error in bulk update",
                        note_path=str(note.file_path),
                        error=str(e),
                        exc_info=True,
                    )

            self.logger.info(
                "Bulk metadata update completed",
                processed=results["processed"],
                updated=results["updated"],
                errors=results["errors"],
            )

            return results

        except Exception as e:
            self.logger.error(
                "Failed to perform bulk metadata update", error=str(e), exc_info=True
            )
            return {"processed": 0, "updated": 0, "errors": 1, "updated_notes": []}

    async def analyze_tag_usage(self, limit: int = 1000) -> dict[str, Any]:
        """
        タグ使用状況を分析

        Args:
            limit: 分析対象ノート数

        Returns:
            タグ分析結果
        """
        try:
            self.logger.info("Starting tag usage analysis", limit=limit)

            # ノートを取得
            notes = await self.file_manager.search_notes(limit=limit)

            analysis: dict[str, Any] = {
                "total_notes": len(notes),
                "notes_with_tags": 0,
                "total_tags": 0,
                "unique_tags": set(),
                "tag_frequency": {},
                "ai_tags_frequency": {},
                "manual_tags_frequency": {},
                "co_occurrence": {},
                "orphaned_tags": set(),
                "most_popular_tags": [],
                "tag_trends": {},
            }

            for note in notes:
                # タグを持つノートの数
                all_tags = note.frontmatter.ai_tags + note.frontmatter.tags
                if all_tags:
                    analysis["notes_with_tags"] += 1

                # AIタグの分析
                for tag in note.frontmatter.ai_tags:
                    clean_tag = tag.lstrip("#")
                    analysis["unique_tags"].add(clean_tag)
                    analysis["tag_frequency"][clean_tag] = (
                        analysis["tag_frequency"].get(clean_tag, 0) + 1
                    )
                    analysis["ai_tags_frequency"][clean_tag] = (
                        analysis["ai_tags_frequency"].get(clean_tag, 0) + 1
                    )
                    analysis["total_tags"] += 1

                # 手動タグの分析
                for tag in note.frontmatter.tags:
                    clean_tag = tag.lstrip("#")
                    analysis["unique_tags"].add(clean_tag)
                    analysis["tag_frequency"][clean_tag] = (
                        analysis["tag_frequency"].get(clean_tag, 0) + 1
                    )
                    analysis["manual_tags_frequency"][clean_tag] = (
                        analysis["manual_tags_frequency"].get(clean_tag, 0) + 1
                    )
                    analysis["total_tags"] += 1

                # タグ共起分析
                if len(all_tags) > 1:
                    clean_tags = [tag.lstrip("#") for tag in all_tags]
                    for i, tag1 in enumerate(clean_tags):
                        for tag2 in clean_tags[i + 1 :]:
                            pair = tuple(sorted([tag1, tag2]))
                            analysis["co_occurrence"][pair] = (
                                analysis["co_occurrence"].get(pair, 0) + 1
                            )

            # 人気タグの抽出（上位20個）
            sorted_tags = sorted(
                analysis["tag_frequency"].items(), key=lambda x: x[1], reverse=True
            )[:20]
            analysis["most_popular_tags"] = [
                {
                    "tag": tag,
                    "count": count,
                    "percentage": (count / analysis["total_tags"]) * 100,
                }
                for tag, count in sorted_tags
            ]

            # 孤立タグの特定（使用回数が1回のみ）
            analysis["orphaned_tags"] = {
                tag for tag, count in analysis["tag_frequency"].items() if count == 1
            }

            # 統計の計算
            analysis["unique_tag_count"] = len(analysis["unique_tags"])
            analysis["average_tags_per_note"] = analysis["total_tags"] / max(
                analysis["total_notes"], 1
            )
            analysis["tag_coverage"] = (
                analysis["notes_with_tags"] / max(analysis["total_notes"], 1)
            ) * 100

            # セットをリストに変換（JSON化のため）
            analysis["unique_tags"] = list(analysis["unique_tags"])
            analysis["orphaned_tags"] = list(analysis["orphaned_tags"])

            self.logger.info(
                "Tag usage analysis completed",
                total_notes=analysis["total_notes"],
                unique_tags=analysis["unique_tag_count"],
                tag_coverage=f"{analysis['tag_coverage']:.1f}%",
            )

            return analysis

        except Exception as e:
            self.logger.error(
                "Failed to analyze tag usage", error=str(e), exc_info=True
            )
            return {
                "total_notes": 0,
                "unique_tag_count": 0,
                "tag_coverage": 0,
                "error": str(e),
            }

    async def analyze_content_patterns(self, limit: int = 500) -> dict[str, Any]:
        """
        コンテンツパターンを分析

        Args:
            limit: 分析対象ノート数

        Returns:
            コンテンツパターン分析結果
        """
        try:
            self.logger.info("Starting content pattern analysis", limit=limit)

            notes = await self.file_manager.search_notes(limit=limit)

            analysis: dict[str, Any] = {
                "total_notes": len(notes),
                "content_length_stats": {
                    "min": float("inf"),
                    "max": 0,
                    "average": 0,
                    "median": 0,
                },
                "ai_processing_stats": {
                    "processed_notes": 0,
                    "average_processing_time": 0,
                    "total_processing_time": 0,
                },
                "category_distribution": {},
                "source_type_distribution": {},
                "status_distribution": {},
                "creation_time_patterns": {"hourly": {}, "daily": {}, "monthly": {}},
                "word_frequency": {},
                "common_phrases": [],
            }

            content_lengths = []
            processing_times = []

            for note in notes:
                # コンテンツ長統計
                content_length = len(note.content)
                content_lengths.append(content_length)

                analysis["content_length_stats"]["min"] = min(
                    analysis["content_length_stats"]["min"], content_length
                )
                analysis["content_length_stats"]["max"] = max(
                    analysis["content_length_stats"]["max"], content_length
                )

                # AI処理統計
                if note.frontmatter.ai_processed:
                    analysis["ai_processing_stats"]["processed_notes"] += 1

                    if note.frontmatter.ai_processing_time:
                        processing_times.append(note.frontmatter.ai_processing_time)
                        analysis["ai_processing_stats"]["total_processing_time"] += (
                            note.frontmatter.ai_processing_time
                        )

                # カテゴリ分布
                category = note.frontmatter.ai_category or "未分類"
                analysis["category_distribution"][category] = (
                    analysis["category_distribution"].get(category, 0) + 1
                )

                # ソースタイプ分布
                source_type = note.frontmatter.source_type
                analysis["source_type_distribution"][source_type] = (
                    analysis["source_type_distribution"].get(source_type, 0) + 1
                )

                # ステータス分布
                status = note.frontmatter.status.value
                analysis["status_distribution"][status] = (
                    analysis["status_distribution"].get(status, 0) + 1
                )

                # 作成時間パターン
                created_at = note.created_at
                hour = created_at.hour
                day = created_at.strftime("%A")
                month = created_at.strftime("%B")

                analysis["creation_time_patterns"]["hourly"][hour] = (
                    analysis["creation_time_patterns"]["hourly"].get(hour, 0) + 1
                )
                analysis["creation_time_patterns"]["daily"][day] = (
                    analysis["creation_time_patterns"]["daily"].get(day, 0) + 1
                )
                analysis["creation_time_patterns"]["monthly"][month] = (
                    analysis["creation_time_patterns"]["monthly"].get(month, 0) + 1
                )

                # 単語頻度分析（簡易版）
                words = note.content.lower().split()
                for word in words:
                    if len(word) > 3:  # 3文字以上の単語のみ
                        clean_word = "".join(c for c in word if c.isalnum())
                        if clean_word:
                            analysis["word_frequency"][clean_word] = (
                                analysis["word_frequency"].get(clean_word, 0) + 1
                            )

            # 統計の計算
            if content_lengths:
                analysis["content_length_stats"]["average"] = sum(
                    content_lengths
                ) / len(content_lengths)
                content_lengths.sort()
                median_index = len(content_lengths) // 2
                analysis["content_length_stats"]["median"] = content_lengths[
                    median_index
                ]

            if processing_times:
                analysis["ai_processing_stats"]["average_processing_time"] = sum(
                    processing_times
                ) / len(processing_times)

            # 頻出単語（上位20個）
            sorted_words = sorted(
                analysis["word_frequency"].items(), key=lambda x: x[1], reverse=True
            )[:20]
            analysis["common_words"] = [
                {"word": word, "count": count} for word, count in sorted_words
            ]

            # inf値の処理
            if analysis["content_length_stats"]["min"] == float("inf"):
                analysis["content_length_stats"]["min"] = 0

            self.logger.info(
                "Content pattern analysis completed",
                total_notes=analysis["total_notes"],
                average_length=analysis["content_length_stats"]["average"],
                ai_processed=analysis["ai_processing_stats"]["processed_notes"],
            )

            return analysis

        except Exception as e:
            self.logger.error(
                "Failed to analyze content patterns", error=str(e), exc_info=True
            )
            return {"total_notes": 0, "error": str(e)}

    async def generate_metadata_report(self) -> dict[str, Any]:
        """
        包括的なメタデータレポートを生成

        Returns:
            メタデータレポート
        """
        try:
            self.logger.info("Generating comprehensive metadata report")

            # 基本統計
            vault_stats = await self.file_manager.get_vault_stats()

            # タグ分析
            tag_analysis = await self.analyze_tag_usage(limit=1000)

            # コンテンツパターン分析
            content_analysis = await self.analyze_content_patterns(limit=500)

            # レポート生成
            report = {
                "generated_at": datetime.now().isoformat(),
                "vault_overview": {
                    "total_notes": vault_stats.total_notes,
                    "total_size_mb": round(
                        vault_stats.total_size_bytes / (1024 * 1024), 2
                    ),
                    "ai_processed_notes": vault_stats.ai_processed_notes,
                    "average_ai_processing_time": vault_stats.average_ai_processing_time,
                },
                "folder_distribution": vault_stats.notes_by_folder,
                "category_distribution": vault_stats.notes_by_category,
                "status_distribution": vault_stats.notes_by_status,
                "creation_trends": {
                    "notes_created_today": vault_stats.notes_created_today,
                    "notes_created_this_week": vault_stats.notes_created_this_week,
                    "notes_created_this_month": vault_stats.notes_created_this_month,
                },
                "tag_insights": {
                    "total_tags": tag_analysis.get("total_tags", 0),
                    "unique_tags": tag_analysis.get("unique_tag_count", 0),
                    "tag_coverage": tag_analysis.get("tag_coverage", 0),
                    "most_popular_tags": tag_analysis.get("most_popular_tags", [])[:10],
                    "orphaned_tags_count": len(tag_analysis.get("orphaned_tags", [])),
                },
                "content_insights": {
                    "average_content_length": content_analysis.get(
                        "content_length_stats", {}
                    ).get("average", 0),
                    "common_words": content_analysis.get("common_words", [])[:10],
                    "creation_time_patterns": content_analysis.get(
                        "creation_time_patterns", {}
                    ),
                },
                "recommendations": self._generate_recommendations(
                    vault_stats, tag_analysis, content_analysis
                ),
            }

            self.logger.info("Metadata report generated successfully")
            return report

        except Exception as e:
            self.logger.error(
                "Failed to generate metadata report", error=str(e), exc_info=True
            )
            return {"generated_at": datetime.now().isoformat(), "error": str(e)}

    def _generate_recommendations(
        self,
        vault_stats: VaultStats,
        tag_analysis: dict[str, Any],
        content_analysis: dict[str, Any],
    ) -> list[dict[str, str]]:
        """レコメンデーションを生成"""
        recommendations = []

        # Vaultサイズの推奨
        size_mb = vault_stats.total_size_bytes / (1024 * 1024)
        if size_mb > 1000:  # 1GB以上
            recommendations.append(
                {
                    "type": "storage",
                    "priority": "medium",
                    "message": f"Vaultサイズが{size_mb:.1f}MBと大きくなっています。古いノートのアーカイブを検討してください。",
                }
            )

        # タグの推奨
        tag_coverage = tag_analysis.get("tag_coverage", 0)
        if tag_coverage < 50:
            recommendations.append(
                {
                    "type": "tagging",
                    "priority": "low",
                    "message": f"タグ付けされたノートが{tag_coverage:.1f}%です。タグ付けを増やすとノートが見つけやすくなります。",
                }
            )

        orphaned_tags = len(tag_analysis.get("orphaned_tags", []))
        if orphaned_tags > 20:
            recommendations.append(
                {
                    "type": "tagging",
                    "priority": "low",
                    "message": f"使用回数が1回のみのタグが{orphaned_tags}個あります。タグの整理を検討してください。",
                }
            )

        # AI処理の推奨
        ai_coverage = (
            vault_stats.ai_processed_notes / max(vault_stats.total_notes, 1)
        ) * 100
        if ai_coverage < 80:
            recommendations.append(
                {
                    "type": "ai_processing",
                    "priority": "medium",
                    "message": f"AI処理済みノートが{ai_coverage:.1f}%です。未処理のノートがあれば処理を検討してください。",
                }
            )

        # 日次ノートの推奨
        if vault_stats.notes_created_today == 0:
            recommendations.append(
                {
                    "type": "daily_notes",
                    "priority": "low",
                    "message": "今日のノートがまだ作成されていません。日次ノートの作成を検討してください。",
                }
            )

        return recommendations
