"""Fetch World Bank health indicators needed by run_poc_AH.py.

Stores JSON responses under /home/ubuntu/healthcare_tempo_data/wb/.
Idempotent: re-running skips files already present.
"""
import os, json, requests

OUT = "/home/ubuntu/healthcare_tempo_data/wb"
os.makedirs(OUT, exist_ok=True)

INDICATORS = [
    "SH.XPD.CHEX.GD.ZS",   # current health expenditure % GDP
    "SH.XPD.CHEX.PC.CD",   # per capita USD
    "SH.XPD.CHEX.PP.CD",   # per capita PPP
    "SH.XPD.GHED.GD.ZS",   # government health expenditure % GDP
    "SH.XPD.OOPC.CH.ZS",   # out-of-pocket share
    "SP.DYN.LE00.IN",      # life expectancy at birth
    "SP.DYN.LE00.MA.IN",
    "SP.DYN.LE00.FE.IN",
    "SP.DYN.AMRT.MA",      # adult male mortality
    "SP.DYN.AMRT.FE",
    "SH.DYN.NMRT",         # neonatal mortality
]


def main():
    for code in INDICATORS:
        p = os.path.join(OUT, f"{code}.json")
        if os.path.exists(p):
            print(code, "cached")
            continue
        url = (f"https://api.worldbank.org/v2/country/all/indicator/{code}"
               "?format=json&per_page=25000&date=1960:2023")
        d = requests.get(url, timeout=120).json()
        if len(d) >= 2 and d[1]:
            with open(p, "w") as fh:
                json.dump(d[1], fh)
            print(code, "OK", len(d[1]))
        else:
            print(code, "empty")


if __name__ == "__main__":
    main()
