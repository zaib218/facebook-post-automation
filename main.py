"""
Facebook Group Auto-Poster
Async multi-account Playwright bot with 2FA, post rotation, and duplicate tracking.
"""

from __future__ import annotations

import asyncio
import json
import os
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pyotp
from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    async_playwright,
)

# ========================= CONFIG =========================
ACCOUNTS_FILE = "accounts.json"
POSTS_FILE = "posts.json"
GROUPS_FILE = "groups.json"
POSTED_GROUPS_FILE = "posted_groups.txt"

MAX_CONCURRENT_TABS = 3
LOOP_POSTING = False
BATCH_DELAY_SECONDS = 120
PER_POST_DELAY_RANGE = (10, 25)
LOGIN_TIMEOUT_MS = 60_000
NAV_TIMEOUT_MS = 60_000

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

SCRIPT_DIR = Path(__file__).resolve().parent
# ==========================================================


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_group_url(entry: Any) -> str | None:
    """Accept a plain URL string or legacy {url|username} objects."""
    if isinstance(entry, str):
        raw = entry.strip()
    elif isinstance(entry, dict):
        raw = str(entry.get("username") or entry.get("url") or "").strip()
    else:
        return None

    if not raw:
        return None

    match = re.search(r"groups/([A-Za-z0-9._-]+)", raw)
    if match:
        return f"https://web.facebook.com/groups/{match.group(1)}/"
    if "facebook.com" not in raw:
        return f"https://web.facebook.com/groups/{raw}/"
    return raw if raw.endswith("/") else f"{raw}/"


def resolve_image_paths(image_field: Any) -> list[str]:
    """Normalize posts.json `image` (string or list) into existing absolute paths."""
    if not image_field:
        return []
    names = image_field if isinstance(image_field, list) else [image_field]
    paths: list[str] = []
    for name in names:
        full = SCRIPT_DIR / name if not os.path.isabs(str(name)) else Path(name)
        if full.exists():
            paths.append(str(full))
        else:
            print(f"\t[!] Image not found, skipped: {full}")
    return paths


