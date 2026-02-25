"""
TEFAS Fon Veri Çekici
======================
GitHub Actions tarafından her gün çalıştırılır.
Çıktı: data/funds.json

Yerel test için:
    pip install tefas-crawler pandas
    python scripts/fetch_funds.py
"""

import json
import os
from datetime import date, timedelta

import pandas as pd
from tefas import Crawler

ROOT   = os.path.join(os.path.dirname(__file__), "..")
OUTPUT = os.path.join(ROOT, "data", "funds.json")
os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)

KATEGORI = {
    "Hisse Senedi Fonu":          "Hisse",
    "Yabancı Hisse Senedi Fonu":  "Hisse (Yab.)",
    "Karma Fon":                  "Karma",
    "Değişken Fon":               "Değişken",
    "Borçlanma Araçları Fonu":    "Tahvil/Bono",
    "Para Piyasası Fonu":         "Para Piyasası",
    "Kıymetli Madenler Fonu":     "Altın",
    "Emtia Fonu":                 "Emtia",
    "Endeks Fonu":                "Endeks",
    "Fon Sepeti Fonu":            "Fon Sepeti",
    "Borsa Yatırım Fonu":         "BYF/ETF",
}

def kategori_cevir(raw):
    for k, v in KATEGORI.items():
        if k.lower() in str(raw).lower():
            return v
    return "Diğer"

def risk_skoru(getiriler):
    """Standart sapma → 1-5 arası risk dilimi"""
    if len(getiriler) < 5:
        return 3
    std = pd.Series(getiriler).std()
    if   std < 0.003: return 1
    elif std < 0.007: return 2
    elif std < 0.015: return 3
    elif std < 0.025: return 4
    else:             return 5

def sinyal(g1h, g1a, g3a):
    """Basit momentum sinyali: AL / SAT / BEKLE"""
    if any(x is None for x in [g1h, g1a, g3a]):
        return "BEKLE"
    puan = sum([
        g1h > 0,
        g1a > 0,
        g3a > 0,
        g1a > 0 and g1h > g1a / 4,
        g3a > 0 and g1a > g3a / 3,
    ])
    if   puan >= 4: return "AL"
    elif puan <= 1: return "SAT"
    else:           return "BEKLE"

def main():
    bugun = date.today()
    while bugun.weekday() >= 5:
        bugun -= timedelta(days=1)

    baslangic = bugun - timedelta(days=90)
    print(f"[TEFAS] Çekiliyor: {baslangic} → {bugun}")

    crawler = Crawler()
    df = crawler.fetch(start=str(baslangic), end=str(bugun))

    if df.empty:
        print("[UYARI] Boş veri.")
        return

    print(f"[TEFAS] {len(df)} satır, {df['code'].nunique()} fon")

    fonlar = []
    for kod, grp in df.groupby("code"):
        grp = grp.sort_values("date")
        fiyatlar = grp["price"].dropna().tolist()
        if len(fiyatlar) < 2:
            continue

        gunluk = [(fiyatlar[i]-fiyatlar[i-1])/fiyatlar[i-1] for i in range(1, len(fiyatlar))]
        son = fiyatlar[-1]

        def g(gun):
            hedef = bugun - timedelta(days=gun)
            onceki = grp[grp["date"] <= str(hedef)]
            if onceki.empty: return None
            eski = onceki.iloc[-1]["price"]
            return round((son - eski) / eski * 100, 2) if eski else None

        g_ytd = None
        ytd = grp[grp["date"] >= str(date(bugun.year, 1, 1))]
        if not ytd.empty and ytd.iloc[0]["price"]:
            g_ytd = round((son - ytd.iloc[0]["price"]) / ytd.iloc[0]["price"] * 100, 2)

        s = grp.iloc[-1]
        g1h, g1a, g3a = g(7), g(30), g(90)

        fonlar.append({
            "kod":        kod,
            "isim":       s.get("title", kod),
            "kategori":   kategori_cevir(s.get("type", "")),
            "fiyat":      round(son, 6),
            "getiri_1h":  g1h,
            "getiri_1a":  g1a,
            "getiri_3a":  g3a,
            "getiri_ytd": g_ytd,
            "risk":       risk_skoru(gunluk),
            "sinyal":     sinyal(g1h, g1a, g3a),
            "yatirimci":  int(s.get("number_of_investors", 0) or 0),
            "portfoy_tl": round(float(s.get("total_value", 0) or 0), 0),
        })

    cikti = {
        "guncelleme": str(bugun),
        "fon_sayisi": len(fonlar),
        "fonlar": sorted(fonlar, key=lambda x: x["getiri_1a"] or -999, reverse=True)
    }

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(cikti, f, ensure_ascii=False, indent=2)

    print(f"[TAMAM] {len(fonlar)} fon kaydedildi → {OUTPUT}")

if __name__ == "__main__":
    main()
