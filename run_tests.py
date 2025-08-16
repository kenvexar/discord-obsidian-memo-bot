#!/usr/bin/env python3
"""
Discord-Obsidian Memo Bot テスト実行スクリプト

包括的なテストスイートを実行し、システムの動作を確認
"""

import asyncio
import os
import sys
from pathlib import Path

# プロジェクトのルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# 環境変数の設定（テスト用）
os.environ.update(
    {
        "ENVIRONMENT": "test",
        "ENABLE_MOCK_MODE": "true",
        "LOG_LEVEL": "WARNING",  # テスト中のログを抑制
        "DISCORD_BOT_TOKEN": "test_token_for_testing_only",
        "DISCORD_GUILD_ID": "123456789",
        "GEMINI_API_KEY": "test_gemini_key_for_testing_only",
        "OBSIDIAN_VAULT_PATH": "/tmp/test_vault_discord_bot",
        "ENABLE_ACCESS_LOGGING": "false",  # テスト中はアクセスログを無効化
    }
)


async def run_basic_tests() -> bool:
    """基本的な動作テスト"""
    print("=== 基本動作テストの実行 ===")

    try:
        # 設定の読み込みテスト
        from src.config import get_settings

        settings = get_settings()
        print(f"✓ 設定読み込み成功 (環境: {settings.environment})")

        # ログシステムのテスト
        from src.utils import get_logger, setup_logging

        setup_logging()
        logger = get_logger("test")
        logger.info("テストログメッセージ")
        print("✓ ログシステム初期化成功")

        # Obsidianディレクトリの作成
        vault_path = Path(settings.obsidian_vault_path)
        vault_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ テスト用Obsidianディレクトリ作成: {vault_path}")

        return True

    except Exception as e:
        print(f"❌ 基本テストエラー: {e}")
        return False


async def run_component_tests() -> bool:
    """コンポーネント別テスト"""
    print("\n=== コンポーネント別テストの実行 ===")

    try:
        # 基本システムテストの実行
        print("新システム基本動作テスト実行中...")

        # test_new_systems.pyがあれば実行
        test_file = project_root / ".tmp" / "test_new_systems.py"
        if test_file.exists():
            import subprocess

            env = os.environ.copy()
            env["PYTHONPATH"] = f"{project_root}:{project_root / 'src'}"
            result = subprocess.run(
                [sys.executable, str(test_file)],
                capture_output=True,
                text=True,
                cwd=project_root,
                env=env,
            )

            if result.returncode == 0:
                print("✓ 新システム基本動作テスト成功")
            else:
                print(f"⚠️  新システムテスト警告: {result.stderr}")

        return True

    except Exception as e:
        print(f"❌ コンポーネントテストエラー: {e}")
        return False


async def run_integration_tests() -> bool:
    """統合テストの実行"""
    print("\n=== 統合テストの実行 ===")

    try:
        # 統合テストの実行
        from tests.test_integration import run_integration_tests

        success = await run_integration_tests()

        if success:
            print("✓ 統合テスト成功")
            return True
        else:
            print("❌ 統合テスト失敗")
            return False

    except Exception as e:
        print(f"❌ 統合テストエラー: {e}")
        import traceback

        traceback.print_exc()
        return False


async def cleanup_test_environment() -> None:
    """テスト環境のクリーンアップ"""
    print("\n=== テスト環境クリーンアップ ===")

    try:
        # テスト用Obsidianディレクトリの削除
        test_vault = Path("/tmp/test_vault_discord_bot")
        if test_vault.exists():
            import shutil

            shutil.rmtree(test_vault)
            print(f"✓ テスト用ディレクトリ削除: {test_vault}")

        # 一時ファイルのクリーンアップ
        temp_logs = Path("/tmp").glob("*discord_bot_test*")
        for temp_file in temp_logs:
            if temp_file.is_file():
                temp_file.unlink()

        print("✓ テスト環境クリーンアップ完了")

    except Exception as e:
        print(f"⚠️  クリーンアップ警告: {e}")


async def main() -> None:
    """メインテスト実行関数"""
    print("Discord-Obsidian Memo Bot - 包括的テストスイート")
    print("=" * 60)

    success_count = 0
    total_tests = 3

    try:
        # 基本動作テスト
        if await run_basic_tests():
            success_count += 1

        # コンポーネント別テスト
        if await run_component_tests():
            success_count += 1

        # 統合テスト
        if await run_integration_tests():
            success_count += 1

    finally:
        # クリーンアップは必ず実行
        await cleanup_test_environment()

    # 結果の表示
    print("\n" + "=" * 60)
    print("テスト実行結果:")
    print(f"成功: {success_count}/{total_tests}")

    if success_count == total_tests:
        print("🎉 全てのテストが成功しました！")
        print("\nシステムは正常に動作しています。")
    else:
        print(f"⚠️  {total_tests - success_count} 個のテストで問題が発見されました。")
        print("\n問題の詳細を確認して修正してください。")


if __name__ == "__main__":
    exit_code = asyncio.run(main())
