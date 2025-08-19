#!/usr/bin/env python3
"""
簡単な Obsidian ノート作成テスト
"""

import asyncio

# プロジェクトのパスを追加
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.settings import Settings
from src.obsidian.file_manager import ObsidianFileManager
from src.obsidian.models import ObsidianNote


async def create_simple_note():
    """簡単な Obsidian ノートを作成"""

    print("🚀 簡単な Obsidian ノート作成テストを開始...")

    # 設定を読み込み
    settings = Settings()
    print(f"📁 Vault path: {settings.obsidian_vault_path}")

    # Obsidian ファイルマネージャーを初期化
    obsidian_manager = ObsidianFileManager(vault_path=settings.obsidian_vault_path)

    # Vault を初期化
    await obsidian_manager.initialize_vault()
    print("✅ Obsidian vault 初期化完了")

    # テストメッセージ
    test_message = """🚀 新プロジェクト企画: AI 駆動型知識管理システム

主な機能:
- 自動分類とタグ付け
- 関連性分析
- スマート検索
- リアルタイム同期

来週までに仕様書を作成予定。
チームメンバーとの会議も調整中。"""

    # 現在の日時（ファイル名に使える形式）
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H%M")  # コロンを除去

    # ノートの内容を作成
    note_content = f"""---
type: memo
created: {now.isoformat()}
tags:
  - project
  - ai
  - knowledge-management
author: test_user
---

# 💡 新プロジェクト企画

{test_message}

## 📅 作成日時

{now.strftime("%Y 年%m 月%d 日 %H:%M")}

## 🔄 次のアクション

- [ ] 仕様書の詳細化
- [ ] チームメンバーとの会議調整
- [ ] 技術選定の検討

---
*このノートは Discord-Obsidian Memo Bot によって自動生成されました*
"""

    # ノートオブジェクトを作成（ ASCII 文字のみでファイル名を生成）
    note_title = f"project_idea_{date_str}_{time_str}"
    filename = f"{note_title}.md"
    note_path = settings.obsidian_vault_path / "02_Ideas" / filename

    from src.obsidian.models import NoteFrontmatter

    frontmatter = NoteFrontmatter(
        obsidian_folder="02_Ideas",
        ai_category="project",
        tags=["project", "ai", "knowledge-management"],
        discord_author="test_user",
        created=now.isoformat(),
    )

    note = ObsidianNote(
        filename=filename,
        file_path=note_path,
        frontmatter=frontmatter,
        content=note_content,
    )

    print("📄 ノート作成:")
    print(f"   - タイトル: {note.title}")
    print(f"   - ファイルパス: {note.file_path}")
    print(f"   - フォルダ: {note.frontmatter.obsidian_folder}")
    print(f"   - タグ: {note.frontmatter.tags}")

    # ノートを保存
    print("💾 ノートを保存中...")
    success = await obsidian_manager.save_note(note)

    if success:
        print(f"✅ ノート保存成功: {note.file_path}")

        # 保存されたファイルの内容を確認
        if note.file_path.exists():
            with open(note.file_path, encoding="utf-8") as f:
                content = f.read()
            print("\n 📖 保存されたノートの内容:")
            print("=" * 80)
            print(content)
            print("=" * 80)

            # ファイルサイズも表示
            file_size = note.file_path.stat().st_size
            print("\n 📊 ファイル情報:")
            print(f"   - サイズ: {file_size} バイト")
            print(f"   - 行数: {len(content.splitlines())} 行")

        else:
            print("❌ ファイルが見つかりません")
    else:
        print("❌ ノート保存に失敗")


if __name__ == "__main__":
    asyncio.run(create_simple_note())
