import json
import os
from datetime import date, timedelta

import pandas as pd
from tefas import Crawler

ROOT   = os.path.join(os.path.dirname(__file__), "..")
OUTPUT = os.path.join(ROOT, "data", "funds.json")
os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)

def kategori_belirle(row):
    try:
        hisse    = float(row.get("stock", 0) or 0) + float(row.get("foreign_equity", 0) or 0)
        altin    = float(row.get("precious_metals", 0) or 0) + \
                   float(row.get("precious_metals_byf", 0) or 0) + \
                   float(row.get("precious_metals_kba", 0) or 0) + \
                   float(row.get("precious_metals_kks", 0) or 0)
        para_piy = float(row.get("repo", 0) or 0) + \
                   float(row.get("reverse_repo", 0) or 0) + \
                   float(row.get("term_deposit", 0) or 0) + \
                   float(row.get("term_deposit_tl", 0) or 0) + \
                   float(row.get("tmm", 0) or 0)
        tahvil   = float(row.get("government_bond", 0) or 0) + \
                   float(row.get("treasury_bill", 0) or 0) + \
                   float(row.get("private_sector_bond", 0) or 0) + \
                   float(row.get("public_domestic_debt_instruments", 0) or 0)
        katilim  = float(row.get("participation_account", 0) or 0) + \
                   float(row.get("participation_account_tl", 0) or 0) + \
                   float(row.get("government_lease_certificates", 0) or 0) + \
                   float(row.get("government_lease_certificates_tl", 0) or 0)
        etf      = float(row.get("exchange_traded_fund", 0) or 0) + \
                   float(row.get("foreign_exchange_traded_funds", 0) or 0)
        fon_sep  = float(row.get("fund_participation_certificate", 0) or 0) + \
                   float(row.get("foreign_investment_fund_participation_shares", 0) or 0)

        skorlar = {
            "Hisse":         hisse,
            "Altin":         altin,
            "Para Piyasasi": para_piy,
            "Tahvil/Bono":   tahvil,
            "Katilim":       katilim,
            "BYF/ETF":       etf,
            "Fon Sepeti":    fon_sep,
        }

        en_buyuk       = max(skorlar, key=skorlar.get)
        en_buyuk_deger = skorlar[en_buyuk]

        if en_buyuk_deger >= 50:
            return en_buyuk
        elif en_buyuk_deger >= 25:
            ikinci = sorted(skorlar, key=skorlar.get, reverse=True)[1]
            if skorlar[ikinci] >= 15:
                return "Karma"
            return en_buyuk
        else:
            return "Degisken"
    except:
        return "Diger"

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
    print(f"[TEFAS] Cekiliyor: {baslangic} -> {bugun}")

    crawler = Crawler()
    df = crawler.fetch(start=str(baslangic), end=str(bugun))

    if df.empty:
        print("[UYARI] Bos veri.")
        return

    df["date"] = pd.to_datetime(df["date"])
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
                eski_f = float(fiyatlar[i-1])
                yeni_f = float(fiyatlar[i])
                if eski_f > 0:
                    gunluk.append((yeni_f - eski_f) / eski_f)
            except:
                continue

        def getiri(gun):
            try:
                hedef  = pd.Timestamp(bugun - timedelta(days=gun))
                onceki = grp[grp["date"] <= hedef]
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

        son_satir = grp.iloc[-1]
        onceki_gun = grp.iloc[-2] if len(grp) >= 2 else None

        # Gunluk degisim
        gunluk_degisim = None
        try:
            if onceki_gun is not None:
                eski_fiyat = float(onceki_gun["price"])
                if eski_fiyat > 0:
                    gunluk_degisim = round((son - eski_fiyat) / eski_fiyat * 100, 2)
        except:
            pass

        g1h = getiri(7)
        g1a = getiri(30)

        fonlar.append({
            "kod":             kod,
            "isim":            str(son_satir.get("title", kod)),
            "kategori":        kategori_belirle(son_satir),
            "fiyat":           round(son, 4),
            "gunluk_degisim":  gunluk_degisim,
            "getiri_1h":       g1h,
            "getiri_1a":       g1a,
            "getiri_3a":       None,
            "getiri_ytd":      g_ytd,
            "risk":            risk_skoru(gunluk),
            "sinyal":          sinyal(g1h, g1a),
            "yatirimci":       int(son_satir.get("number_of_investors", 0) or 0),
            "portfoy_tl":      round(float(son_satir.get("market_cap", 0) or 0), 0),
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
