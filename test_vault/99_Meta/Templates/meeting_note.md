---
type: meeting
date: {{date_ymd}}
tags:
  - meeting
  - {{ai_category}}
ai_processed: {{ai_processed}}
participants: []
---

# 🏢 会議メモ - {{date_format(current_date, "%Y-%m-%d")}}

## ℹ️ 基本情報

- **日時**: {{date_format(current_date, "%Y年%m月%d日 %H:%M")}}
- **参加者**:
- **場所**:

## 📋 議題

{{#if ai_key_points}}
{{#each ai_key_points}}
1. {{@item}}
{{/each}}
{{else}}
1. 議題項目1
2. 議題項目2
{{/if}}

## 💬 討議内容

{{#if content}}
{{content}}
{{else}}
会議の内容をここに記録する。
{{/if}}

{{#if ai_processed}}
## 🤖 AI要約

{{ai_summary}}

**カテゴリ**: {{ai_category}} ({{ai_confidence}})
{{/if}}

## ✅ アクションアイテム

- [ ] TODO項目1
- [ ] TODO項目2

## 📝 次回までの課題

-

## 🔗 関連資料

-
