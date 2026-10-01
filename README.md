# ContractCode – Hukuki AI Analiz Botu

Türk hukuk metinlerini analiz eden, mevzuat ve içtihat araştırması yapan AI destekli web uygulaması.

## 🚀 Özellikler

- **Mevzuat Araştırması** — İlgili kanun maddelerini otomatik bulma
- **İçtihat Analizi** — Yargıtay emsal kararları tarama
- **Sentez Raporu** — HTML formatında yapılandırılmış hukuk analizi

## 🛠 Kurulum (Lokal)

```bash
# Sanal ortam oluştur
python -m venv .venv
.venv\Scripts\activate       # Windows
source .venv/bin/activate    # macOS/Linux

# Bağımlılıkları yükle
pip install -r requirements.txt

# .env dosyasını oluştur
cp .env.example .env
# .env dosyasına OPENAI_API_KEY değerini gir

# Uygulamayı başlat
python main.py
```

Uygulama `http://localhost:8000` adresinde açılır.

## ☁️ Render'a Deploy

1. GitHub'a push'la
2. [Render Dashboard](https://dashboard.render.com/) → **New Web Service**
3. Repo'yu bağla
4. Render otomatik olarak `render.yaml` ayarlarını okuyacak
5. **Environment** bölümünden `OPENAI_API_KEY` değerini gir
6. Deploy et!

## 📁 Proje Yapısı

```
├── main.py           # FastAPI backend + CrewAI agents
├── index.html        # Frontend UI
├── script.js         # Frontend JavaScript
├── style.css         # Styles
├── requirements.txt  # Python dependencies
├── render.yaml       # Render deployment config
├── Procfile          # Process start command
├── .env.example      # Environment variable template
└── .gitignore        # Git ignore rules
```

## ⚙️ Ortam Değişkenleri

| Değişken | Açıklama | Varsayılan |
|----------|----------|------------|
| `OPENAI_API_KEY` | OpenAI API anahtarı | — (zorunlu) |
| `ENVIRONMENT` | `development` veya `production` | `production` |
| `PORT` | Sunucu portu | `8000` |
| `ALLOWED_ORIGINS` | CORS izinli origin'ler (virgülle ayır) | `*` |

## 📝 Lisans

MIT
