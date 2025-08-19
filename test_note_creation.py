#!/usr/bin/env python3
"""
Obsidian ノート作成の直接テスト
"""

import asyncio

# プロジェクトのパスを追加
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.settings import Settings
from src.obsidian.file_manager import ObsidianFileManager
from src.obsidian.template_system import TemplateEngine


async def create_test_note():
    """テスト用の Obsidian ノートを作成"""

    print("🚀 Obsidian ノート作成テストを開始...")

    # 設定を読み込み
    settings = Settings()
    print(f"📁 Vault path: {settings.obsidian_vault_path}")

    # コンポーネントを初期化
    obsidian_manager = ObsidianFileManager(vault_path=settings.obsidian_vault_path)
    template_engine = TemplateEngine(vault_path=settings.obsidian_vault_path)

    # Vault を初期化
    await obsidian_manager.initialize_vault()
    print("✅ Obsidian vault 初期化完了")

    # テストメッセージ
    test_message = """
    🚀 新プロジェクト企画: AI 駆動型知識管理システム

    主な機能:
    - 自動分類とタグ付け
    - 関連性分析
    - スマート検索
    - リアルタイム同期

    来週までに仕様書を作成予定。
    チームメンバーとの会議も調整中。
    """

    print(f"📝 テストメッセージ: {test_message[:50]}...")

    # AI 処理をスキップ（ API キーエラーのため）
    print("⚠️  AI 処理をスキップしてテンプレートのみでノートを作成します")
    ai_result = None

    # メッセージデータを構築
    message_data = {
        "metadata": {
            "message_id": 12345,
            "author": "test_user",
            "content": test_message,
            "timestamp": datetime.now().isoformat(),
            "channel_id": 123456789,
            "channel_name": "inbox",
            "bot": False,
            "has_attachments": False,
            "attachment_count": 0,
            "content_length": len(test_message),
            "is_reply": False,
            "mentions_count": 0,
            "embed_count": 0,
        },
        "ai_processing": ai_result.model_dump() if ai_result else None,
        "channel_info": {
            "name": "inbox",
            "category": "capture",
            "description": "Main memo capture channel",
        },
        "processing_timestamp": datetime.now().isoformat(),
    }

    # テンプレートからノートを生成
    print("📄 テンプレートからノートを生成中...")
    note = await template_engine.generate_note_from_template(
        template_name="idea_note",
        message_data=message_data,
        ai_result=ai_result,
    )

    if note:
        print("✅ ノート生成成功:")
        print(f"   - タイトル: {note.title}")
        print(f"   - ファイルパス: {note.file_path}")
        print(f"   - コンテンツ長: {len(note.content)} 文字")

        # ノートを保存
        print("💾 ノートを保存中...")
        success = await obsidian_manager.save_or_append_daily_note(note)

        if success:
            print(f"✅ ノート保存成功: {note.file_path}")

            # 保存されたファイルの内容を表示
            if note.file_path.exists():
                with open(note.file_path, encoding="utf-8") as f:
                    content = f.read()
                print("\n 📖 保存されたノートの内容:")
                print("=" * 50)
                print(content[:800] + "..." if len(content) > 800 else content)
                print("=" * 50)
            else:
                print("❌ ファイルが見つかりません")
        else:
            print("❌ ノート保存に失敗")
    else:
        print("❌ ノート生成に失敗")


if __name__ == "__main__":
    asyncio.run(create_test_note())
