#!/usr/bin/env python3
"""
Health analysis models test script (standalone)
"""

import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Direct import to avoid dependency issues
from health_analysis.models import (
    ActivityCorrelation,
    AnalysisReport,
    AnalysisType,
    ChangeDetection,
    ChangeType,
    HealthInsight,
    TrendAnalysis,
    WeeklyHealthSummary,
)


def test_health_analysis_models():
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
        print(f"  - Type: {change.change_type.value}")
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

        # ActivityCorrelationのテスト
        correlation = ActivityCorrelation(
            date_range=f"{week_start} - {week_start + timedelta(days=6)}",
            correlation_type="health_discord_activity",
            discord_activity_correlation={
                "message_count_vs_sleep_hours": 0.65,
                "active_hours_count_vs_daily_steps": -0.42,
            },
            sleep_steps_correlation=0.38,
            sleep_hr_correlation=-0.25,
            steps_hr_correlation=-0.15,
            peak_activity_hours=[14, 15, 20, 21],
            low_activity_hours=[2, 3, 4, 5],
            notable_patterns=[
                "Discord活動が活発な日は睡眠時間が長い傾向があります",
                "活動的な日ほど歩数も多い傾向があります",
            ],
            recommendations=[
                "適度な活動は良い睡眠につながっているようです",
                "継続的な健康データモニタリングを行いましょう",
            ],
        )

        print("✓ ActivityCorrelation created successfully")
        print(f"  - Date range: {correlation.date_range}")
        print(
            f"  - Discord correlations: {len(correlation.discord_activity_correlation)}"
        )
        print(f"  - Sleep-steps correlation: {correlation.sleep_steps_correlation}")
        print(f"  - Notable patterns: {len(correlation.notable_patterns)}")
        print(f"  - Recommendations: {len(correlation.recommendations)}")

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
        print(f"  - Analysis type: {report.analysis_type.value}")
        print(f"  - Data quality: {report.data_quality_score:.1%}")
        print(f"  - Key findings: {len(report.key_findings)}")

        # メソッドのテスト
        priority_insights = report.get_priority_insights("high")
        actionable_insights = report.get_actionable_insights()
        significant_changes = report.get_significant_changes(0.8)

        print(f"  - High priority insights: {len(priority_insights)}")
        print(f"  - Actionable insights: {len(actionable_insights)}")
        print(f"  - Significant changes: {len(significant_changes)}")

        # レポートフォーマットのテスト
        print("\n--- Sample Analysis Report Format ---")
        week_range = f"{report.start_date.strftime('%m/%d')} - {report.end_date.strftime('%m/%d')}"

        sample_format = f"""## 🔍 週次健康分析 ({week_range})

### 📊 サマリー
{report.summary}

### 🎯 主要な発見"""

        for finding in report.key_findings:
            sample_format += f"\n- {finding}"

        sample_format += "\n\n### ⚠️ 重要な洞察"
        for insight in priority_insights:
            sample_format += f"\n**{insight.title}**\n{insight.description}"
            if insight.recommended_actions:
                sample_format += "\n推奨アクション:"
                for action in insight.recommended_actions:
                    sample_format += f"\n- {action}"

        sample_format += f"\n\n### 📈 分析情報\n- 分析対象日数: {report.analyzed_days}日\n- データ品質スコア: {report.data_quality_score:.1%}"

        print(sample_format)
        print("--- End Sample Format ---")

        print("\n✓ All model tests completed successfully!")

    except Exception as e:
        print(f"✗ Model test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_enum_values():
    """Enumの値をテスト"""
    print("\n=== Testing Enum Values ===")

    try:
        # ChangeTypeのテスト
        change_types = [
            ChangeType.IMPROVEMENT,
            ChangeType.DECLINE,
            ChangeType.SIGNIFICANT_CHANGE,
            ChangeType.NO_CHANGE,
        ]
        print("✓ ChangeType enum values:")
        for change_type in change_types:
            print(f"  - {change_type.name}: {change_type.value}")

        # AnalysisTypeのテスト
        analysis_types = [
            AnalysisType.WEEKLY_SUMMARY,
            AnalysisType.MONTHLY_SUMMARY,
            AnalysisType.TREND_ANALYSIS,
            AnalysisType.CHANGE_DETECTION,
        ]
        print("✓ AnalysisType enum values:")
        for analysis_type in analysis_types:
            print(f"  - {analysis_type.name}: {analysis_type.value}")

        print("\n✓ Enum tests completed successfully!")

    except Exception as e:
        print(f"✗ Enum test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """メインテスト関数"""
    print("Starting Health Analysis Models Tests...")
    print("=" * 60)

    success = True

    if not test_health_analysis_models():
        success = False

    if not test_enum_values():
        success = False

    print("\n" + "=" * 60)
    if success:
        print("✅ All health analysis model tests passed!")
    else:
        print("❌ Some tests failed!")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
