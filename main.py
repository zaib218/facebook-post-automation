import json
import time
import os
import re
from playwright.sync_api import sync_playwright
from datetime import datetime
import random

# ================= KONFIGURASI =================
CREATE_SESSION = False
ACCOUNTS_LIST = ["akun1.json", #"akun2.json"
] 
GROUPS_FILE = "groups.json"
IMAGE_FILENAMES = ["foto1.jpg", "foto2.jpg"] 

now = datetime.now()
POST_CONTENT = f"""
NAK CAIRKAN LIMIT?
JANGAN TERTIPU CAJ MURAH&GAMBAR AWEK 🤓

wasap.my/601169821094/Nakcashout

Openn Cashout Limit Apps!!🥰🥰
✓🔴BOOST PAYFLEX
✓🔵RYT PAYLATERR. 
✓🟠SHOPEE SPAYLATER
✓🟡AHAPAY PAYLATER
✓⚫ATOME PAYLATER/CC
✓🟢GRAB PAYLATER

ALWAYS ON SERVICE INSTANT 

#spaylater #boostpayflex
#rytpaylater #shopeepaylater
#ahapay #grabpay #grabpaylater
#atome
(Jam: {now.strftime("%H:%M:%S")})
"""
# ===============================================
# Tambahan konfigurasi
LOOP_POSTING = True                # Jika True, akan ulang terus setelah menyelesaikan semua grup
BATCH_DELAY_SECONDS = 120         # Jeda setelah selesai semua grup (default 2 menit)
PER_POST_DELAY_RANGE = (10, 25)   # Jeda acak antar post per grup (detik)
AUTO_ADD_GROUPS = True            # Jika True, ambil grup dari halaman akun dan tambahkan ke groups.json
SUGGESTED_SAFE_MINUTES = 15      # Rekomendasi aman (estimasi), gunakan 15-30 menit untuk mengurangi risiko
# ===============================================

