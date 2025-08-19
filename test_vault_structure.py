#!/usr/bin/env python3
"""
新しい Vault 構造のテスト
"""

import asyncio

# プロジェクトのパスを追加
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.settings import Settings
from src.obsidian.file_manager import ObsidianFileManager


async def test_new_vault_structure():
    """新しい Vault 構造をテスト"""

    print("🚀 新しい Vault 構造生成テストを開始...")

    # 設定を読み込み
    settings = Settings()
    print(f"📁 Vault path: {settings.obsidian_vault_path}")

    # Obsidian ファイルマネージャーを初期化
    obsidian_manager = ObsidianFileManager(vault_path=settings.obsidian_vault_path)

    # Vault を初期化（新しい構造で作成）
    success = await obsidian_manager.initialize_vault()

    if success:
        print("✅ Vault 構造初期化完了")

        # 作成されたフォルダ構造を確認
        vault_path = Path(settings.obsidian_vault_path)
        print("\n 📂 作成された Vault 構造:")
        print("=" * 60)

        def show_tree(
            path: Path, prefix: str = "", max_depth: int = 3, current_depth: int = 0
        ):
            if current_depth >= max_depth:
                return

            items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                print(f"{prefix}{current_prefix}{item.name}")

                if item.is_dir() and current_depth < max_depth - 1:
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    show_tree(item, next_prefix, max_depth, current_depth + 1)

        show_tree(vault_path)
        print("=" * 60)

        # フォルダ数をカウント
        all_folders = list(vault_path.rglob("*/"))
        print("\n 📊 統計:")
        print(f"   - 総フォルダ数: {len(all_folders)} 個")
        print(
            f"   - トップレベルフォルダ数: {len([f for f in vault_path.iterdir() if f.is_dir()])} 個"
        )

        # 特定のフォルダが正しく作成されたかチェック
        expected_folders = [
            "00_Inbox",
            "01_Projects",
            "02_DailyNotes",
            "03_Ideas",
            "04_Archive",
            "05_Resources",
            "06_Finance",
            "07_Tasks",
            "08_Health",
            "09_Knowledge",  # 新しい名前
            "10_Attachments",
            "99_Meta",
        ]

        print("\n ✅ フォルダ存在確認:")
        all_exist = True
        for folder in expected_folders:
            folder_path = vault_path / folder
            exists = folder_path.exists()
            status = "✅" if exists else "❌"
            print(f"   {status} {folder}")
            if not exists:
                all_exist = False

        if all_exist:
            print("\n 🎉 すべての必要フォルダが正しく作成されました！")
        else:
            print("\n ⚠️ 一部のフォルダが作成されていません")

    else:
        print("❌ Vault 構造初期化に失敗")


if __name__ == "__main__":
    asyncio.run(test_new_vault_structure())
