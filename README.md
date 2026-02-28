
```
# 🤖 Auto Post Facebook Group & X (Twitter) Bot

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Playwright](https://img.shields.io/badge/Playwright-45ba4b?style=for-the-badge&logo=Playwright&logoColor=white)

Script automasi (Bot) yang dibangun menggunakan Python dan Playwright untuk melakukan posting massal ke Grup Facebook dan interaksi otomatis di X (Twitter). Script ini menggunakan metode *Persistent Context* (Profil Browser) dan injeksi sesi via JSON untuk menghindari *checkpoint* atau blokir dari platform.

## ✨ Fitur Utama

**Facebook Auto Post:**
- 🎭 **Multi-Akun Support**: Berpindah antar akun secara otomatis menggunakan file sesi `.json`.
- 🔗 **Smart Link Converter**: Mengubah link grup *mobile/lite* menjadi mode desktop dan memaksa masuk ke tab `/discussion` (Mencegah nyasar ke tab Media/Files).
- 📸 **Image Injector**: Mampu mengupload banyak foto sekaligus langsung melalui *file chooser* resmi Playwright.
- 🛡️ **Anti-Ban/Crash**: Dilengkapi *delay* natural dan penanganan error per-grup (jika satu grup gagal, bot akan lanjut ke grup berikutnya tanpa mati).

**X (Twitter) Automate:**
- 📝 **Auto Post Status**: Memposting tweet beserta gambar secara otomatis.
- ❤️ **Smart Auto Like Feed**: Melakukan *scroll* beranda/tab Following dan menyukai tweet berdasarkan **Filter Bahasa** (Hanya menyukai tweet yang mengandung keyword Melayu/Inggris, mengabaikan iklan).
- 🧠 **Memory System**: Mengingat tweet yang sudah diinteraksi dalam satu sesi untuk mencegah *looping* pada tweet yang sama.

## 🛠️ Persyaratan (Prerequisites)

Pastikan kamu sudah menginstal Python (minimal versi 3.8+). Kemudian instal library yang dibutuhkan:

```bash
pip install playwright
playwright install chromium
```

## 🚀 Cara Penggunaan

1. **Clone Repository ini:**
   **Bash**

   ```
   git clone [https://github.com/ariknih/autopost-facebook-group.git](https://github.com/ariknih/autopost-facebook-group.git)
   cd autopost-facebook-group
   ```
2. **Mode Login (Wajib dilakukan pertama kali):**

   * Buka file `main.py` atau `main_twitter.py`.
   * Ubah variabel `CREATE_SESSION = True`.
   * Jalankan script: `python main.py`.
   * Browser akan terbuka. Silakan login secara manual.
   * Setelah masuk ke beranda, kembali ke terminal/CMD dan tekan `ENTER`. Sesi akan tersimpan menjadi file `.json` (misal: `akun1.json`).
3. **Mode Automasi / Posting:**

   * Ubah kembali variabel `CREATE_SESSION = False`.
   * Pastikan nama file foto (contoh: `foto1.jpg`) dan file json (contoh: `akun1.json`) sudah sesuai di bagian konfigurasi.
   * Untuk Facebook, siapkan link grup di dalam file `groups.json`.
   * Jalankan script: `python main.py`.

## ⚙️ Konfigurasi (`groups.json`)

Contoh format pengisian link target grup Facebook:

**JSON**

```
[
  {"url": "[https://www.facebook.com/groups/123456789/](https://www.facebook.com/groups/123456789/)"},
  {"url": "[https://web.facebook.com/groups/namagrupbebas/](https://web.facebook.com/groups/namagrupbebas/)"}
]
```

## ⚠️ Disclaimer

Gunakan script ini dengan bijak dan tanggung jawab penuh ada pada pengguna. Melakukan *spamming* berlebihan dapat menyebabkan akun media sosial Anda dibatasi atau di-banned secara permanen oleh pihak platform. Berikan *delay* yang wajar antar aktivitas.

---

**Author:** Mochammad Sayyid Ath Thariq

```

```
