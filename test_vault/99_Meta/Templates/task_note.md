---
type: task
created: {{date_iso}}
status: pending
priority: medium
tags:
  - task
  - {{ai_category}}
{{#if ai_tags}}
{{#each ai_tags}}
  - {{@item}}
{{/each}}
{{/if}}
due_date:
ai_processed: {{ai_processed}}
---

# ✅ {{#if ai_summary}}{{truncate(ai_summary, 60)}}{{else}}新しいタスク{{/if}}

## 📋 タスク詳細

{{#if content}}
{{content}}
{{else}}
タスクの詳細をここに記録する。
{{/if}}

{{#if ai_processed}}
## 🤖 AI分析

**要約**: {{ai_summary}}

{{#if ai_key_points}}
### アクションポイント
{{#each ai_key_points}}
- [ ] {{@item}}
{{/each}}
{{/if}}

**カテゴリ**: {{ai_category}} (信頼度: {{ai_confidence}})
{{/if}}

## ⏰ スケジュール

- **作成日**: {{date_format(current_date, "%Y-%m-%d")}}
- **期限**: 未設定
- **見積時間**:

## 📊 進捗

- [ ] 準備段階
- [ ] 実行中
- [ ] レビュー
- [ ] 完了

## 💭 メモ

作業中のメモや気づきをここに記録する。

## 🔗 関連リンク

-
