```

```


<div align="center">

# 🤖 Auto Post Facebook Group & X (Twitter) Bot

**Script automasi tangguh berbasis Python dan Playwright untuk mengelola posting massal dan interaksi media sosial secara otomatis.**

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-2EAD33?style=for-the-badge&logo=Playwright&logoColor=white)](https://playwright.dev/python/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg?style=for-the-badge)](https://github.com/ariknih/autopost-facebook-group/graphs/commit-activity)
[![Author](https://img.shields.io/badge/Author-Arik-blue?style=for-the-badge)](https://github.com/ariknih)

</div>

---

> **💡 Deskripsi Singkat**
> Script ini menggunakan metode *Persistent Context* (Profil Browser) dan *Injeksi Sesi via JSON* untuk mensimulasikan aktivitas manusia secara natural. Hal ini sangat efektif untuk menghindari *checkpoint* atau pemblokiran dari sistem keamanan platform.

<br>

## ✨ Fitur Utama

### 📘 Facebook Auto Post

* 🎭 **Multi-Akun Support**: Berpindah antar akun secara otomatis bergantian menggunakan file sesi `.json`.
* 🔗 **Smart Link Converter**: Mengubah link grup *mobile/lite* menjadi mode *desktop* dan mengunci target ke tab `/discussion` (Mencegah bot nyasar ke tab Media/Files).
* 📸 **Image Injector**: Mampu mengunggah banyak foto sekaligus secara stabil melalui *file chooser* resmi Playwright.
* 🛡️ **Anti-Ban / Auto-Recovery**: Dilengkapi *delay* natural dan penanganan error per-grup. Jika satu grup gagal/dikunci admin, bot akan langsung *skip* dan lanjut ke grup berikutnya tanpa *crash*.

### 🐦 X (Twitter) Automate

* 📝 **Auto Post Status**: Memposting tweet teks beserta gambar secara otomatis.
* ❤️ **Smart Auto Like Feed**: Melakukan *scroll* beranda (opsi tab *Following*) dan menyukai tweet secara selektif berdasarkan **Filter Bahasa** (Hanya menyukai tweet yang mengandung *keyword* Melayu/Inggris, serta otomatis mengabaikan iklan).
* 🧠 **Memory System**: Mengingat ID tweet yang sudah diinteraksi dalam satu sesi untuk mencegah *looping* pada tweet yang sama.

<br>

## 🛠️ Persyaratan Sistem (Prerequisites)

Pastikan kamu sudah menginstal **Python (minimal versi 3.8+)**. Kemudian instal *library* utama yang dibutuhkan melalui terminal/CMD:

```bash
pip install playwright
playwright install chromium
```


## 🚀 Cara Penggunaan

### 1. Clone Repository

Unduh *source code* ini ke komputer kamu:

```
git clone https://github.com/ariknih/autopost-facebook-group.git
```

```
cd autopost-facebook-group
```


### 2. Mode Login (Wajib untuk Setup Awal)

Langkah ini dilakukan sekali saja untuk mengambil *cookie* akun kamu.

1. Buka file `main.py` (untuk FB) atau `main_twitter.py` (untuk X).
2. Ubah variabel menjadi `CREATE_SESSION = True`.
3. Jalankan script:
   ```
   python main.py
   ```


4. Browser akan terbuka.  **Silakan login secara manual** .

5. Setelah berhasil masuk ke Beranda/Feed, kembali ke terminal/CMD dan tekan `ENTER`.

6. Sesi akan tersimpan aman menjadi file `.json` (misal: `akun1.json`).

### 3. Mode Automasi (Posting & Interaksi)

Setelah sesi tersimpan, saatnya bot bekerja:

1. Ubah kembali variabel menjadi `CREATE_SESSION = False`.
2. Pastikan nama file foto (contoh: `foto1.jpg`) dan nama file json (contoh: `akun1.json`) sudah sesuai di bagian konfigurasi atas script.
3. Khusus Facebook: Siapkan link grup target di dalam file `groups.json`.
4. Jalankan script, dan biarkan bot bekerja!

## ⚙️ Konfigurasi Target (`groups.json`)

Untuk automasi Facebook, buat file bernama `groups.json` di folder yang sama, lalu isi dengan format *array of objects* seperti contoh di bawah ini:

```
[
  {"url": "https://www.facebook.com/groups/123456789/"},
  {"url": "https://web.facebook.com/groups/namagrupbebas/"},
  {"url": "19827391823791"}
]
```