class PostedGroupsTracker:
    """Thread-safe tracker shared across concurrent account workers."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = asyncio.Lock()
        self._urls: set[str] = set()
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    url = line.strip()
                    if url:
                        self._urls.add(self._canonical(url))

    @staticmethod
    def _canonical(url: str) -> str:
        normalized = normalize_group_url(url)
        return (normalized or url).rstrip("/").lower()

    async def already_posted(self, url: str) -> bool:
        async with self._lock:
            return self._canonical(url) in self._urls

    async def mark_posted(self, url: str) -> None:
        canonical = self._canonical(url)
        async with self._lock:
            if canonical in self._urls:
                return
            self._urls.add(canonical)
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(f"{canonical}\n")


class FacebookAsyncBot:
    def __init__(
        self,
        accounts: list[dict],
        posts: list[dict],
        groups: list[str],
        tracker: PostedGroupsTracker,
    ) -> None:
        self.accounts = accounts
        self.posts = posts
        self.groups = groups
        self.tracker = tracker
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_TABS)

    async def run(self) -> None:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=False,
                channel="chrome",
                args=["--start-maximized", "--disable-notifications"],
            )
            try:
                while True:
                    tasks = [
                        self.run_account(browser, account)
                        for account in self.accounts
                    ]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    for account, result in zip(self.accounts, results):
                        if isinstance(result, Exception):
                            email = account.get("email", "?")
                            print(f"[-] Account fatal error ({email}): {result}")

                    if not LOOP_POSTING:
                        print("[*] Finished one full run (LOOP_POSTING=False).")
                        break

                    print(
                        f"[*] Batch complete. Waiting {BATCH_DELAY_SECONDS}s "
                        "before next loop..."
                    )
                    await asyncio.sleep(BATCH_DELAY_SECONDS)
            except asyncio.CancelledError:
                print("\n[!] Cancelled.")
            finally:
                await browser.close()

    async def run_account(self, browser: Browser, account: dict) -> None:
        email = account.get("email", "unknown")
        async with self.semaphore:
            print(f"\n{'=' * 50}\n[*] Starting account: {email}\n{'=' * 50}")
            context: BrowserContext | None = None
            try:
                context = await browser.new_context(
                    no_viewport=True,
                    user_agent=USER_AGENT,
                )
                page = await context.new_page()
                logged_in = await self.ensure_logged_in(context, page, account)
                if not logged_in:
                    print(f"[-] Login failed for {email}. Skipping.")
                    return
                await self.post_to_groups(page, email)
            except Exception as exc:
                print(f"[-] Error on account {email}: {exc}")
            finally:
                if context is not None:
                    try:
                        await context.close()
                    except Exception:
                        pass

    async def ensure_logged_in(
        self,
        context: BrowserContext,
        page: Page,
        account: dict,
    ) -> bool:
        session_file = SCRIPT_DIR / account.get("session_file", "sessions/session.json")
        session_file.parent.mkdir(parents=True, exist_ok=True)

        if session_file.exists():
            try:
                cookies = load_json(session_file)
                if isinstance(cookies, list):
                    await context.add_cookies(cookies)
                await page.goto("https://web.facebook.com/", timeout=NAV_TIMEOUT_MS)
                await asyncio.sleep(random.uniform(3, 5))
                if not await self._is_login_page(page):
                    print(f"[+] Session restored: {session_file.name}")
                    return True
                print("[!] Session expired. Logging in with credentials...")
            except Exception as exc:
                print(f"[!] Failed to restore session: {exc}")

        return await self.login_with_credentials(context, page, account, session_file)

    async def login_with_credentials(
        self,
        context: BrowserContext,
        page: Page,
        account: dict,
        session_file: Path,
    ) -> bool:
        email = account.get("email", "")
        password = account.get("password", "")
        secret = account.get("2fa_secret") or account.get("twofa_secret") or ""

        if not email or not password:
            print("[-] Missing email/password in accounts.json")
            return False

        try:
            await page.goto("https://web.facebook.com/login", timeout=LOGIN_TIMEOUT_MS)
            await asyncio.sleep(random.uniform(2, 4))

            email_input = page.locator("input[name='email']").first
            pass_input = page.locator("input[name='pass']").first
            await email_input.fill(email)
            await asyncio.sleep(random.uniform(0.4, 1.0))
            await pass_input.fill(password)
            await asyncio.sleep(random.uniform(0.4, 1.0))

            login_btn = page.locator("button[name='login']").first
            if await login_btn.count() > 0:
                await login_btn.click()
            else:
                await pass_input.press("Enter")

            await asyncio.sleep(random.uniform(4, 6))
            await self.handle_2fa(page, secret)
            await asyncio.sleep(random.uniform(3, 5))

            if await self._is_login_page(page):
                print("[-] Still on login page after credentials/2FA.")
                return False

            cookies = await context.cookies()
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(cookies, f, indent=2)
            print(f"[+] Login OK. Session saved -> {session_file}")
            return True
        except Exception as exc:
            print(f"[-] Login error: {exc}")
            return False

    async def handle_2fa(self, page: Page, secret: str) -> None:
        """Detect Facebook 2FA / approval code prompts and fill a TOTP code."""
        if not secret:
            print("[!] No 2fa_secret configured; skipping automated 2FA.")
            return

        selectors = [
            "input#approvals_code",
            "input[name='approvals_code']",
            "input[autocomplete='one-time-code']",
            "input[inputmode='numeric']",
            "input[type='text'][maxlength='6']",
            "input[type='tel'][maxlength='6']",
        ]

        code_input = None
        for _ in range(8):
            for sel in selectors:
                loc = page.locator(sel)
                try:
                    if await loc.count() > 0 and await loc.first.is_visible():
                        code_input = loc.first
                        break
                except Exception:
                    continue
            if code_input is not None:
                break

            # Checkpoint / two-factor wording on page
            body = (await page.content()).lower()
            if any(
                token in body
                for token in (
                    "two-factor",
                    "authentication code",
                    "approvals_code",
                    "login code",
                    "kode autentikasi",
                    "kode login",
                )
            ):
                await asyncio.sleep(1.5)
                continue
            break

        if code_input is None:
            return

        try:
            totp = pyotp.TOTP(secret.replace(" ", "").upper())
            code = totp.now()
            print(f"[*] Entering 2FA code: {code}")
            await code_input.fill(code)
            await asyncio.sleep(random.uniform(0.5, 1.2))

            submit_selectors = [
                "button[type='submit']",
                "button[name='submit[Submit Code]']",
                "button[id='checkpointSubmitButton']",
                "//button[contains(., 'Continue')]",
                "//button[contains(., 'Submit')]",
                "//button[contains(., 'Lanjutkan')]",
                "//div[@role='button' and (contains(., 'Continue') or contains(., 'Submit') or contains(., 'Lanjutkan'))]",
            ]
            for sel in submit_selectors:
                try:
                    btn = page.locator(sel).first
                    if await btn.count() > 0 and await btn.is_visible():
                        await btn.click()
                        print("[+] 2FA submitted.")
                        await asyncio.sleep(random.uniform(3, 5))
                        return
                except Exception:
                    continue

            await code_input.press("Enter")
            print("[+] 2FA submitted via Enter.")
            await asyncio.sleep(random.uniform(3, 5))
        except Exception as exc:
            print(f"[-] 2FA handling failed: {exc}")

    @staticmethod
    async def _is_login_page(page: Page) -> bool:
        try:
            if await page.locator("input[name='email']").count() > 0:
                return True
            url = page.url.lower()
            return "login" in url or "checkpoint" in url
        except Exception:
            return True

    async def post_to_groups(self, page: Page, account_email: str) -> None:
        for group_url in self.groups:
            if await self.tracker.already_posted(group_url):
                print(f"[*] SKIP (already posted): {group_url}")
                continue

            post = random.choice(self.posts)
            text = post.get("text", "").strip()
            # Optional timestamp so near-identical templates still vary slightly
            stamp = datetime.now().strftime("%H:%M:%S")
            content = f"{text}\n(Jam: {stamp})" if text else stamp
            images = resolve_image_paths(post.get("image"))

            print(f"\n[{account_email}] Opening: {group_url}")
            try:
                success = await self.post_once(page, group_url, content, images)
                if success:
                    await self.tracker.mark_posted(group_url)
                    print(f"\t[+] Marked posted: {group_url}")
                delay = random.uniform(*PER_POST_DELAY_RANGE)
                print(f"\t[*] Waiting {delay:.1f}s before next group...")
                await asyncio.sleep(delay)
            except Exception as exc:
                print(f"\t[-] Group error: {exc}")
                continue

    async def post_once(
        self,
        page: Page,
        group_url: str,
        content: str,
        image_paths: list[str],
    ) -> bool:
        await page.goto(group_url, timeout=NAV_TIMEOUT_MS)
        await asyncio.sleep(random.uniform(5, 8))

        join_btn = page.locator(
            "//div[@aria-label='Gabung ke grup' or @aria-label='Join group']"
        )
        if await join_btn.count() > 0:
            print("\t[!] SKIP: Not a member of this group.")
            return False

        if not await self._open_composer(page):
            print("\t[-] Could not open composer.")
            return False

        await asyncio.sleep(random.uniform(1.5, 2.5))
        try:
            editor = page.locator(
                "div[role='dialog'] div[contenteditable='true']"
            ).first
            await editor.click()
            await page.keyboard.type(content, delay=random.randint(15, 40))
        except Exception:
            await page.keyboard.type(content, delay=random.randint(15, 40))

        if image_paths:
            await self._upload_images(page, image_paths)

        if not await self._click_post(page):
            print("\t[-] Failed to click Post.")
            return False

        await asyncio.sleep(random.uniform(4, 6))
        print("\t[+] Post submitted.")
        return True

    async def _open_composer(self, page: Page) -> bool:
        # Shortcut P
        try:
            await page.locator("body").click()
            await page.keyboard.press("p")
            await asyncio.sleep(2.5)
            if await page.locator("div[role='dialog']").count() > 0:
                print("\t[+] Composer opened (shortcut P)")
                return True
        except Exception:
            pass

        selectors = [
            "//span[contains(text(), 'Tulis sesuatu...')]",
            "//span[contains(text(), 'Write something...')]",
            "//span[contains(text(), 'Jual Sesuatu')]",
            "//span[contains(text(), 'Apa yang Anda jual')]",
            "//div[contains(@class, 'x1i10hfl') and contains(text(), 'Tulis sesuatu...')]",
        ]
        for sel in selectors:
            try:
                loc = page.locator(sel)
                if await loc.count() > 0:
                    await loc.first.click()
                    await asyncio.sleep(2)
                    if await page.locator("div[role='dialog']").count() > 0:
                        print("\t[+] Composer opened (selector)")
                        return True
            except Exception:
                continue
        return False

    async def _upload_images(self, page: Page, image_paths: list[str]) -> None:
        print(f"\t[*] Uploading {len(image_paths)} image(s)...")
        photo_icons = [
            "//div[@aria-label='Foto/video']",
            "//div[@aria-label='Photo/Video']",
            "//div[@aria-label='Foto/Video']",
            "//img[contains(@src, 'images/composer/SATP_Aa_square')]/ancestor::div[@role='button']",
        ]

        for icon in photo_icons:
            try:
                loc = page.locator(icon).first
                if await loc.is_visible():
                    async with page.expect_file_chooser(timeout=5000) as fc_info:
                        await loc.click()
                    chooser = await fc_info.value
                    await chooser.set_files(image_paths)
                    print("\t[+] Upload via photo icon.")
                    await asyncio.sleep(random.uniform(10, 15))
                    return
            except Exception:
                continue

        try:
            await page.locator(
                "div[role='dialog'] input[type='file']"
            ).first.set_input_files(image_paths)
            print("\t[+] Upload via file input inject.")
            await asyncio.sleep(random.uniform(10, 15))
        except Exception:
            print("\t[-] Image upload failed.")

    async def _click_post(self, page: Page) -> bool:
        print("\t[*] Clicking Post...")
        post_buttons = [
            "//div[@role='dialog']//div[@aria-label='Posting']",
            "//div[@role='dialog']//div[@aria-label='Post']",
            "//div[@role='dialog']//div[@aria-label='Kirim']",
            "//div[@role='dialog']//span[text()='Kirim']",
            "//div[@role='dialog']//span[text()='Post']",
        ]
        for btn in post_buttons:
            try:
                loc = page.locator(btn).first
                if await loc.is_visible():
                    await loc.click()
                    return True
            except Exception:
                continue

        try:
            await page.locator(
                "div[role='dialog'] div[role='button'][tabindex='0']"
            ).last.click()
            return True
        except Exception:
            return False


async def async_main() -> None:
    accounts_path = SCRIPT_DIR / ACCOUNTS_FILE
    posts_path = SCRIPT_DIR / POSTS_FILE
    groups_path = SCRIPT_DIR / GROUPS_FILE
    posted_path = SCRIPT_DIR / POSTED_GROUPS_FILE

    for required in (accounts_path, posts_path, groups_path):
        if not required.exists():
            print(f"[-] Missing config file: {required.name}")
            return

    accounts = load_json(accounts_path)
    posts = load_json(posts_path)
    raw_groups = load_json(groups_path)

    if not isinstance(accounts, list) or not accounts:
        print("[-] accounts.json must be a non-empty list.")
        return
    if not isinstance(posts, list) or not posts:
        print("[-] posts.json must be a non-empty list.")
        return

    groups: list[str] = []
    seen: set[str] = set()
    for entry in raw_groups:
        url = normalize_group_url(entry)
        if not url:
            continue
        key = url.rstrip("/").lower()
        if key not in seen:
            seen.add(key)
            groups.append(url)

    if not groups:
        print("[-] No valid groups found in groups.json")
        return

    posted_path.touch(exist_ok=True)
    tracker = PostedGroupsTracker(posted_path)

    print(
        f"[*] Loaded {len(accounts)} account(s), {len(posts)} post variation(s), "
        f"{len(groups)} group(s). Max concurrent: {MAX_CONCURRENT_TABS}"
    )

    bot = FacebookAsyncBot(accounts, posts, groups, tracker)
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\n[!] Stopped by user.")
