import time
import os
import random
from playwright.sync_api import sync_playwright
from datetime import datetime

# ================= KONFIGURASI =================
ACCOUNTS_LIST = ["akun1.json"] 

# KONTEN POSTING SENDIRI (JANGAN DIUBAH)
PHOTOS = ["foto1.jpg", "foto2.jpg"] 
POST_TEXT = f"""
---
"""

# SETTING LIMIT
LIMIT_LIKES = 30           # Target like per sesi
SCROLL_LIMIT = 50          # Batas scroll biar gak error

# FILTER BAHASA (MALAY & ENGLISH KEYWORDS)
TARGET_KEYWORDS = [
    # Malay / Slang
    "aku", "tak", "nak", "je", "ni", "tu", "ada", "ke", "kan", "lah", "sya", 
    "awak", "kite", "korang", "diorang", "boleh", "kena", "dah", "tapi", 
    "sebab", "memang", "pasal", "siapa", "bila", "kene", "pula", "pulak",
    "kasi", "bagi", "buat", "tahu", "tau", "malaysia", "kl", "jb",
    
    # English
    "the", "is", "are", "you", "me", "my", "your", "we", "they", "it", 
    "this", "that", "have", "has", "will", "can", "do", "don't", "dont",
    "good", "bad", "time", "day", "night", "ready", 
]
# ===============================================

