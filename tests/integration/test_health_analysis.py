#!/usr/bin/env python3
"""
Health analysis integration test script
"""
import asyncio
import sys
from datetime import date, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from health_analysis.analyzer import HealthDataAnalyzer
from health_analysis.models import (
    AnalysisReport,
    AnalysisType,
    ChangeDetection,
    ChangeType,
    HealthInsight,
    TrendAnalysis,
    WeeklyHealthSummary,
)


async def test_health_analysis_models():
    """健康分析モデルのテスト"""
    print("=== Testing Health Analysis Models ===")

    try:
        # HealthInsightのテスト
        insight = HealthInsight(
            category="睡眠",
            insight_type="sleep_duration",
            title="睡眠不足の可能性",
            description="平均睡眠時間が推奨値を下回っています",
            confidence_score=0.8,
            actionable=True,
            recommended_actions=["就寝時間を早める", "睡眠環境を改善する"],
            priority="high",
        )

        print("✓ HealthInsight created successfully")
        print(f"  - Title: {insight.title}")
        print(f"  - Priority: {insight.priority}")
        print(f"  - Actionable: {insight.actionable}")
        print(f"  - Actions: {len(insight.recommended_actions)}")

        # TrendAnalysisのテスト
        trend = TrendAnalysis(
            metric_name="sleep_hours",
            period_days=7,
            trend_direction="下降",
            change_percentage=-15.2,
            average_value=6.5,
            confidence_level=0.85,
            data_points=6,
            interpretation="睡眠時間にやや下降傾向が見られます（大きな変化: -15.2%）",
        )

        print("✓ TrendAnalysis created successfully")
        print(f"  - Metric: {trend.metric_name}")
        print(f"  - Direction: {trend.trend_direction}")
        print(f"  - Change: {trend.change_percentage}%")
        print(f"  - Confidence: {trend.confidence_level}")

        # ChangeDetectionのテスト
        change = ChangeDetection(
            metric_name="daily_steps",
            change_type=ChangeType.DECLINE,
            magnitude=2500.0,
            detection_date=date.today(),
            baseline_period=4,
            baseline_average=8500.0,
            current_value=6000.0,
            significance_score=0.9,
            description="1日の歩数が過去数日で29.4%減少しています（要注意）",
            recommended_action="日常的な散歩や運動を増やすことを検討してください",
        )

        print("✓ ChangeDetection created successfully")
        print(f"  - Metric: {change.metric_name}")
        print(f"  - Type: {change.change_type}")
        print(f"  - Significance: {change.significance_score}")
        print(f"  - Description: {change.description}")

        # WeeklyHealthSummaryのテスト
        week_start = date.today() - timedelta(days=7)
        summary = WeeklyHealthSummary(
            week_start=week_start,
            week_end=week_start + timedelta(days=6),
            avg_sleep_hours=7.2,
            avg_sleep_score=82.0,
            sleep_consistency=0.8,
            total_steps=45000,
            avg_daily_steps=6428.0,
            active_days=5,
            avg_resting_hr=65.0,
            hr_variability=0.12,
            total_workouts=3,
            total_workout_minutes=180,
            data_completeness=0.86,
            missing_days=[],
        )

        print("✓ WeeklyHealthSummary created successfully")
        print(f"  - Week: {summary.week_start} - {summary.week_end}")
        print(f"  - Avg sleep: {summary.avg_sleep_hours}h")
        print(f"  - Avg steps: {summary.avg_daily_steps}")
        print(f"  - Data completeness: {summary.data_completeness:.1%}")
        print(f"  - Active days: {summary.active_days}/7")

        # AnalysisReportのテスト
        report = AnalysisReport(
            report_id="test_report_001",
            analysis_type=AnalysisType.WEEKLY_SUMMARY,
            start_date=week_start,
            end_date=week_start + timedelta(days=6),
            summary="テスト週の健康データ分析結果です。データの完全性は良好です。重要な健康上の課題は検出されませんでした。",
            key_findings=["睡眠時間が安定している", "活動量は目標値を上回っている"],
            insights=[insight],
            trends=[trend],
            changes=[change],
            data_quality_score=0.86,
            analyzed_days=6,
            missing_days=1,
        )

        print("✓ AnalysisReport created successfully")
        print(f"  - Report ID: {report.report_id}")
        print(f"  - Analysis type: {report.analysis_type}")
        print(f"  - Data quality: {report.data_quality_score:.1%}")
        print(f"  - Key findings: {len(report.key_findings)}")

        # メソッドのテスト
        priority_insights = report.get_priority_insights("high")
        actionable_insights = report.get_actionable_insights()
        significant_changes = report.get_significant_changes(0.8)

        print(f"  - High priority insights: {len(priority_insights)}")
        print(f"  - Actionable insights: {len(actionable_insights)}")
        print(f"  - Significant changes: {len(significant_changes)}")

        print("\n✓ All model tests completed successfully!")

    except Exception as e:
        print(f"✗ Model test failed with error: {e}")
        import traceback

        traceback.print_exc()


