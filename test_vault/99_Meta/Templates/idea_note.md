---
type: idea
created: {{date_iso}}
tags:
  - idea
  - {{ai_category}}
{{#if ai_tags}}
{{#each ai_tags}}
  - {{@item}}
{{/each}}
{{/if}}
ai_processed: {{ai_processed}}
{{#if ai_processed}}
ai_summary: "{{ai_summary}}"
ai_confidence: {{ai_confidence}}
{{/if}}
---

# 💡 {{#if ai_summary}}{{truncate(ai_summary, 50)}}{{else}}新しいアイデア{{/if}}

{{#if content}}
## 📝 内容

{{content}}

{{else}}
## 📝 内容

アイデアの内容をここに記録する。

{{/if}}
{{#if ai_processed}}
## 🤖 AI分析

**要約**: {{ai_summary}}

{{#if ai_key_points}}
### 主要ポイント
{{#each ai_key_points}}
- {{@item}}
{{/each}}
{{/if}}

**分類**: {{ai_category}} (信頼度: {{ai_confidence}})

{{#if ai_reasoning}}
**根拠**: {{ai_reasoning}}
{{/if}}
{{/if}}

## 🔄 次のアクション

- [ ] アイデアを詳細化する
- [ ] 実現可能性を検討する
- [ ] 関連する情報を収集する

{{#if ai_tags}}
## 🏷️ タグ

{{tag_list(ai_tags)}}

{{/if}}
## 📅 作成日時

{{date_format(current_date, "%Y年%m月%d日 %H:%M")}}

---
*このノートはDiscord-Obsidian Memo Botによって自動生成されました*