class TwitterBot:
    def __init__(self):
        print("[*] Memulai System...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=False,
            channel="chrome",
            args=['--start-maximized', '--disable-notifications']
        )

    def close(self):
        print("[*] Menutup browser...")
        self.browser.close()
        self.playwright.stop()

    def run(self):
        for account in ACCOUNTS_LIST:
            self.run_account(account)
        self.close()

    def run_account(self, account_file):
        print(f"\n🚀 MEMPROSES AKUN: {account_file}")
        
        if not os.path.exists(account_file):
            print(f"[-] File {account_file} tidak ditemukan. Skip.")
            return

        try:
            context = self.browser.new_context(
                storage_state=account_file,
                no_viewport=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        except Exception as e:
            print(f"[-] Gagal load session: {e}")
            return

        page = context.new_page()

        print("[*] Membuka X.com...")
        try:
            page.goto("https://x.com/home", timeout=60000)
            time.sleep(5)
        except:
            print("[-] Timeout loading beranda.")
            context.close()
            return

        if page.locator("input[autocomplete='username']").count() > 0:
            print("❌ COOKIE MATI. Harap login ulang.")
            context.close()
            return

        # 1. POSTING STATUS SENDIRI
        self.post_new_tweet(page, PHOTOS)

        # 2. AUTO LIKE FEED (Tab Following + Filter Bahasa)
        self.auto_like_feed(page)

        print(f"[*] Selesai akun {account_file}")
        context.close()

    def post_new_tweet(self, page, photos):
        print("\n📝 MENUJU POSTING TWEET SENDIRI...")
        
        composer_found = False
        try:
            input_area = page.locator("div.public-DraftStyleDefault-block").first
            if input_area.is_visible():
                input_area.click()
                composer_found = True
        except: pass

        if not composer_found:
            try:
                page.locator("a[href='/compose/tweet']").click()
                time.sleep(2)
                composer_found = True
            except: 
                print("\t[-] Gagal menemukan kotak tulis.")
                return

        time.sleep(2)
        try: page.keyboard.type(POST_TEXT, delay=50)
        except: pass

        if photos:
            valid_photos = [os.path.abspath(p) for p in photos if os.path.exists(p)]
            if valid_photos:
                print(f"\t[*] Upload {len(valid_photos)} foto...")
                try:
                    media_btn = page.locator("div[aria-label='Add photos or video']").first
                    with page.expect_file_chooser() as fc_info:
                        media_btn.click()
                    fc_info.value.set_files(valid_photos)
                    time.sleep(5) 
                except: print("\t[-] Gagal upload.")

        try:
            post_btn = page.locator("button[data-testid='tweetButtonInline']").first
            if not post_btn.is_visible():
                post_btn = page.locator("button[data-testid='tweetButton']").first
            
            if post_btn.is_enabled():
                post_btn.click()
                print("\t[+] SUKSES POSTING STATUS!")
                time.sleep(5)
            else:
                print("\t[-] Tombol Post belum aktif.")
        except: pass

    def is_target_language(self, text):
        """Cek apakah teks mengandung kata Melayu/Inggris"""
        text_lower = text.lower()
        for word in TARGET_KEYWORDS:
            if f" {word} " in f" {text_lower} ": 
                return True
        return False

    def auto_like_feed(self, page):
        print("\n❤️ MEMULAI AUTO LIKE FEED (MELAYU/INGGRIS)...")
        
        # Refresh home
        if "home" not in page.url: page.goto("https://x.com/home")
        else: page.reload()
        time.sleep(5)

        # === FIX: PINDAH KE TAB 'FOLLOWING' / 'MENGIKUTI' ===
        # Biar gak kejebak algoritma foto doang
        print("\t[*] Mencoba pindah ke tab 'Following'...")
        try:
            # Cari tab kedua di header (biasanya Following/Mengikuti)
            tabs = page.locator("div[role='tablist'] > div[role='presentation']")
            if tabs.count() >= 2:
                following_tab = tabs.nth(1) # Index 1 = Tab Kedua
                following_tab.click()
                print("\t[+] Berhasil pindah tab.")
                time.sleep(4)
            else:
                print("\t[!] Tab tidak ditemukan, lanjut di For You.")
        except:
            print("\t[!] Gagal pindah tab, lanjut default.")

        processed_ids = [] 
        likes_count = 0
        scroll_attempts = 0

        while likes_count < LIMIT_LIKES and scroll_attempts < SCROLL_LIMIT:
            
            # Ambil semua tweet di layar
            tweets = page.locator("article[data-testid='tweet']").all()
            new_tweets_found = False

            for tweet in tweets:
                if likes_count >= LIMIT_LIKES: break

                try:
                    # Ambil Text Tweet
                    txt_element = tweet.locator("div[data-testid='tweetText']")
                    if txt_element.count() == 0: continue # Skip kalau cuma gambar
                    
                    tweet_text = txt_element.first.inner_text()
                    
                    # Filter Iklan
                    if "Promoted" in tweet.inner_text() or "Iklan" in tweet.inner_text():
                        continue

                    # Memory Check
                    tweet_id = tweet_text[:20].replace('\n', '')
                    if tweet_id in processed_ids: continue
                    
                    processed_ids.append(tweet_id)
                    new_tweets_found = True

                    # === CEK BAHASA ===
                    if self.is_target_language(tweet_text):
                        like_btn = tweet.locator("button[data-testid='like']").first
                        unlike_btn = tweet.locator("button[data-testid='unlike']").first
                        
                        if unlike_btn.is_visible():
                            # print(f"\t[SKIP] Sudah like: {tweet_id}...")
                            continue

                        if like_btn.is_visible():
                            tweet.scroll_into_view_if_needed()
                            time.sleep(1)
                            
                            like_btn.click()
                            likes_count += 1
                            print(f"\t[+] LIKED #{likes_count}: {tweet_text[:40].replace('\n', ' ')}...")
                            time.sleep(random.uniform(2, 5)) 
                    else:
                        pass # Bahasa tidak cocok

                except Exception as e:
                    continue
            
            # Scroll Down
            print("\t[*] Scrolling...")
            page.mouse.wheel(0, 800)
            time.sleep(3)
            scroll_attempts += 1
            
            if not new_tweets_found:
                page.mouse.wheel(0, 1500)
                time.sleep(2)

        print(f"\n[*] Selesai. Total Like: {likes_count}")

if __name__ == "__main__":
    bot = TwitterBot()
    bot.run()