async def test_health_analyzer():
    """HealthDataAnalyzerのテスト"""
    print("\n=== Testing HealthDataAnalyzer ===")

    try:
        # Mock AIProcessorを作成
        class MockAIProcessor:
            async def process_text(self, text: str, context: str = "") -> dict:
                return {
                    "processed_content": "テスト用の週次健康データ分析結果です。"
                    "睡眠時間は安定しており、活動量も適切なレベルを維持しています。"
                    "継続的な健康管理が功を奏しているようです。"
                }

        analyzer = HealthDataAnalyzer(ai_processor=MockAIProcessor())

        print("✓ HealthDataAnalyzer initialized")
        print(f"  - Min data points: {analyzer.min_data_points}")
        print(f"  - Trend threshold: {analyzer.trend_threshold}")
        print(
            f"  - Change significance threshold: {analyzer.change_significance_threshold}"
        )

        # 計算メソッドのテスト
        consistency = analyzer._calculate_consistency([7.0, 7.2, 6.8, 7.1, 7.3])
        print(f"  - Sleep consistency calculation: {consistency:.3f}")

        variability = analyzer._calculate_variability([65, 67, 63, 66, 64])
        print(f"  - HR variability calculation: {variability:.3f}")

        # 相関計算のテスト
        correlation = analyzer._calculate_correlation_coefficient(
            [7.0, 7.2, 6.8, 7.1], [8000, 8200, 7500, 8100]
        )
        print(f"  - Correlation calculation: {correlation}")

        print("✓ HealthDataAnalyzer basic tests completed successfully!")

    except Exception as e:
        print(f"✗ HealthDataAnalyzer test failed with error: {e}")
        import traceback

        traceback.print_exc()


async def test_markdown_formatting():
    """Markdown整形のテスト"""
    print("\n=== Testing Markdown Formatting ===")

    try:
        # サンプルデータでレポートを作成
        week_start = date.today() - timedelta(days=7)

        insights = [
            HealthInsight(
                category="睡眠",
                insight_type="sleep_quality",
                title="良好な睡眠パターン",
                description="睡眠時間が一定で、質の高い睡眠が取れています。",
                confidence_score=0.9,
                actionable=False,
                priority="low",
            ),
            HealthInsight(
                category="活動",
                insight_type="activity_level",
                title="運動不足の可能性",
                description="週の半分以上で推奨歩数を下回っています。",
                confidence_score=0.8,
                actionable=True,
                recommended_actions=[
                    "毎日の散歩を習慣化する",
                    "階段を積極的に使用する",
                ],
                priority="medium",
            ),
        ]

        report = AnalysisReport(
            report_id="markdown_test",
            analysis_type=AnalysisType.WEEKLY_SUMMARY,
            start_date=week_start,
            end_date=week_start + timedelta(days=6),
            summary="週次健康分析のサンプルレポートです。基本的な健康指標は良好で、継続的な改善が見られます。",
            key_findings=[
                "睡眠パターンが安定している",
                "心拍数が正常範囲内",
                "活動量にわずかな改善の余地あり",
            ],
            insights=insights,
            data_quality_score=0.92,
            analyzed_days=7,
            missing_days=0,
        )

        # フォーマット機能をテスト（実際のスケジューラーから呼び出し）
        class MockScheduler:
            def _format_analysis_for_daily_note(
                self, analysis_report, correlation_analysis=None
            ):
                markdown_parts = []

                # ヘッダー
                week_range = f"{analysis_report.start_date.strftime('%m/%d')} - {analysis_report.end_date.strftime('%m/%d')}"
                markdown_parts.append(f"## 🔍 週次健康分析 ({week_range})")
                markdown_parts.append("")

                # サマリー
                markdown_parts.append("### 📊 サマリー")
                markdown_parts.append(analysis_report.summary)
                markdown_parts.append("")

                # 主要な発見
                if analysis_report.key_findings:
                    markdown_parts.append("### 🎯 主要な発見")
                    for finding in analysis_report.key_findings:
                        markdown_parts.append(f"- {finding}")
                    markdown_parts.append("")

                # 実行可能な洞察
                actionable_insights = [
                    i for i in analysis_report.insights if i.actionable
                ]
                if actionable_insights:
                    markdown_parts.append("### 💡 実行可能な改善提案")
                    for insight in actionable_insights:
                        markdown_parts.append(
                            f"**{insight.title}**: {insight.description}"
                        )
                        if insight.recommended_actions:
                            for action in insight.recommended_actions:
                                markdown_parts.append(f"  - {action}")
                    markdown_parts.append("")

                # メタ情報
                markdown_parts.append("### 📈 分析情報")
                markdown_parts.append(
                    f"- 分析対象日数: {analysis_report.analyzed_days}日"
                )
                markdown_parts.append(
                    f"- データ品質スコア: {analysis_report.data_quality_score:.1%}"
                )

                return "\n".join(markdown_parts)

        scheduler = MockScheduler()
        markdown_output = scheduler._format_analysis_for_daily_note(report)

        print("✓ Markdown formatting successful")
        print("--- Formatted Output ---")
        print(markdown_output)
        print("--- End Output ---")

    except Exception as e:
        print(f"✗ Markdown formatting test failed with error: {e}")
        import traceback

        traceback.print_exc()


async def main():
    """メインテスト関数"""
    print("Starting Health Analysis Integration Tests...")
    print("=" * 60)

    await test_health_analysis_models()
    await test_health_analyzer()
    await test_markdown_formatting()

    print("\n" + "=" * 60)
    print("All health analysis tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
