import requests
from bs4 import BeautifulSoup
import json
import time
import re

class AshisutoSitemapCrawler:
    def __init__(self):
        # サイト全体の地図URL
        self.sitemap_url = "https://www.ashisuto.co.jp/sitemap.xml"
        self.output_data = []

    def get_all_article_urls(self):
        """サイトマップからJP1ブログの記事URLをすべて抽出する"""
        print(f"サイトマップを解析中: {self.sitemap_url}")
        try:
            res = requests.get(self.sitemap_url, timeout=10)
            res.raise_for_status()
            # XMLとして解析
            soup = BeautifulSoup(res.content, 'lxml-xml')
            
            # 全ての <loc> タグ（URL）を取得
            all_urls = [loc.text for loc in soup.find_all('loc')]
            
            # JP1ブログの記事URL（/jp1blog/article/xxxx.html）だけに絞り込む
            article_urls = [url for url in all_urls if "/jp1blog/article/" in url]
            
            print(f"合計 {len(article_urls)} 件の記事URLを発見しました。")
            return article_urls
        except Exception as e:
            print(f"サイトマップ解析エラー: {e}")
            return []

    def scrape_article(self, url):
        """記事の本文を抽出"""
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.content, 'html.parser')
            
            title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "No Title"
            
            # 本文エリアの特定（前回の知見を活かし、広めに設定）
            content_area = (
                soup.find('div', id='contents') or 
                soup.find('div', class_='main-column') or
                soup.find('main')
            )
            
            if content_area:
                # 不要なナビゲーションやサイドバーを削除
                for noise in content_area(['nav', 'header', 'footer', 'aside', 'script', 'style', 'div.side-column']):
                    noise.decompose()
                
                body_text = content_area.get_text(separator='\n', strip=True)
                
                self.output_data.append({
                    "text": f"Source: {url}\nCategory: JP1_Blog_Ashisuto\nTitle: {title}\nContent:\n{body_text}"
                })
                print(f"取得成功: {title}")
            
            time.sleep(1) # サーバー負荷軽減
        except Exception as e:
            print(f"記事取得エラー ({url}): {e}")

    def run(self, limit=None):
        """
        limit: テスト用に取得件数を制限する場合に指定
        """
        urls = self.get_all_article_urls()
        
        if limit:
            urls = urls[:limit]
            print(f"テストのため先頭 {limit} 件に制限して実行します。")

        for url in urls:
            self.scrape_article(url)
        
        # 結果を保存
        with open("ashisuto_jp1_blog_full.jsonl", "w", encoding="utf-8") as f:
            for entry in self.output_data:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        print(f"保存完了: {len(self.output_data)} 件のデータを保存しました。")

if __name__ == "__main__":
    crawler = AshisutoSitemapCrawler()
    # まずは動作確認のため limit=10 で実行。問題なければ limit=None に。
    crawler.run(limit=None)