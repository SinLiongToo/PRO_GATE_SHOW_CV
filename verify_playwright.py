import os
import re
import sys
from playwright.sync_api import sync_playwright

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def run_verification():
    html_path = os.path.abspath('index.html')
    file_url = f"file:///{html_path.replace(os.sep, '/')}"
    print(f"Loading: {file_url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        page = context.new_page()
        page.goto(file_url)

        # 1. Verify default Chinese version
        print("\n--- 1. Testing Default (Chinese) ---")
        yield_title_zh = page.locator('[data-i18n="title-test2"]').text_content().strip()
        test_title_zh = page.locator('[data-i18n="title-test1"]').text_content().strip()
        print(f"Yield Title (ZH): {yield_title_zh}")
        print(f"Test Title (ZH): {test_title_zh}")
        assert "良率" in yield_title_zh, "Failed: Chinese title for Yield not found"
        assert "測試" in test_title_zh, "Failed: Chinese title for Test not found"

        # 2. Click Language Toggle to English
        print("\n--- 2. Toggling Language to English ---")
        page.click("#langToggleBtn")
        page.wait_for_timeout(300)

        # Verify English title in Yield
        yield_title_en = page.locator('[data-i18n="title-test2"]').text_content().strip()
        test_title_en = page.locator('[data-i18n="title-test1"]').text_content().strip()
        print(f"Yield Title (EN): {yield_title_en}")
        print(f"Test Title (EN): {test_title_en}")

        # Check for any Chinese characters in Yield & Test titles
        chinese_char_pattern = re.compile(r'[\u4e00-\u9fff]')
        assert not chinese_char_pattern.search(yield_title_en), f"Error: Chinese character found in EN Yield title: {yield_title_en}"
        assert not chinese_char_pattern.search(test_title_en), f"Error: Chinese character found in EN Test title: {test_title_en}"
        assert "Yield Improvement" in yield_title_en, "Expected 'Yield Improvement' in title"

        # Check all 11 card titles in EN
        titles = page.locator('article h3').all_text_contents()
        print(f"\nAll 11 Card Titles in English:")
        for idx, t in enumerate(titles, 1):
            t_clean = t.strip()
            has_chinese = bool(chinese_char_pattern.search(t_clean))
            print(f"  [{idx:02d}] {t_clean} (Has Chinese: {has_chinese})")
            assert not has_chinese, f"Card {idx} still contains Chinese in EN mode: {t_clean}"

        # Check result count badge in EN
        badge_en = page.locator("#resultCountBadge").text_content().strip()
        print(f"Badge in EN: {badge_en}")
        assert "Items" in badge_en, f"Expected 'Items' in badge, got {badge_en}"

        # Screenshot English version
        page.screenshot(path="playwright_en_verification.png", full_page=True)
        print("Saved screenshot: playwright_en_verification.png")

        # 3. Test Search / Find
        print("\n--- 3. Testing Search (Find) Filter ---")
        page.fill("#searchInput", "Yield")
        page.wait_for_timeout(300)
        visible_cards = page.locator('article:visible').count()
        print(f"Search for 'Yield' -> visible cards: {visible_cards}")
        assert visible_cards >= 1, "Expected at least 1 card visible for 'Yield'"

        page.fill("#searchInput", "")
        page.wait_for_timeout(200)

        # 4. Test Theme Toggle
        print("\n--- 4. Testing Theme Toggle ---")
        page.click("#themeToggleBtn")
        page.wait_for_timeout(200)
        is_light = page.evaluate("document.documentElement.classList.contains('light')")
        print(f"Theme toggled to light: {is_light}")
        assert is_light, "Expected light theme"

        # Switch back to dark theme
        page.click("#themeToggleBtn")
        page.wait_for_timeout(200)

        # 5. Switch back to Chinese
        print("\n--- 5. Switching back to Chinese ---")
        page.click("#langToggleBtn")
        page.wait_for_timeout(300)
        yield_title_zh_again = page.locator('[data-i18n="title-test2"]').text_content().strip()
        print(f"Yield Title back in ZH: {yield_title_zh_again}")
        assert "良率" in yield_title_zh_again

        page.screenshot(path="playwright_zh_verification.png", full_page=True)
        print("Saved screenshot: playwright_zh_verification.png")

        browser.close()
        print("\nALL PLAYWRIGHT TESTS PASSED SUCCESSFULLY! ✅")

if __name__ == '__main__':
    run_verification()
