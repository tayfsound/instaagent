# ⚡ InstaAgent — Instagram AI Otomatik Yanıt Sistemi

Python/FastAPI + Claude AI + Supabase + Render ile çalışan, tamamen ücretsiz Instagram otomatik yanıt sistemi.

---

## 🏗️ Sistem Mimarisi

```
Instagram Kullanıcısı
        │
        ▼
  [Meta Webhook]  ──POST──▶  [Render — FastAPI Sunucu]
                                      │
                          ┌───────────┼───────────┐
                          ▼           ▼           ▼
                    [Supabase]   [Claude AI]  [Instagram
                    PostgreSQL   Yanıt Üret   Graph API]
                          │                       ▲
                          ▼                       │
                   [Dashboard]  ──Onayla──────────┘
                   (Sen buradan
                    görürsün)
```

---

## 🚀 Kurulum (Adım Adım)

### Adım 1 — Supabase (Veritabanı)

1. [supabase.com](https://supabase.com) → **New Project** oluştur
2. **Settings → Database → Connection String → URI** kısmını kopyala
3. Bu string `DATABASE_URL` olarak kullanılacak

### Adım 2 — Meta Developer Console (Instagram API)

1. [developers.facebook.com](https://developers.facebook.com) → **My Apps → Create App**
2. **Instagram** tipini seç
3. **Instagram Basic Display API** ve **Instagram Messaging** ekle
4. **Access Token** al → `INSTAGRAM_ACCESS_TOKEN`
5. **Page ID** al → `INSTAGRAM_PAGE_ID`
6. Webhook URL'yi şimdilik boş bırak (Adım 4'te dolduracağız)

### Adım 3 — Anthropic API Key

1. [console.anthropic.com](https://console.anthropic.com) → **API Keys → Create Key**
2. `ANTHROPIC_API_KEY` olarak kaydet

### Adım 4 — GitHub'a Push

```bash
git init
git add .
git commit -m "Initial InstaAgent setup"
# GitHub'da yeni repo oluştur, sonra:
git remote add origin https://github.com/KULLANICI/instaagent.git
git push -u origin main
```

### Adım 5 — Render'a Deploy

1. [render.com](https://render.com) → **New → Web Service**
2. GitHub reponuzu bağlayın
3. **Environment Variables** kısmına `.env.example`'daki tüm değerleri girin:

| Key | Değer |
|-----|-------|
| `INSTAGRAM_VERIFY_TOKEN` | Kendin belirle (örn: `benim-token-abc123`) |
| `INSTAGRAM_ACCESS_TOKEN` | Meta'dan aldığın token |
| `INSTAGRAM_PAGE_ID` | Instagram page ID |
| `ANTHROPIC_API_KEY` | Anthropic'ten aldığın key |
| `DATABASE_URL` | Supabase connection string |
| `DASHBOARD_PASSWORD` | Güçlü bir şifre belirle |
| `SECRET_KEY` | Rastgele uzun bir string |

4. **Deploy** başladıktan sonra URL'ni al: `https://instaagent-xxxx.onrender.com`

### Adım 6 — Webhook'u Meta'ya Tanıt

Meta Developer Console → **Webhooks → Add Webhook:**
- **Callback URL:** `https://instaagent-xxxx.onrender.com/webhook/instagram`
- **Verify Token:** Adım 5'te girdiğin `INSTAGRAM_VERIFY_TOKEN`
- **Subscribe:** `messages`, `comments`, `story_insights` seç

### Adım 7 — Bilgi Tabanını Yükle

```bash
# Lokal .env dosyanı hazırla
cp .env.example .env
# Değerleri doldur, sonra:

pip install -r requirements.txt
python seed_knowledge.py
```

`knowledge_base/` klasörüne kendi ürün/SSS dosyalarını `.txt` veya `.md` olarak ekle.

---

## 📊 Dashboard'a Erişim

Dashboard API'ye doğrudan erişmek için:

```
https://instaagent-xxxx.onrender.com/docs
```

Buradan tüm endpoint'leri test edebilirsin (Swagger UI).

**Login:**
```bash
curl -X POST https://instaagent-xxxx.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"sifren"}'
```

Token'ı alıp diğer isteklerde `Authorization: Bearer TOKEN` olarak kullan.

---

## 📁 Proje Yapısı

```
instaagent/
├── app/
│   ├── main.py              # FastAPI uygulaması
│   ├── config.py            # Env değişkenleri
│   ├── database.py          # PostgreSQL bağlantısı
│   ├── models.py            # Pydantic şemaları
│   ├── routers/
│   │   ├── webhook.py       # /webhook/instagram — Meta'dan gelen olaylar
│   │   ├── messages.py      # /api/messages — Dashboard API
│   │   ├── auth.py          # /api/auth — JWT girişi
│   │   └── knowledge.py     # /api/knowledge — Bilgi tabanı yönetimi
│   └── services/
│       ├── ai_service.py    # Claude AI entegrasyonu
│       └── instagram_service.py  # Instagram Graph API
├── knowledge_base/
│   └── urunler_sss.txt      # Örnek bilgi tabanı
├── seed_knowledge.py        # KB yükleme scripti
├── requirements.txt
├── render.yaml              # Render deploy konfigürasyonu
├── .env.example             # Örnek env dosyası
└── .gitignore
```

---

## ⚙️ Otomatik Yanıt Mantığı

```
Mesaj Geldi
    │
    ▼
Claude yanıt üretiyor (güven skoru ile)
    │
    ├─ Güven ≥ %90 + needs_human=False
    │       └─▶ OTOMATİK GÖNDER ⚡
    │
    └─ Güven < %90 VEYA needs_human=True
            └─▶ DASHBOARD'A DÜŞER ⏳
                    │
                    ├─ Onayla → Gönder ✅
                    ├─ Düzenle → Gönder ✏️
                    └─ İnsana Yönlendir 🙋
```

---

## 💡 İpuçları

- `knowledge_base/` klasörüne ne kadar detaylı bilgi girersen AI o kadar iyi yanıt üretir
- `AUTO_REPLY_CONFIDENCE_THRESHOLD=0.90` değerini düşürürsen daha fazla otomatik gönderilir
- Şikayet/hakaret içeren mesajlar her zaman insan onayına düşer
- Render ücretsiz planda 15 dk boşta kalınca "uyur", ilk istek ~30 sn gecikebilir
