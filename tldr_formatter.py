import os
import json
import re

def parse_tldr_to_text(file_path, platform, lang='en'):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # コマンド名の抽出
    command_match = re.search(r'^#\s+(.+)', content, re.MULTILINE)
    command_name = command_match.group(1).strip() if command_match else "Unknown"

    # 概要の抽出
    description_match = re.findall(r'>\s+(.+)', content)
    description = " ".join(description_match) if description_match else ""

    # 使用例の抽出
    example_pairs = re.findall(r'-\s+(.+?):\n\n`(.+?)`', content)
    
    # プラットフォーム名のラベル設定
    platform_labels = {
        "linux": "Linux",
        "windows": "Windows",
        "common": "共通(Common)"
    }
    plt_label = platform_labels.get(platform, "汎用")
    
    if lang == 'ja':
        prefix = f"{plt_label}コマンド「{command_name}」の解説:"
        usage_label = "主な使い方は以下の通りです。"
    else:
        prefix = f"{plt_label} command '{command_name}' overview:"
        usage_label = "Common usage examples:"

    examples_text = ""
    for desc, cmd in example_pairs:
        examples_text += f"\n・{desc}: `{cmd}`"

    full_text = f"{prefix} {description}\n{usage_label}{examples_text}"
    
    return {"text": full_text}

def main():
    # 対象とするディレクトリのリスト
    targets = ["linux", "windows", "common"]
    output_file = 'tldr_hybrid_full_v2.jsonl'
    
    results_count = 0
    with open(output_file, 'w', encoding='utf-8') as f:
        for platform in targets:
            ja_path = f'./tldr/pages.ja/{platform}'
            en_path = f'./tldr/pages/{platform}'

            # ファイルリスト取得（日本語・英語両方）
            ja_commands = set()
            if os.path.exists(ja_path):
                ja_commands = {f for f in os.listdir(ja_path) if f.endswith('.md')}
            
            en_commands = set()
            if os.path.exists(en_path):
                en_commands = {f for f in os.listdir(en_path) if f.endswith('.md')}

            all_command_files = ja_commands | en_commands
            
            for cmd_file in sorted(all_command_files):
                # 日本語版を優先、なければ英語版
                if cmd_file in ja_commands:
                    target_path = os.path.join(ja_path, cmd_file)
                    data = parse_tldr_to_text(target_path, platform, lang='ja')
                else:
                    target_path = os.path.join(en_path, cmd_file)
                    data = parse_tldr_to_text(target_path, platform, lang='en')
                
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
                results_count += 1

    print(f"完了！ 合計 {results_count} 個のコマンド（Linux/Windows/Common）を処理しました。")
    print(f"出力ファイル: {output_file}")

if __name__ == "__main__":
    main()