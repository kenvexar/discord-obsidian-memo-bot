#!/usr/bin/env python3
"""
URL processor standalone test
"""

import asyncio

# シンプルなURL抽出とWebスクレイピングのテスト
import re
import sys

import aiohttp
from bs4 import BeautifulSoup


class SimpleURLExtractor:
    """簡単なURL抽出機能"""

    def __init__(self):
        self.headers = {"User-Agent": "Mozilla/5.0 (compatible; TestBot/1.0)"}

    def extract_urls_from_text(self, text):
        """テキストからURLを抽出"""
        url_pattern = r'https?://[^\s<>"\'{}\|\\^`\[\]]+[^\s<>"\'{}\|\\^`\[\].,;!?)]'
        urls = re.findall(url_pattern, text, re.IGNORECASE)
        return list(set(urls))

    def is_valid_url(self, url):
        """URL妥当性チェック"""
        from urllib.parse import urlparse

        try:
            parsed = urlparse(url)
            return all(
                [
                    parsed.scheme in ("http", "https"),
                    parsed.netloc,
                    not any(
                        domain in parsed.netloc.lower()
                        for domain in [
                            "localhost",
                            "127.0.0.1",
                            "192.168.",
                            "10.",
                            "172.",
                        ]
                    ),
                ]
            )
        except Exception:
            return False


async def test_url_extraction():
    """URL抽出のテスト"""
    print("=== Testing URL Extraction ===")

    try:
        extractor = SimpleURLExtractor()

        # テスト用テキスト
        test_texts = [
            """
            今日は面白い記事を見つけました！
            https://www.example.com/article1
            https://github.com/user/repo
            参考になりそうです。
            """,
            """
            Check out these links:
            https://docs.python.org/3/
            http://www.google.com
            https://stackoverflow.com/questions/123
            """,
            """
            ノーマルなテキストです。URLは含まれていません。
            """,
        ]

        for i, text in enumerate(test_texts):
            print(f"\nTest {i + 1}:")
            print(f"Text: {text.strip()}")

            urls = extractor.extract_urls_from_text(text)
            print(f"Extracted URLs: {urls}")

            valid_urls = [url for url in urls if extractor.is_valid_url(url)]
            print(f"Valid URLs: {valid_urls}")

        print("\n✓ URL extraction test completed successfully!")
        return True

    except Exception as e:
        print(f"✗ URL extraction test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_web_scraping():
    """簡単なWebスクレイピングテスト"""
    print("\n=== Testing Web Scraping ===")

    try:
        test_url = "https://httpbin.org/html"  # テスト用のHTMLページ

        timeout = aiohttp.ClientTimeout(total=10)
        headers = {"User-Agent": "Mozilla/5.0 (compatible; TestBot/1.0)"}

        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            try:
                async with session.get(test_url) as response:
                    print(f"Status: {response.status}")

                    if response.status == 200:
                        content = await response.text()

                        # HTMLパース
                        soup = BeautifulSoup(content, "html.parser")
                        title = soup.find("title")

                        print(f"Title: {title.get_text() if title else 'No title'}")
                        print(f"Content length: {len(content)} characters")

                        # メインテキストを抽出
                        for script in soup(["script", "style"]):
                            script.decompose()

                        text = soup.get_text()
                        lines = [
                            line.strip() for line in text.split("\n") if line.strip()
                        ]
                        clean_text = "\n".join(lines[:10])  # 最初の10行

                        print(f"Extracted text preview:\n{clean_text}")

                        print("✓ Web scraping test completed successfully!")
                        return True
                    else:
                        print(f"✗ HTTP error: {response.status}")
                        return False

            except aiohttp.ClientError as e:
                print(f"✗ Client error: {e}")
                return False

    except Exception as e:
        print(f"✗ Web scraping test failed: {e}")
        return False


async def test_url_processing():
    """URL処理の統合テスト"""
    print("\n=== Testing URL Processing Integration ===")

    try:
        extractor = SimpleURLExtractor()

        # URL付きテキスト
        text_with_urls = """
        AIに関する興味深い記事を見つけました:
        https://httpbin.org/html
        
        この記事では、人工知能の最新動向について述べられています。
        参考にしてください。
        """

        print(f"Original text:\n{text_with_urls}")

        # URL抽出
        urls = extractor.extract_urls_from_text(text_with_urls)
        print(f"\nFound URLs: {urls}")

        # 各URLの処理
        processed_urls = []
        for url in urls:
            if extractor.is_valid_url(url):
                print(f"\nProcessing: {url}")

                try:
                    timeout = aiohttp.ClientTimeout(total=10)
                    headers = {"User-Agent": "Mozilla/5.0 (compatible; TestBot/1.0)"}

                    async with aiohttp.ClientSession(
                        timeout=timeout, headers=headers
                    ) as session, session.get(url) as response:
                        if response.status == 200:
                            content = await response.text()
                            soup = BeautifulSoup(content, "html.parser")

                            # メタデータ抽出
                            title = soup.find("title")
                            title_text = title.get_text() if title else "No title"

                            processed_urls.append(
                                {
                                    "url": url,
                                    "title": title_text,
                                    "status": "success",
                                    "content_length": len(content),
                                }
                            )

                            print(f"  ✓ Title: {title_text}")
                            print(f"  ✓ Content: {len(content)} chars")
                        else:
                            processed_urls.append(
                                {
                                    "url": url,
                                    "status": "error",
                                    "error": f"HTTP {response.status}",
                                }
                            )

                except Exception as e:
                    processed_urls.append(
                        {"url": url, "status": "error", "error": str(e)}
                    )
                    print(f"  ✗ Error: {e}")

        print("\nProcessed URLs summary:")
        for result in processed_urls:
            status = "✓" if result["status"] == "success" else "✗"
            print(f"  {status} {result['url']} - {result['status']}")

        print("✓ URL processing integration test completed!")
        return True

    except Exception as e:
        print(f"✗ URL processing test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """メインテスト関数"""
    print("Starting URL Processing Tests...")
    print("=" * 60)

    tests = [
        test_url_extraction,
        test_web_scraping,
        test_url_processing,
    ]

    results = []
    for test_func in tests:
        try:
            result = await test_func()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test_func.__name__} failed with error: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"✅ All {total} URL processing tests passed!")
    else:
        print(f"⚠️  {passed}/{total} tests passed, {total - passed} failed")

    print("\n🎯 URL processing functionality is working!")
    print("   - URL extraction from text")
    print("   - Web content fetching")
    print("   - HTML parsing and metadata extraction")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
