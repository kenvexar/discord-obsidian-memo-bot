# ブランチ戦略

## 概要

このプロジェクトでは **GitHub Flow + Development Branch** 戦略を採用しています。
個人開発プロジェクトの特性と継続的デプロイメントの要件に最適化されています。

## ブランチ構成

### メインブランチ

#### `main`
- **目的**: 本番環境にデプロイされる安定版コード
- **保護**: プルリクエスト経由でのみマージ可能
- **デプロイ**: 自動デプロイメントのトリガー
- **命名**: `main` (GitHub デフォルト)

#### `develop`
- **目的**: 開発中の機能を統合するブランチ
- **保護**: プルリクエスト経由でのみマージ可能
- **テスト**: CI/CD パイプラインで自動テスト実行
- **リリース**: 安定したら `main` にマージ

### 作業ブランチ

#### Feature ブランチ
- **命名規則**: `feature/機能名` または `feature/issue 番号-機能名`
- **分岐元**: `develop`
- **マージ先**: `develop`
- **例**:
  - `feature/discord-voice-commands`
  - `feature/obsidian-template-system`
  - `feature/123-garmin-integration`

#### Bugfix ブランチ
- **命名規則**: `bugfix/修正内容` または `bugfix/issue 番号-修正内容`
- **分岐元**: `develop` (緊急時は `main`)
- **マージ先**: `develop` (または `main`)
- **例**:
  - `bugfix/discord-message-encoding`
  - `bugfix/456-obsidian-file-permission`

#### Hotfix ブランチ
- **命名規則**: `hotfix/修正内容`
- **分岐元**: `main`
- **マージ先**: `main` および `develop`
- **用途**: 本番環境の緊急修正
- **例**:
  - `hotfix/security-token-leak`
  - `hotfix/critical-bot-crash`

#### Release ブランチ（オプション）
- **命名規則**: `release/バージョン番号`
- **分岐元**: `develop`
- **マージ先**: `main` および `develop`
- **用途**: リリース準備とバージョンアップ
- **例**:
  - `release/v1.2.0`
  - `release/v2.0.0-beta`

## ワークフロー

### 1. 機能開発フロー

```bash
# 1. develop ブランチを最新に更新
git switch develop
git pull origin develop

# 2. feature ブランチを作成
git switch -c feature/新機能名

# 3. 開発作業
# ... コード編集 ...

# 4. コミット（小さく頻繁に）
git add .
git commit -m "feat: 新機能の基本実装"

# 5. リモートに push
git push -u origin feature/新機能名

# 6. Pull Request 作成
# GitHub Web UI で develop ブランチに対して PR 作成

# 7. レビュー・マージ後
git switch develop
git pull origin develop
git branch -d feature/新機能名
```

### 2. リリースフロー

```bash
# 1. release ブランチ作成（必要に応じて）
git switch develop
git pull origin develop
git switch -c release/v1.2.0

# 2. バージョン更新・最終調整
# ... pyproject.toml 等のバージョン更新 ...

# 3. main にマージ
# GitHub Web UI で main ブランチに対して PR 作成

# 4. タグ作成
git switch main
git pull origin main
git tag v1.2.0
git push origin v1.2.0
```

### 3. 緊急修正フロー

```bash
# 1. hotfix ブランチ作成
git switch main
git pull origin main
git switch -c hotfix/緊急修正名

# 2. 修正作業
# ... 緊急修正 ...

# 3. main と develop の両方にマージ
# 1. main への PR 作成・マージ
# 2. develop への PR 作成・マージ
```

## Git 設定

### 推奨ローカル設定

```bash
# リベースベースの pull
git config pull.rebase true

# rerere 有効化（コンフリクト解決の記憶）
git config rerere.enabled true

# デフォルトブランチ名
git config init.defaultBranch main
```

### リポジトリ設定（ GitHub ）

- **Merge 方式**: Squash merge のみ許可
- **ブランチ保護**:
  - `main`: PR 必須、レビュー必須、 CI 成功必須
  - `develop`: PR 必須、 CI 成功必須
- **自動削除**: マージ後の head ブランチ自動削除
- **Linear history**: 必須

## 命名規則

### コミットメッセージ

[Conventional Commits](https://www.conventionalcommits.org/) 形式を採用：

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

#### Type

- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント更新
- `style`: フォーマット（機能に影響しない）
- `refactor`: リファクタリング
- `test`: テスト追加・修正
- `chore`: ビルド・補助ツール関連

#### 例

```
feat(discord): add voice command processing
fix(obsidian): resolve file encoding issue
docs: update API documentation
refactor(ai): improve error handling
test(integration): add Discord bot tests
chore(deps): update dependencies
```

## ベストプラクティス

### Do's ✅

- **小さく頻繁なコミット**: 論理的な単位でコミット
- **意味のあるコミットメッセージ**: 変更内容が分かりやすい
- **PR 前のリベース**: `develop` の最新状態で作業
- **CI/CD の成功確認**: マージ前に全テストパス
- **コードレビュー**: 小さな PR でも自己レビュー実施

### Don'ts ❌

- **直接 main に push**: 必ず PR 経由
- **巨大な PR**: 500 行以上の変更は分割検討
- **WIP コミット**: 作業中状態での push 避ける
- **ブランチの長期保持**: マージ後は速やかに削除
- **merge commit**: squash merge を使用

## ツール連携

### IDE 設定

- **VSCode**: GitLens 拡張推奨
- **コミットテンプレート**: `.gitmessage` 活用

### CI/CD

- **GitHub Actions**: PR 作成時の自動テスト
- **デプロイ**: `main` マージ時の自動デプロイ
- **品質チェック**: ruff 、 mypy 、 pytest の自動実行

## トラブルシューティング

### よくある問題

1. **マージコンフリクト**
   ```bash
   git switch feature/ブランチ名
   git rebase develop
   # コンフリクト解決後
   git rebase --continue
   git push --force-with-lease
   ```

2. **間違ったブランチでの作業**
   ```bash
   # 未コミットの変更がある場合
   git stash
   git switch 正しいブランチ
   git stash pop
   ```

3. **PR 後のクリーンアップ**
   ```bash
   git switch develop
   git pull origin develop
   git branch -d feature/完了したブランチ名
   ```

## 参考資料

- [GitHub Flow](https://docs.github.com/en/get-started/quickstart/github-flow)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Best Practices](https://git-scm.com/book/en/v2)
