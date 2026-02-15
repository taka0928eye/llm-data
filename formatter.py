import json
import pdfplumber
import pandas as pd
import os
import re

class PdfToLlmCleaner:
    def __init__(self, category):
        self.category = category
        self.output_data = []

    def clean_content(self, text):
        """抽出したテキストをLLM用に洗浄する"""
        if not text:
            return ""

        # 1. 著作権表示・商標などの定型文を削除 (大文字小文字無視)
        text = re.sub(r"Copyright ©.*all rights reserved\.", "", text, flags=re.IGNORECASE)
        text = re.sub(r"Amazon の商標および.*ありません。", "", text, flags=re.DOTALL)
        
        # 2. 目次の点線行を削除 (例: "定義.................. 2")
        text = re.sub(r".*\.{5,}\s*\d+", "", text)
        
        # 3. ページ末尾の見出し＋ページ番号を削除 (例: "序章 1")
        text = re.sub(r"\n.* \d+$", "", text)

        # 4. 特有のゴミ文字・記号の置換
        text = text.replace("$.Name", "項目名")
        
        # 5. 重複する改行を整理
        text = re.sub(r"\n\s*\n", "\n\n", text)
        
        return text.strip()

    def is_toc_page(self, text):
        """目次ページかどうかを判定して除外する"""
        if "Table of Contents" in text or "目次" in text:
            if "...." in text or "．．．．" in text:
                return True
        return False

    def process_pdf(self, pdf_path):
        """PDFの全ページを処理し、テキストと表を抽出・洗浄"""
        filename = os.path.basename(pdf_path)
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_num = i + 1
                    
                    # --- テキスト抽出と洗浄 ---
                    raw_text = page.extract_text()
                    if raw_text and not self.is_toc_page(raw_text):
                        cleaned_text = self.clean_content(raw_text)
                        
                        # 内容が薄いページ（クレンジング後にほぼ空になったもの）は除外
                        if len(cleaned_text) > 30:
                            self.output_data.append({
                                "text": f"Source: {filename}\nCategory: {self.category}\nPage: {page_num}\nType: Text\nContent:\n{cleaned_text}"
                            })

                    # --- 表データの抽出と成型 ---
                    tables = page.extract_tables()
                    if tables:
                        for j, table in enumerate(tables):
                            df = pd.DataFrame(table).fillna("")
                            if not df.empty and len(df.columns) > 1:
                                # 1行目をヘッダーとして処理
                                df.columns = df.iloc[0]
                                df = df[1:]
                                md_table = df.to_markdown(index=False)
                                
                                # 表内のゴミ取り（$.Nameなど）
                                md_table = self.clean_content(md_table)

                                self.output_data.append({
                                    "text": f"Source: {filename}\nCategory: {self.category}\nPage: {page_num}\nType: Table-{j+1}\nContent:\n{md_table}"
                                })
            
            print(f"完了: {filename} ({len(pdf.pages)} ページ処理済み)")
        except Exception as e:
            print(f"エラー ({filename}): {e}")

    def save_jsonl(self, output_filename):
        with open(output_filename, 'w', encoding='utf-8') as f:
            for entry in self.output_data:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        print(f"保存完了: {len(self.output_data)} 件の精緻化データを生成しました。")

# --- 実行 ---
# AWS用
aws_processor = PdfToLlmCleaner(category="AWS_Well_Architected")
aws_processor.process_pdf("wellarchitected-framework.pdf")
aws_processor.process_pdf("wellarchitected-operational-excellence-pillar.pdf")
aws_processor.save_jsonl("cleaned_aws_data.jsonl")
