# FonTakip — TEFAS Fon Analiz Dashboard

TEFAS'taki 1000+ fonu analiz eden, günlük otomatik güncellenen, ücretsiz fon takip aracı.

## Özellikler
- Tüm TEFAS fonlarının performans karşılaştırması (1H / 1A / 3A / YBB)
- Kategori filtreleme (Hisse, Altın, Para Piyasası, Karma, Tahvil)
- Volatilite bazlı risk skoru (1-5)
- Momentum bazlı AL / SAT / BEKLE sinyali
- Kişisel izleme listesi (tarayıcıda saklanır)
- Her hafta içi otomatik veri güncelleme (GitHub Actions)

---

## Kurulum (10 dakika)

### 1. GitHub repo oluştur
- github.com'da **"New repository"** tıkla
- İsim: `fontakip` (veya istediğin bir isim)
- **Public** seç (GitHub Pages için şart)
- "Create repository" tıkla

### 2. Bu dosyaları yükle
Tüm dosyaları yeni repoya yükle (sürükle-bırak ya da git push):
```
fontakip/
├── index.html
├── requirements.txt
├── data/
│   └── funds.json          ← örnek veri, ilk Action çalışınca güncellenir
├── scripts/
│   └── fetch_funds.py
└── .github/
    └── workflows/
        └── update-data.yml
```

### 3. GitHub Pages aktifleştir
- Repo → **Settings** → **Pages**
- Source: **Deploy from a branch**
- Branch: **main** / **(root)**
- **Save** tıkla
- Birkaç dakika sonra: `https://KULLANICI_ADIN.github.io/fontakip`

### 4. İlk veriyi çek
- Repo → **Actions** sekmesi
- **"TEFAS Veri Güncelle"** workflow'unu seç
- **"Run workflow"** → **"Run workflow"** tıkla
- ~1-2 dakika bekle, `data/funds.json` güncellenecek

**Bundan sonra her hafta içi 19:00'da otomatik çalışır.**

---

## Dosya Açıklamaları

| Dosya | Açıklama |
|-------|----------|
| `index.html` | Tüm arayüz — tek dosya, sıfır bağımlılık |
| `scripts/fetch_funds.py` | Veri çekme ve hesaplama script'i |
| `.github/workflows/update-data.yml` | Günlük otomatik güncelleme |
| `data/funds.json` | Canlı fon verisi (Actions tarafından güncellenir) |

---

## Geliştirme Yol Haritası

- [ ] Fon detay sayfası (tarihsel grafik)
- [ ] E-posta / Telegram sinyal bildirimleri
- [ ] Portföy simülatörü
- [ ] Premium özellikler için kullanıcı girişi

---

*Veriler tefas.gov.tr'dan çekilmektedir. Yatırım tavsiyesi değildir.*
