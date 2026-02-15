import json

def inject_tags_into_text(data):
    text_content = data["text"].lower()
    tags = []
    
    # --- タグ判定ロジック ---
    # JP1製品
    if any(k in text_content for k in ["ajs", "ジョブ管理", "スケジュール"]): tags.append("JP1/AJS")
    if any(k in text_content for k in ["im", "統合管理", "ビューア"]): tags.append("JP1/IM")
    if any(k in text_content for k in ["pfm", "パフォーマンス", "監視"]): tags.append("JP1/PFM")
    
    # クラウド
    if "aws" in text_content: tags.append("AWS")
    if "gcp" in text_content or "google cloud" in text_content: tags.append("GCP")
    
    # 内容の種類
    if any(k in text_content for k in ["エラー", "トラブル", "失敗", "解決"]): tags.append("Troubleshooting")
    if any(k in text_content for k in ["構築", "セットアップ", "インストール"]): tags.append("Setup")
    if any(k in text_content for k in ["設計", "アーキテクチャ", "ベストプラクティス"]): tags.append("Design")

    # --- テキストへの埋め込み処理 ---
    # タグを [AWS][JP1/AJS] のような形式の文字列にする
    tag_str = "".join([f"[{t}]" for t in tags])
    
    # 既存の text 属性の先頭（Source情報の後など）に挿入
    # 構造: "Source: ... \nTags: [AWS][JP1/AJS] \nCategory: ... "
    lines = data["text"].split('\n')
    # 2行目（Categoryの前あたり）にタグ行を挿入
    lines.insert(1, f"Tags: {tag_str}")
    
    data["text"] = '\n'.join(lines)
    return data

# 実行処理
input_file = "ashisuto_jp1_blog_full.jsonl"
output_file = "final_jp1_llm_data.jsonl"

with open(input_file, "r", encoding="utf-8") as f_in, \
     open(output_file, "w", encoding="utf-8") as f_out:
    
    count = 0
    for line in f_in:
        data = json.loads(line)
        updated_data = inject_tags_into_text(data)
        f_out.write(json.dumps(updated_data, ensure_ascii=False) + '\n')
        count += 1

print(f"完了！ {count} 件のデータにタグを直接埋め込み、{output_file} に保存しました。")