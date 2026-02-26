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
    if len(getiriler) < 5:
        return 3
    std = pd.Series(getiriler).std()
    if   std < 0.003: return 1
    elif std < 0.007: return 2
    elif std < 0.015: return 3
    elif std < 0.025: return 4
    else:             return 5

def sinyal(g1h, g1a):
    if g1h is None or g1a is None:
        return "BEKLE"
    puan = sum([g1h > 0, g1a > 0, g1h > g1a / 4])
    if   puan >= 3: return "AL"
    elif puan == 0: return "SAT"
    else:           return "BEKLE"

def main():
    bugun = date.today()
    while bugun.weekday() >= 5:
        bugun -= timedelta(days=1)

    baslangic = bugun - timedelta(days=30)
    print(f"[TEFAS] Çekiliyor: {baslangic} -> {bugun}")

    crawler = Crawler()
    df = crawler.fetch(start=str(baslangic), end=str(bugun))

    if df.empty:
        print("[UYARI] Bos veri.")
        return

    df["date"] = pd.to_datetime(df["date"])
    print("[DEBUG] Kolonlar:", df.columns.tolist())
    print("[DEBUG] Ornek satir:", df.iloc[0].to_dict())
    print(f"[OK] {len(df)} satir, {df['code'].nunique()} fon")

    yil_basi = pd.Timestamp(date(bugun.year, 1, 1))
    fonlar = []

    for kod, grp in df.groupby("code"):
        grp = grp.sort_values("date")
        fiyatlar = grp["price"].dropna().tolist()
        if len(fiyatlar) < 2:
            continue

        try:
            son = float(fiyatlar[-1])
            if son == 0:
                continue
        except:
            continue

        gunluk = []
        for i in range(1, len(fiyatlar)):
            try:
                onceki = float(fiyatlar[i-1])
                simdi  = float(fiyatlar[i])
                if onceki > 0:
                    gunluk.append((simdi - onceki) / onceki)
            except:
                continue

        def getiri(gun):
            try:
                hedef   = pd.Timestamp(bugun - timedelta(days=gun))
                onceki  = grp[grp["date"] <= hedef]
                if onceki.empty:
                    return None
                eski = float(onceki.iloc[-1]["price"])
                if eski == 0:
                    return None
                return round((son - eski) / eski * 100, 2)
            except:
                return None

        g_ytd = None
        try:
            ytd = grp[grp["date"] >= yil_basi]
            if not ytd.empty:
                eski_ytd = float(ytd.iloc[0]["price"])
                if eski_ytd > 0:
                    g_ytd = round((son - eski_ytd) / eski_ytd * 100, 2)
        except:
            pass

        s   = grp.iloc[-1]
        g1h = getiri(7)
        g1a = getiri(30)

        fonlar.append({
            "kod":        kod,
            "isim":       str(s.get("title", kod)),
            "kategori":   kategori_cevir(s.get("type", "")),
            "fiyat":      round(son, 6),
            "getiri_1h":  g1h,
            "getiri_1a":  g1a,
            "getiri_3a":  None,
            "getiri_ytd": g_ytd,
            "risk":       risk_skoru(gunluk),
            "sinyal":     sinyal(g1h, g1a),
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

    print(f"[TAMAM] {len(fonlar)} fon kaydedildi.")

if __name__ == "__main__":
    main()
