#!/usr/bin/env python3
"""
Garmin integration test script
"""

import asyncio
import sys
from datetime import date
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.garmin.cache import GarminDataCache
from src.garmin.models import DataError, DataSource, HealthData


async def test_cache_functionality() -> None:
    """キャッシュ機能のテスト"""
    print("=== Testing Cache Functionality ===")

    try:
        # キャッシュディレクトリを指定してキャッシュを初期化
        cache_dir = Path.cwd() / ".test_cache"
        cache = GarminDataCache(cache_dir, max_age_hours=1.0)

        print("✓ Cache initialized successfully")
        print(f"  - Cache directory: {cache_dir}")
        print("  - Max age: 1.0 hours")

        # キャッシュ統計
        print("\n--- Initial Cache Statistics ---")
        cache_stats = cache.get_cache_stats()
        print(f"Cache stats: {cache_stats}")

        # テスト用の HealthData オブジェクトを作成してキャッシュ機能をテスト
        print("\n--- Cache Save/Load Test ---")
        test_date = date.today()
        test_health_data = HealthData(
            date=test_date,
            detailed_errors=[
                DataError(
                    source=DataSource.SLEEP,
                    error_type="TestError",
                    message="Test error message",
                    user_message="テスト用のエラーメッセージです",
                )
            ],
        )

        # キャッシュに保存
        save_success = cache.save_health_data(test_health_data)
        print(f"Cache save success: {save_success}")

        # キャッシュから読み込み
        cached_data = cache.load_health_data(test_date)
        if cached_data:
            print("✓ Successfully loaded data from cache")
            print(f"  - Cache age: {cached_data.cache_age_hours:.2f} hours")
            print(
                f"  - User-friendly errors: {cached_data.user_friendly_error_messages}"
            )
        else:
            print("✗ Failed to load data from cache")

        # キャッシュ有効性チェック
        print("\n--- Cache Validity Test ---")
        is_valid = cache.is_cache_valid(test_date)
        print(f"Cache is valid: {is_valid}")

        # キャッシュ統計の更新
        print("\n--- Updated Cache Statistics ---")
        cache_stats = cache.get_cache_stats()
        print(f"Updated cache stats: {cache_stats}")

        # キャッシュクリーンアップテスト
        print("\n--- Cache Cleanup Test ---")
        cleaned_count = cache.cleanup_old_cache(days_to_keep=0)  # 全て削除
        print(f"Cleaned {cleaned_count} cache files")

        print("\n ✓ Cache tests completed successfully!")

    except Exception as e:
        print(f"✗ Cache test failed with error: {e}")
        import traceback

        traceback.print_exc()


async def test_health_data_models() -> None:
    """HealthData モデルのテスト"""
    print("\n=== Testing Health Data Models ===")

    from typing import cast

    from src.garmin.models import DataError, DataSource

    try:
        # エラー付き HealthData の作成
        health_data = HealthData(
            date=date.today(),
            detailed_errors=[
                DataError(
                    source=DataSource.SLEEP,
                    error_type="ConnectionError",
                    message="Failed to connect to Garmin",
                    is_recoverable=True,
                    user_message="Garmin サーバーとの接続に問題があります。",
                ),
                DataError(
                    source=DataSource.STEPS,
                    error_type="TimeoutError",
                    message="Request timed out",
                    is_recoverable=True,
                    user_message="リクエストがタイムアウトしました。",
                ),
            ],
            is_cached_data=True,
            cache_age_hours=2.5,
        )

        print("✓ HealthData created")
        print(f"  - Has any data: {health_data.has_any_data}")
        print(f"  - Data quality: {health_data.data_quality}")

        failed_sources = cast(list[DataSource], health_data.failed_data_sources)
        recoverable_errors = cast(list[DataError], health_data.recoverable_errors)
        print(f"  - Failed sources: {[s.value for s in failed_sources]}")
        print(f"  - Recoverable errors: {len(recoverable_errors)}")
        print(f"  - User messages: {health_data.user_friendly_error_messages}")
        print(f"  - Is cached: {health_data.is_cached_data}")
        print(f"  - Cache age: {health_data.cache_age_hours} hours")

        print("\n ✓ Model tests completed successfully!")

    except Exception as e:
        print(f"✗ Model test failed with error: {e}")
        import traceback

        traceback.print_exc()


async def test_formatter() -> None:
    """フォーマッタのテスト"""
    print("\n=== Testing Formatter ===")

    try:
        from src.garmin.formatter import format_health_data_for_markdown

        # テストデータの作成
        health_data = HealthData(
            date=date.today(),
            detailed_errors=[
                DataError(
                    source=DataSource.SLEEP,
                    error_type="ConnectionError",
                    message="Connection failed",
                    user_message="睡眠データの取得に失敗しました",
                )
            ],
            is_cached_data=True,
            cache_age_hours=1.5,
        )

        # Markdown フォーマット
        markdown_output = format_health_data_for_markdown(health_data)

        print("✓ Markdown formatting successful")
        print("--- Formatted Output ---")
        print(markdown_output)
        print("--- End Output ---")

    except Exception as e:
        print(f"✗ Formatter test failed with error: {e}")
        import traceback

        traceback.print_exc()


async def main():
    """メインテスト関数"""
    print("Starting Garmin Integration Tests...")
    print("=" * 50)

    await test_cache_functionality()
    await test_health_data_models()
    await test_formatter()

    print("\n" + "=" * 50)
    print("All integration tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
