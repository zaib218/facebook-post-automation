# Twitter Auto-Post & Engagement Bot

Automation bot untuk Twitter (X) dengan fitur:
- **Auto Post**: Post tweet otomatis dengan gambar
- **Auto Like Comment**: Like semua comment di postingan feed secara otomatis
- **Auto Comment**: Comment otomatis dengan text custom
- **Loop Mode**: Ulang terus-menerus dengan jeda yang dapat dikonfigurasi

## Cara Setup

### 1. Persiapan Awal

1. Pastikan Playwright sudah terinstall:
```powershell
pip install playwright
playwright install
```

2. Tempatkan foto-foto Anda di folder ini:
   - `foto1.jpg`
   - `foto2.jpg`
   (Update nama file di `PHOTOS` dalam `main.py` sesuai foto Anda)

### 2. Buat Session (Login Manual)

1. Edit `main.py`, set `CREATE_SESSION = True`
2. Jalankan:
```powershell
python main.py
```
3. Browser akan terbuka, login manual ke Twitter
4. Tunggu sampai Anda masuk ke home feed
5. Tekan ENTER di terminal
6. Cookie akan disimpan ke `akun1.json`

### 3. Jalankan Automation

1. Set `CREATE_SESSION = False` di `main.py`
2. Jalankan:
```powershell
python main.py
```

Untuk menghentikan: Tekan `Ctrl+C`

## Konfigurasi

### POST CONFIGURATION
```python
POST_TEXT = """..."""      # Text yang akan dipost
PHOTOS = ["foto1.jpg", "foto2.jpg"]  # Foto yang diupload (dummy file dulu)
```

### COMMENT CONFIGURATION
```python
COMMENT_TEXT = "Bagus banget! Menarik sekali 👍"  # Text comment otomatis
```

### DELAY CONFIGURATION
```python
BATCH_DELAY_SECONDS = 120           # Jeda antar siklus (detik)
POST_DELAY_RANGE = (15, 30)        # Jeda antar post (detik, random)
LIKE_DELAY_RANGE = (2, 5)          # Jeda antar like (detik, random)
COMMENT_DELAY_RANGE = (3, 8)       # Jeda antar comment (detik, random)
FEED_SCROLL_DELAY_RANGE = (10, 20) # Jeda antar postingan feed
```

### FEATURE FLAGS
```python
AUTO_POST_ENABLED = True            # Aktifkan auto post
AUTO_LIKE_COMMENT_ENABLED = True    # Aktifkan auto like comment
AUTO_COMMENT_ENABLED = True         # Aktifkan auto comment
LOOP_MODE = True                    # Ulang terus jika True
```

## Fitur Detail

### 1. Auto Post
- Membuka composer
- Menulis tweet sesuai `POST_TEXT`
- Upload foto jika ada
- Posting tweet

### 2. Auto Like Comment
- Membuka setiap postingan di feed
- Scroll untuk load semua comment
- Like semua comment yang ditemukan
- Kembali ke feed dengan Escape

### 3. Auto Comment
- Reply ke postingan
- Menulis comment sesuai `COMMENT_TEXT`
- Posting comment

### 4. Loop Mode
- Setelah selesai satu siklus, tunggu `BATCH_DELAY_SECONDS`
- Jalankan lagi dari awal
- Tekan Ctrl+C untuk berhenti

## Keamanan & Rekomendasi

⚠️ **PENTING:**
- Jangan gunakan jeda terlalu cepat (risiko pembatasan akun dari Twitter)
- Rekomendasikan interval minimal:
  - Antar post: 15-30 detik (sudah default)
  - Antar like: 2-5 detik (sudah default)
  - Antar comment: 3-8 detik (sudah default)
  - Antar siklus: 2-5 menit (default 2 menit, bisa dinaikkan)

## Troubleshooting

### Session Expired
- Jika error "SESSION EXPIRED", jalankan create session lagi dengan `CREATE_SESSION = True`

### Foto tidak ditemukan
- Pastikan nama file foto di `PHOTOS` sudah benar
- Pastikan foto ada di folder yang sama dengan `main.py`

### Compose/Reply button tidak ditemukan
- Twitter UI sering berubah, mungkin perlu update selector di kode
- Update `compose_buttons` atau `reply_buttons` sesuai UI terbaru

### Tidak bisa click element
- Tunggu lebih lama dengan menambah `time.sleep()`
- Cek apakah page sudah fully load

## TODO/Development

- [ ] Support multiple accounts sekaligus
- [ ] Database untuk track yang sudah dilike/comment
- [ ] Proxy support
- [ ] Better error handling & retry logic
- [ ] Headless mode option
- [ ] More complex comment templates


still openn yaa realslot/realsex&bj 
dm if interested

.

vcs on

.

private content on

.

tags only jb,kl,shahalam,johor,johorbahru,kluang,petalingjaya,pj,putrajaya,bangi,bangsar,seksyen,kuantan,tganu,terengganu,damansara,georgetown,penang