class FacebookGroupSpam:
    def __init__(self) -> None:
        print("[*] Memulai Playwright...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=False, 
            channel='chrome', 
            args=['--start-maximized', '--disable-notifications']
        )

    def close(self):
        print("[*] Menutup browser...")
        self.browser.close()
        self.playwright.stop()

    def run(self):
        if CREATE_SESSION:
            self.create_new_session()
        else:
            self.run_batch_posting()
        self.close()

    def create_new_session(self):
        context = self.browser.new_context(
            no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto("https://web.facebook.com")
        
        print("\n" + "="*50)
        print("INSTRUKSI: Login manual -> Sampai masuk BERANDA.")
        filename = input("Masukkan nama file (cth: akun1.json): ")
        if not filename.endswith(".json"): filename += ".json"
        input("Tekan ENTER jika sudah login...")
        
        with open(filename, "w") as f:
            json.dump(context.cookies(), f)
        print(f"[+] Cookie disimpan: {filename}")
        context.close()

    def run_batch_posting(self):
        if not os.path.exists(GROUPS_FILE):
            print("[-] File groups.json tidak ditemukan!")
            return

        with open(GROUPS_FILE, 'r') as f:
            groups = json.load(f)

        # Cek Foto
        valid_image_paths = []
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if IMAGE_FILENAMES:
            for img in IMAGE_FILENAMES:
                full_path = os.path.join(script_dir, img)
                if os.path.exists(full_path):
                    valid_image_paths.append(full_path)

        # Looping batch: ulang terus jika LOOP_POSTING True
        try:
            while True:
                for account_file in ACCOUNTS_LIST:
                    print(f"\n🚀 AKUN: {account_file}")
                    if not os.path.exists(account_file):
                        print(f"[-] File cookie tidak ditemukan: {account_file}")
                        continue

                    context = self.browser.new_context(
                        no_viewport=True,
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )

                    try:
                        with open(account_file, "r") as f:
                            context.add_cookies(json.load(f))

                        page = context.new_page()

                        try:
                            page.goto("https://web.facebook.com", timeout=60000)
                            time.sleep(5)
                        except:
                            print("[-] Gagal memuat beranda. Skip akun.")
                            context.close()
                            continue

                        # Auto-add groups dari akun ini bila diaktifkan
                        if AUTO_ADD_GROUPS:
                            try:
                                added = self.add_groups_from_account(page, groups)
                                if added:
                                    with open(GROUPS_FILE, 'w') as gf:
                                        json.dump(groups, gf, indent=2)
                                    print(f"[+] Ditambahkan {added} grup ke {GROUPS_FILE}")
                            except Exception as e:
                                print(f"[-] Gagal auto-add grup: {e}")

                        if page.locator("input[name='email']").count() > 0:
                            print("❌ COOKIE MATI. Harap login ulang.")
                            context.close()
                            break

                        self.post_to_groups(page, groups, valid_image_paths)

                    except Exception as e:
                        print(f"[-] Error Akun Fatal: {e}")
                    finally:
                        try:
                            context.close()
                        except:
                            pass

                    # jika tidak ingin loop terus, hentikan setelah 1 kali
                    if not LOOP_POSTING:
                        print('[*] Selesai satu kali run (LOOP_POSTING=False).')
                        return

                    # antar akun jeda singkat agar tidak langsung melompat
                    wait_short = random.uniform(5, 12)
                    print(f"[*] Menunggu {wait_short:.1f}s sebelum akun berikutnya...")
                    time.sleep(wait_short)

                # selesai untuk semua akun dalam satu putaran
                if LOOP_POSTING:
                    print(f"[*] Selesai semua akun. Menunggu {BATCH_DELAY_SECONDS}s sebelum putaran berikutnya...")
                    time.sleep(BATCH_DELAY_SECONDS)
                else:
                    break
        except KeyboardInterrupt:
            print('\n[!] Dihentikan oleh pengguna (KeyboardInterrupt).')
            return

    def post_to_groups(self, page, groups, image_paths_list):
        for group in groups:
            raw_url = group.get('username', group.get('url', ''))

            # AMBIL ID SAJA (TANPA /DISCUSSION)
            group_id = ""
            match = re.search(r'groups\/([A-Za-z0-9\._-]+)', raw_url)

            if match:
                group_id = match.group(1)
            elif "facebook.com" not in raw_url:
                group_id = raw_url

            if not group_id:
                print(f"[-] Link tidak valid: {raw_url}")
                continue

            # URL POLOS (User Request)
            target_url = f"https://web.facebook.com/groups/{group_id}/"

            print(f"\n[*] Membuka: {target_url}")
            try:
                page.goto(target_url, timeout=60000)
                time.sleep(8)

                if page.locator("//div[@aria-label='Gabung ke grup' or @aria-label='Join group']").count() > 0:
                    print("\t⚠️ SKIP: Belum gabung grup.")
                    continue

                box_found = False

                # JURUS 1: Shortcut P
                try:
                    page.locator("body").click()
                    page.keyboard.press("p")
                    time.sleep(3)
                    if page.locator("div[role='dialog']").count() > 0:
                        box_found = False
                        print("\t[+] Kotak tulis terbuka (Shortcut P)")
                except:
                    pass

                # JURUS 2: Manual Search
                if not box_found:
                    selectors = [
                        "//span[contains(text(), 'Tulis sesuatu...')]",
                        "//span[contains(text(), 'Write something...')]",
                        "//span[contains(text(), 'Jual Sesuatu')]",
                        "//span[contains(text(), 'Apa yang Anda jual')]",
                        "//div[contains(@class, 'x1i10hfl') and contains(text(), 'Tulis sesuatu...')]"
                    ]
                    for sel in selectors:
                        try:
                            if page.locator(sel).count() > 0:
                                page.locator(sel).first.click()
                                box_found = True
                                break
                        except:
                            continue

                if not box_found:
                    print(f"\t[-] Gagal buka kotak tulis.")
                    continue

                # ISI KONTEN
                time.sleep(2)
                try:
                    page.locator("div[role='dialog'] div[contenteditable='true']").first.click()
                    page.keyboard.type(POST_CONTENT)
                except:
                    page.keyboard.type(POST_CONTENT)

                # ==================================================
                # PERBAIKAN LOGIKA UPLOAD FOTO (V4)
                # ==================================================
                if image_paths_list:
                    print(f"\t[*] Upload {len(image_paths_list)} foto...")
                    upload_success = False

                    # CARA 1: KLIK IKON FOTO (Paling Stabil)
                    photo_icons = [
                        "//div[@aria-label='Foto/video']",
                        "//div[@aria-label='Photo/Video']",
                        "//div[@aria-label='Foto/Video']",
                        "//img[contains(@src, 'images/composer/SATP_Aa_square')]/ancestor::div[@role='button']"
                    ]

                    for icon in photo_icons:
                        try:
                            if page.locator(icon).first.is_visible():
                                with page.expect_file_chooser(timeout=5000) as fc_info:
                                    page.locator(icon).first.click()
                                file_chooser = fc_info.value
                                file_chooser.set_files(image_paths_list)
                                upload_success = True
                                print("\t[+] Upload via Klik Ikon Sukses.")
                                time.sleep(15)
                                break
                        except:
                            continue

                    # CARA 2: INJECT INPUT (Fallback)
                    if not upload_success:
                        print("\t[*] Mencoba inject input dalam dialog...")
                        try:
                            page.locator("div[role='dialog'] input[type='file']").first.set_input_files(image_paths_list)
                            upload_success = True
                            print("\t[+] Upload via Inject Sukses.")
                            time.sleep(15)
                        except:
                            print("\t[-] Gagal total upload foto.")
                # ==================================================

                # KIRIM
                print("\t[*] Mengirim...")
                clicked = False
                post_buttons = [
                    "//div[@role='dialog']//div[@aria-label='Posting']",
                    "//div[@role='dialog']//div[@aria-label='Post']",
                    "//div[@role='dialog']//div[@aria-label='Kirim']",
                    "//div[@role='dialog']//span[text()='Kirim']",
                    "//div[@role='dialog']//span[text()='Post']"
                ]

                for btn in post_buttons:
                    try:
                        if page.locator(btn).first.is_visible():
                            page.locator(btn).first.click()
                            clicked = True
                            print("\t[+] Terkirim.")
                            break
                    except:
                        continue

                if not clicked:
                    try:
                        page.locator("div[role='dialog'] div[role='button'][tabindex='0']").last.click()
                        clicked = True
                        print("\t[+] Terkirim (Paksa).")
                    except:
                        print("\t[-] Gagal klik kirim.")

                time.sleep(5)
                # Jeda kecil antar post agar lebih natural
                per_post_delay = random.uniform(*PER_POST_DELAY_RANGE)
                print(f"\t[*] Menunggu {per_post_delay:.1f}s sebelum grup berikutnya...")
                time.sleep(per_post_delay)

            except Exception as e:
                print(f"\t[-] Error pada grup ini: {e}")
                continue

    def add_groups_from_account(self, page, groups_list):
        """Kunjungi halaman grup akun dan ekstrak group IDs numerik lalu tambahkan ke groups_list."""
        print("\t[*] Mengumpulkan grup dari akun (halaman Groups)...")
        try:
            page.goto("https://web.facebook.com/groups", timeout=60000)
            time.sleep(5)
        except:
            # lanjutkan walau gagal goto
            time.sleep(2)

        html = page.content()
        found = set()
        try:
            # cari pola facebook.com/groups/123456 atau /groups/123456
            found.update(re.findall(r'facebook\.com/groups/(\d+)', html))
            found.update(re.findall(r'/groups/(\d+)[/\"\']', html))
        except Exception:
            pass

        # dedup dan bandingkan dengan yang sudah ada
        existing = {str(g.get('username', '')) for g in groups_list}
        added = 0
        for gid in found:
            if gid and gid not in existing:
                groups_list.append({"name": gid, "username": gid, "status": "straight"})
                existing.add(gid)
                added += 1

        return added
        

if __name__ == "__main__":
    FacebookGroupSpam().run()