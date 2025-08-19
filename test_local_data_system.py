#!/usr/bin/env python3
"""
ローカルデータ管理システムのテスト
"""

import asyncio
import json
import tempfile
from datetime import datetime
from pathlib import Path

from src.obsidian.file_manager import ObsidianFileManager
from src.obsidian.models import NoteFrontmatter, NoteStatus, ObsidianNote, VaultFolder


async def test_local_data_system():
    """ローカルデータ管理システムのテスト"""
    print("🧪 ローカルデータ管理システムのテストを開始...")

    # テスト用の一時ディレクトリを作成
    with tempfile.TemporaryDirectory() as temp_dir:
        vault_path = Path(temp_dir) / "test_vault"
        vault_path.mkdir(parents=True)

        print(f"📁 テスト用 Vault: {vault_path}")

        # ObsidianFileManager の初期化
        file_manager = ObsidianFileManager(
            vault_path=vault_path, enable_local_data=True
        )

        # 1. ローカルデータ管理システムの初期化
        print("\n1 ️⃣ ローカルデータ管理システムの初期化...")
        init_success = await file_manager.initialize_local_data()
        print(f"   ✅ 初期化成功: {init_success}")
        assert init_success, "初期化に失敗しました"

        # 2. テストノートの作成と保存
        print("\n2 ️⃣ テストノートの作成と保存...")
        test_notes = []

        for i in range(5):
            frontmatter = NoteFrontmatter(
                discord_message_id=1000 + i,
                discord_channel=f"test-channel-{i}",
                discord_author=f"test-user-{i}",
                ai_processed=True,
                ai_summary=f"テストノート{i}の要約です。",
                ai_tags=["#test", f"#category{i % 3}"],
                ai_category=f"test_category_{i % 3}",
                ai_confidence=0.95,
                status=NoteStatus.ACTIVE,
                obsidian_folder=VaultFolder.INBOX.value,
            )

            # Obsidian の命名規則に従ったファイル名
            timestamp = datetime.now().strftime("%Y%m%d%H%M")
            filename = f"{timestamp}_test_category_{i}_テストノート{i}.md"

            note = ObsidianNote(
                filename=filename,
                file_path=vault_path / VaultFolder.INBOX.value / filename,
                frontmatter=frontmatter,
                content=f"# テストノート{i}\n\n これは{i}番目のテストノートです。\n\n## 詳細\n 何かしらの内容がここに入ります。",
                created_at=datetime.now(),
                modified_at=datetime.now(),
            )

            # ノートを保存
            save_success = await file_manager.save_note(note)
            print(f"   📝 ノート{i} 保存: {save_success}")
            assert save_success, f"ノート{i}の保存に失敗しました"

            test_notes.append(note)

        # 3. 高速検索のテスト
        print("\n3 ️⃣ 高速検索のテスト...")

        # インデックス状態の確認
        if file_manager.local_data_manager:
            notes_count = len(file_manager.local_data_manager.data_index.notes_index)
            content_count = len(
                file_manager.local_data_manager.data_index.content_index
            )
            tags_count = len(file_manager.local_data_manager.data_index.tags_index)
            print(
                f"   📊 インデックス状態: ノート{notes_count}件, コンテンツ{content_count}件, タグ{tags_count}件"
            )

            # インデックス内容の詳細表示
            for key, value in list(
                file_manager.local_data_manager.data_index.notes_index.items()
            )[:2]:
                print(f"   📝 インデックス例: {key} -> {value['title']}")

        # クエリ検索
        search_results = file_manager.search_notes_fast(query="テストノート")
        print(f"   🔍 クエリ検索結果: {len(search_results)}件")

        # デバッグ: 検索処理を手動実行
        if file_manager.local_data_manager:
            manual_results = file_manager.local_data_manager.data_index.search_notes(
                query="テストノート"
            )
            print(f"   🔧 手動検索結果: {len(manual_results)}件")
            print(f"   🔧 手動検索詳細: {manual_results[:3]}")

        assert len(search_results) == 5, (
            f"検索結果が期待値と異なります: {len(search_results)}"
        )

        # タグ検索
        tag_results = file_manager.search_notes_fast(tags=["test"])
        print(f"   🏷️ タグ検索結果: {len(tag_results)}件")
        assert len(tag_results) == 5, (
            f"タグ検索結果が期待値と異なります: {len(tag_results)}"
        )

        # カテゴリ検索
        category_results = file_manager.search_notes_fast(category="test_category_0")
        print(f"   📂 カテゴリ検索結果: {len(category_results)}件")

        # 4. スナップショット作成のテスト
        print("\n4 ️⃣ スナップショット作成のテスト...")
        snapshot_path = await file_manager.create_vault_snapshot("test_snapshot")
        print(f"   📸 スナップショット作成: {snapshot_path}")
        assert snapshot_path and snapshot_path.exists(), (
            "スナップショットの作成に失敗しました"
        )

        # スナップショットファイルサイズ確認
        snapshot_size = snapshot_path.stat().st_size / 1024  # KB
        print(f"   📏 スナップショットサイズ: {snapshot_size:.2f} KB")

        # 5. データエクスポートのテスト
        print("\n5 ️⃣ データエクスポートのテスト...")

        # JSON 形式でエクスポート
        json_export = await file_manager.export_vault_data("json")
        print(f"   📤 JSON エクスポート: {json_export}")
        assert json_export and json_export.exists(), "JSON エクスポートに失敗しました"

        # エクスポートファイルの内容確認
        with open(json_export, encoding="utf-8") as f:
            export_data = json.load(f)

        print(f"   📊 エクスポート統計: {export_data['metadata']['total_notes']}ノート")
        assert export_data["metadata"]["total_notes"] == 5, (
            "エクスポートデータが不正です"
        )

        # ZIP 形式でエクスポート
        zip_export = await file_manager.export_vault_data("zip")
        print(f"   📦 ZIP エクスポート: {zip_export}")
        assert zip_export and zip_export.exists(), "ZIP エクスポートに失敗しました"

        # 6. 統計情報のテスト
        print("\n6 ️⃣ 統計情報のテスト...")
        local_stats = await file_manager.get_local_data_stats()
        print("   📈 ローカルデータ統計:")
        print(f"      - スナップショット数: {local_stats['snapshots']['count']}")
        print(f"      - エクスポート数: {local_stats['exports']['count']}")
        print(f"      - 総ノート数: {local_stats['index']['total_notes']}")
        print(f"      - 総タグ数: {local_stats['index']['total_tags']}")

        assert local_stats["local_data_enabled"], "ローカルデータが有効になっていません"
        assert local_stats["index"]["total_notes"] == 5, "ノート数が不正です"

        # 7. インデックス再構築のテスト
        print("\n7 ️⃣ インデックス再構築のテスト...")
        rebuild_success = await file_manager.rebuild_local_index()
        print(f"   🔄 インデックス再構築: {rebuild_success}")
        assert rebuild_success, "インデックス再構築に失敗しました"

        # 再構築後の検索確認
        rebuilt_results = file_manager.search_notes_fast(query="テストノート")
        print(f"   🔍 再構築後検索結果: {len(rebuilt_results)}件")
        assert len(rebuilt_results) == 5, "再構築後の検索結果が不正です"

        # 8. 自動バックアップのテスト
        print("\n8 ️⃣ 自動バックアップのテスト...")
        auto_backup_success = await file_manager.auto_backup_if_needed()
        print(f"   ⚡ 自動バックアップ: {auto_backup_success}")
        assert auto_backup_success, "自動バックアップに失敗しました"

        # 9. リモート同期テスト（シミュレーション）
        print("\n9 ️⃣ リモート同期テスト...")
        remote_path = Path(temp_dir) / "remote_vault"
        sync_success = await file_manager.sync_with_remote(remote_path, "upload")
        print(f"   🔄 リモート同期: {sync_success}")
        assert sync_success, "リモート同期に失敗しました"

        # リモートディレクトリの確認
        remote_files = list(remote_path.rglob("*.md"))
        print(f"   📁 リモートファイル数: {len(remote_files)}")
        assert len(remote_files) == 5, "リモート同期でファイル数が不正です"

        print("\n ✅ すべてのテストが正常に完了しました！")

        # 最終統計表示
        final_stats = await file_manager.get_local_data_stats()
        print("\n 📊 最終統計:")
        print(f"   - 総ノート数: {final_stats['index']['total_notes']}")
        print(f"   - 総タグ数: {final_stats['index']['total_tags']}")
        print(f"   - スナップショット数: {final_stats['snapshots']['count']}")
        print(f"   - エクスポート数: {final_stats['exports']['count']}")
        print(f"   - Vault パス: {final_stats['vault_path']}")


