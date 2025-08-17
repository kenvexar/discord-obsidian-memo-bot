---
type: daily
date: {{date_ymd}}
tags:
  - daily
  - {{date_format(current_date, "%Y-%m")}}
ai_processed: {{ai_processed}}
{{#if ai_processed}}
ai_summary: "{{ai_summary}}"
ai_category: {{ai_category}}
{{/if}}
---

# 📝 {{#if ai_summary}}{{truncate(ai_summary, 60)}}{{else}}{{date_format(current_date, "%Y年%m月%d日")}} - メモ{{/if}}

{{#if content}}
## 💭 内容

{{content}}

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

**カテゴリ**: {{ai_category}} (信頼度: {{ai_confidence}})

{{#if ai_reasoning}}
**根拠**: {{ai_reasoning}}
{{/if}}

{{/if}}
## 📅 メタデータ

- **作成者**: {{author_name}}
- **作成日時**: {{date_format(current_date, "%Y年%m月%d日 %H:%M:%S")}}
- **チャンネル**: #{{channel_name}}
{{#if ai_processed}}
- **AI処理時間**: {{processing_time}}ms
{{/if}}

{{#if ai_tags}}
## 🏷️ タグ

{{tag_list(ai_tags)}}

{{/if}}
## 🔗 関連リンク

- **Discord Message**: [リンク](https://discord.com/channels/)
- **チャンネル**: #{{channel_name}}

---
*このノートはDiscord-Obsidian Memo Botによって自動生成されました*
