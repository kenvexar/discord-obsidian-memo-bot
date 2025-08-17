# よくある問題と解決方法

Discord-Obsidian Memo Botの使用中によくある問題とその解決方法を説明します。

## 🚀 セットアップ関連の問題

### ボットが起動しない

**症状:** `uv run python -m src.main`実行時にエラーが発生

**解決方法:**
```bash
# 1. 依存関係を再インストール
uv sync

# 2. Python バージョンを確認（3.11以上が必要）
python --version

# 3. 環境変数の確認
cat .env | grep -E "(DISCORD_BOT_TOKEN|GEMINI_API_KEY|OBSIDIAN_VAULT_PATH)"
```

### Discord認証エラー

**症状:** `discord.errors.LoginFailure: Improper token has been passed.`

**解決方法:**
1. [Discord Developer Portal](https://discord.com/developers/applications)でトークンを確認
2. `.env`ファイルの`DISCORD_BOT_TOKEN`を正しいトークンに更新
3. ボットに必要な権限（Send Messages、Read Message History、Attach Files、Use Slash Commands）が付与されているか確認

### Obsidian Vaultアクセスエラー

**症状:** `FileNotFoundError`または`PermissionError`

**解決方法:**
```bash
# 1. Vaultパスの存在確認
ls -la "$OBSIDIAN_VAULT_PATH"

# 2. 書き込み権限の確認
touch "$OBSIDIAN_VAULT_PATH/test_file.md"
rm "$OBSIDIAN_VAULT_PATH/test_file.md"

# 3. 必要なフォルダを作成
mkdir -p "$OBSIDIAN_VAULT_PATH"/{00_Inbox,01_Projects,02_DailyNotes,03_Ideas,04_Archive,05_Resources,06_Finance,07_Tasks,08_Health,99_Meta}
```

## 🤖 AI処理関連の問題

### Gemini APIエラー

**症状:** `API key not valid`または応答なし

**解決方法:**
1. [Google AI Studio](https://aistudio.google.com/)でAPIキーを確認
2. `.env`ファイルの`GEMINI_API_KEY`を正しいキーに更新
3. API制限の確認：Discordで`/ai_stats`コマンドを実行

### AI処理が遅い、または応答しない

**症状:** メッセージを送信してもAI分析が実行されない

**解決方法:**
```bash
# 1. API制限の確認
# Discord で以下のコマンドを実行
/ai_stats
/status

# 2. 手動でAI処理をテスト
/ai_process テキスト:テストメッセージ
```

## 🎤 音声処理関連の問題

### 音声文字起こしが実行されない

**症状:** 音声ファイルをアップロードしても文字起こしされない

**解決方法:**
1. **ファイル形式を確認:** 対応形式（MP3, WAV, FLAC, OGG, M4A, WEBM）か確認
2. **ファイルサイズを確認:** 大きすぎる場合は圧縮
3. **API認証情報の確認:**
   ```bash
   echo $GOOGLE_APPLICATION_CREDENTIALS
   ls -la "$GOOGLE_APPLICATION_CREDENTIALS"
   ```
4. **月間制限の確認:** Discordで`/status`コマンドを実行

### 音声認識の精度が低い

**改善方法:**
- 静かな環境で録音
- マイクを口に近づける
- 明瞭に話す
- 可能であれば前処理でノイズ除去

## 📝 メッセージ処理関連の問題

### メッセージが処理されない

**症状:** Discordにメッセージを投稿してもObsidianに保存されない

**解決方法:**
1. **チャンネル設定の確認:**
   ```bash
   cat .env | grep CHANNEL_
   ```
2. **ボットの権限確認:**
   - ボットが対象チャンネルを閲覧できるか
   - ボットがメッセージを読み取れるか
   - ボットが当該サーバーに参加しているか
3. **ボットの動作状況確認:**
   ```bash
   # Discord で以下のコマンドを実行
   /status
   /ping
   ```

## 🔧 システム関連の問題

### ディスク容量不足

**症状:** `OSError: [Errno 28] No space left on device`

**解決方法:**
```bash
# 1. ディスク使用量確認
df -h

# 2. Vault サイズ確認
du -sh "$OBSIDIAN_VAULT_PATH"

# 3. 古い音声ファイルの削除（90日以上前）
find "$OBSIDIAN_VAULT_PATH/06_Attachments/Audio" -name "*.mp3" -mtime +90 -delete
```

## 🔍 デバッグ方法

### ログの確認

```bash
# 1. デバッグモードで起動
echo "LOG_LEVEL=DEBUG" >> .env
uv run python -m src.main --debug

# 2. エラーログの確認
grep "ERROR" bot.log

# 3. リアルタイムでログを監視
tail -f bot.log
```

### Discord コマンドでの状態確認

```bash
# ボットの状態確認
/status

# AI処理統計
/ai_stats

# Vault統計
/vault_stats

# 接続テスト
/ping
```

## 🛠️ 緊急時の復旧

### ボットが完全に応答しない場合

```bash
# 1. プロセスを強制終了
pkill -9 -f "python -m src.main"

# 2. 設定をリセット
cp .env.example .env
# .envファイルを再設定

# 3. ボットを再起動
uv run python -m src.main
```

## ❓ FAQ

**Q: ボットが「オフライン」表示になる**
A: Discord Developer Portalでボットトークンを確認し、必要に応じて再生成してください。

**Q: 音声ファイルの文字起こしができない**
A: Google Cloud Speech-to-Text APIの認証情報と月間制限を確認してください。

**Q: AI分析の精度を上げたい**
A: より具体的で詳細なメッセージを投稿し、関連するタグ（#work、#learning等）を含めてください。

**Q: Obsidianでノートが見つからない**
A: `/vault_search`コマンドで検索するか、`/vault_organize true`でVaultを整理してください。

問題が解決しない場合は、エラーログと共にGitHub Issuesで報告してください。