async def test_performance():
    """パフォーマンステスト"""
    print("\n 🚀 パフォーマンステストを開始...")

    with tempfile.TemporaryDirectory() as temp_dir:
        vault_path = Path(temp_dir) / "perf_vault"
        vault_path.mkdir(parents=True)

        file_manager = ObsidianFileManager(
            vault_path=vault_path, enable_local_data=True
        )
        await file_manager.initialize_local_data()

        # 大量のノートを作成
        print("📝 大量ノート作成テスト...")
        note_count = 100
        start_time = datetime.now()

        for i in range(note_count):
            frontmatter = NoteFrontmatter(
                discord_message_id=i,
                ai_processed=True,
                ai_summary=f"パフォーマンステスト用ノート{i}",
                ai_tags=["#perf", f"#batch{i // 10}"],
                ai_category=f"perf_category_{i % 5}",
                status=NoteStatus.ACTIVE,
                obsidian_folder=VaultFolder.INBOX.value,
            )

            # Obsidian の命名規則に従ったファイル名
            timestamp = datetime.now().strftime("%Y%m%d%H%M")
            filename = (
                f"{timestamp}_perf_category_{i % 5}_パフォーマンステスト{i:03d}.md"
            )

            note = ObsidianNote(
                filename=filename,
                file_path=vault_path / VaultFolder.INBOX.value / filename,
                frontmatter=frontmatter,
                content=f"# パフォーマンステスト{i}\n\n 大量データ処理のテスト用ノートです。ノート番号: {i}",
                created_at=datetime.now(),
                modified_at=datetime.now(),
            )

            await file_manager.save_note(note)

            if (i + 1) % 20 == 0:
                print(f"   📄 {i + 1}/{note_count} 完了")

        creation_time = (datetime.now() - start_time).total_seconds()
        print(
            f"✅ ノート作成完了: {creation_time:.2f}秒 ({note_count / creation_time:.1f} notes/sec)"
        )

        # 検索パフォーマンス
        print("\n 🔍 検索パフォーマンステスト...")
        search_start = datetime.now()

        # 複数の検索を実行
        queries = ["パフォーマンス", "テスト", "データ"]
        for query in queries:
            results = file_manager.search_notes_fast(query=query)
            print(f"   '{query}': {len(results)}件")

        search_time = (datetime.now() - search_start).total_seconds()
        print(f"✅ 検索完了: {search_time:.3f}秒")

        # スナップショット作成パフォーマンス
        print("\n 📸 スナップショット作成パフォーマンス...")
        snapshot_start = datetime.now()
        snapshot_path = await file_manager.create_vault_snapshot("perf_test")
        snapshot_time = (datetime.now() - snapshot_start).total_seconds()

        snapshot_size = snapshot_path.stat().st_size / (1024 * 1024)  # MB
        print(
            f"✅ スナップショット作成: {snapshot_time:.2f}秒 ({snapshot_size:.2f} MB)"
        )


if __name__ == "__main__":
    print("🧪 ローカルデータ管理システム - 統合テスト")
    print("=" * 50)

    # メインテスト実行
    asyncio.run(test_local_data_system())

    # パフォーマンステスト実行
    asyncio.run(test_performance())

    print("\n 🎉 全テスト完了！")
    print("=" * 50)
