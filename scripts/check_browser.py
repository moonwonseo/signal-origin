#!/usr/bin/env python3
"""Optional headless UI check; serve only demo/ on localhost before running."""
import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8765")
    parser.add_argument("--browser-executable", type=Path)
    parser.add_argument("--out", type=Path, default=Path("runs/browser"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    errors, external_requests = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=str(args.browser_executable) if args.browser_executable else None)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("request", lambda req: external_requests.append(req.url) if not req.url.startswith(args.url) else None)
        page.goto(args.url)
        page.locator("#metricsBody tr").first.wait_for()
        assert "Synthetic software demonstration" in page.locator(".notice").inner_text()
        combinations = 0
        for horizon in ("63", "21"):
            for policy in ("delayed_180d_primary", "fast_45d_revised_sensitivity"):
                for scope in ("all_available_dates", "recent_dates_from_2024", "year_2022", "year_2023", "year_2024", "year_2025", "year_2026"):
                    page.select_option("#horizon", horizon)
                    page.select_option("#policy", policy)
                    page.select_option("#scope", scope)
                    assert page.locator("#metricsBody tr").count() == 7
                    assert page.locator("#forecastDate option").count() > 0
                    assert page.locator("#pathChart svg").get_attribute("data-future-visible") == "false"
                    page.click("#reveal")
                    assert page.locator("#outcome").is_visible()
                    assert page.locator("#pathChart svg").get_attribute("data-future-visible") == "true"
                    page.click("#reveal")
                    assert not page.locator("#outcome").is_visible()
                    combinations += 1
        for control, value in (("horizon", "63"), ("policy", "delayed_180d_primary"), ("scope", "all_available_dates")):
            page.select_option("#" + control, value)
        dates = page.locator("#forecastDate option").evaluate_all("nodes => nodes.map(n => n.value)")
        page.select_option("#forecastDate", dates[0])
        assert page.locator("#previous").is_disabled()
        page.click("#reveal")
        page.click("#next")
        assert page.locator("#forecastDate").input_value() == dates[1]
        assert not page.locator("#outcome").is_visible()
        page.select_option("#forecastDate", dates[-1])
        assert page.locator("#next").is_disabled()
        page.select_option("#forecastDate", dates[0])
        page.screenshot(path=str(args.out / "desktop.png"), full_page=True)
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.screenshot(path=str(args.out / "mobile.png"))
        page.locator("#replay-title").scroll_into_view_if_needed()
        page.screenshot(path=str(args.out / "mobile-replay.png"))
        page.click("#reveal")
        page.locator("#pathChart").scroll_into_view_if_needed()
        page.screenshot(path=str(args.out / "mobile-revealed.png"))
        assert not errors, errors
        assert not external_requests, external_requests
        result = {"passed": True, "combinations": combinations, "page_errors": errors,
                  "external_requests": external_requests, "mobile_horizontal_overflow": False}
        (args.out / "checks.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result))
        browser.close()


if __name__ == "__main__":
    main()
