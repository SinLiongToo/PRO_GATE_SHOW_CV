import os
import re
import sys
import pathlib
from playwright.sync_api import sync_playwright

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def run_verification():
    html_path = os.path.abspath('index.html')
    file_url = pathlib.Path(html_path).as_uri()
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
        financial_title_zh = page.locator('[data-i18n="title-ai2"]').text_content().strip()
        print(f"Yield Title (ZH): {yield_title_zh}")
        print(f"Test Title (ZH): {test_title_zh}")
        print(f"Financial Title (ZH): {financial_title_zh}")
        assert "良率" in yield_title_zh, "Failed: Chinese title for Yield not found"
        assert "測試" in test_title_zh, "Failed: Chinese title for Test not found"
        assert "財務" in financial_title_zh, "Failed: Chinese title for Financial not found"

        total_cards_zh = page.locator('article.portal-card').count()
        print(f"Total cards found: {total_cards_zh}")
        assert total_cards_zh == 12, f"Expected 12 cards, got {total_cards_zh}"

        # 2. Click Language Toggle to English
        print("\n--- 2. Toggling Language to English ---")
        page.click("#langToggleBtn")
        page.wait_for_timeout(300)

        # Verify English title in Yield and Financial
        yield_title_en = page.locator('[data-i18n="title-test2"]').text_content().strip()
        test_title_en = page.locator('[data-i18n="title-test1"]').text_content().strip()
        financial_title_en = page.locator('[data-i18n="title-ai2"]').text_content().strip()
        print(f"Yield Title (EN): {yield_title_en}")
        print(f"Test Title (EN): {test_title_en}")
        print(f"Financial Title (EN): {financial_title_en}")

        chinese_char_pattern = re.compile(r'[\u4e00-\u9fff]')
        assert not chinese_char_pattern.search(yield_title_en), f"Chinese in Yield EN: {yield_title_en}"
        assert not chinese_char_pattern.search(test_title_en), f"Chinese in Test EN: {test_title_en}"
        assert not chinese_char_pattern.search(financial_title_en), f"Chinese in Financial EN: {financial_title_en}"
        assert "Financial & OpEx" in financial_title_en, "Expected 'Financial & OpEx' in title"

        # Check all 12 card titles in EN
        titles = page.locator('article h3').all_text_contents()
        print(f"\nAll 12 Card Titles in English:")
        for idx, t in enumerate(titles, 1):
            t_clean = t.strip()
            has_chinese = bool(chinese_char_pattern.search(t_clean))
            print(f"  [{idx:02d}] {t_clean} (Has Chinese: {has_chinese})")
            assert not has_chinese, f"Card {idx} still contains Chinese in EN mode: {t_clean}"

        # Check result count badge in EN
        badge_en = page.locator("#resultCountBadge").text_content().strip()
        print(f"Badge in EN: {badge_en}")
        assert "12 Items" in badge_en, f"Expected '12 Items' in badge, got {badge_en}"

        page.screenshot(path="playwright_en_verification.png", full_page=True)

        # 3. Test Search / Find
        print("\n--- 3. Testing Search (Find) Filter ---")
        page.fill("#searchInput", "Financial")
        page.wait_for_timeout(300)
        visible_cards = page.locator('article:visible').count()
        print(f"Search for 'Financial' -> visible cards: {visible_cards}")
        assert visible_cards == 1, f"Expected 1 card visible for 'Financial', got {visible_cards}"

        page.fill("#searchInput", "")
        page.wait_for_timeout(200)

        # 4. Test Theme Toggle & Light Mode Contrast
        print("\n--- 4. Testing Theme Toggle & Light Mode Contrast ---")
        page.click("#themeToggleBtn")
        page.wait_for_timeout(250)
        is_light = page.evaluate("document.documentElement.classList.contains('light')")
        print(f"Theme toggled to light: {is_light}")
        assert is_light, "Expected light theme"

        # Verify high contrast colors in light mode
        desc_color = page.locator('article p').first.evaluate('el => window.getComputedStyle(el).color')
        title_color = page.locator('article h3').first.evaluate('el => window.getComputedStyle(el).color')
        print(f"Light Mode Title Color: {title_color} (Expected dark slate #0f172a)")
        print(f"Light Mode Description Color: {desc_color} (Expected high contrast #334155)")
        assert desc_color == "rgb(51, 65, 85)", f"Expected rgb(51, 65, 85), got {desc_color}"
        assert title_color == "rgb(15, 23, 42)", f"Expected rgb(15, 23, 42), got {title_color}"

        page.screenshot(path="playwright_light_mode.png", full_page=True)
        print("Saved screenshot: playwright_light_mode.png")

        # Switch back to dark theme
        page.click("#themeToggleBtn")
        page.wait_for_timeout(200)

        # 5. Switch back to Chinese
        print("\n--- 5. Switching back to Chinese ---")
        page.click("#langToggleBtn")
        page.wait_for_timeout(300)
        financial_title_zh_again = page.locator('[data-i18n="title-ai2"]').text_content().strip()
        print(f"Financial Title back in ZH: {financial_title_zh_again}")
        assert "財務" in financial_title_zh_again

        browser.close()
        print("\nALL 12 CARDS AND LIGHT MODE TESTS PASSED SUCCESSFULLY! ✅")

if __name__ == '__main__':
    run_verification()
