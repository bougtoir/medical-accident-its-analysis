"""
01_compile_round1_stores.py
Compile Round1 USA store locations with opening years, geocoded to counties/states.

Sources:
 - round1usa.com store IDs (numerical ordering correlates with opening)
 - Round1 Group IR materials (round1-group.co.jp)
 - News articles (arcadeheroes.com, rebusinessonline.com, wbsm.com, etc.)
 - Malls & Retail Wiki (fandom)
"""

import csv
import json
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Round1 USA store data compiled from public sources.
# store_id: internal number from round1usa.com booking URLs
# open_year: confirmed or estimated from news / IR / fandom / store ordering
# Sources noted inline.
ROUND1_USA_STORES = [
    # === CONFIRMED from corporate history / news articles ===
    {"store_id": "001", "code": "PHM", "name": "Puente Hills Mall",
     "city": "City of Industry", "state": "CA", "county": "Los Angeles",
     "open_year": 2010, "source": "Round1 Group corporate history (Aug 2010)"},
    {"store_id": "002", "code": "MVM", "name": "Moreno Valley Mall",
     "city": "Moreno Valley", "state": "CA", "county": "Riverside",
     "open_year": 2012, "source": "Spinoso REG press release (2012)"},
    {"store_id": "003", "code": "LWM", "name": "Lakewood Center Mall",
     "city": "Lakewood", "state": "CA", "county": "Los Angeles",
     "open_year": 2013, "source": "RE Business (existing by Apr 2015); store order"},
    {"store_id": "004", "code": "APM", "name": "Arlington Parks Mall",
     "city": "Arlington", "state": "TX", "county": "Tarrant",
     "open_year": 2014, "source": "Arcade Heroes (Dec 20, 2014)"},
    {"store_id": "005", "code": "NRS", "name": "North Riverside Park Mall",
     "city": "North Riverside", "state": "IL", "county": "Cook",
     "open_year": 2014, "source": "RE Business (existing by Apr 2015); estimated"},

    # === 2015 wave (6 new locations announced Apr 2015) ===
    {"store_id": "006", "code": "MPM", "name": "Main Place Mall",
     "city": "Santa Ana", "state": "CA", "county": "Orange",
     "open_year": 2015, "source": "RE Business (Apr 2015)"},
    {"store_id": "007", "code": "SCM", "name": "Westfield Southcenter",
     "city": "Tukwila", "state": "WA", "county": "King",
     "open_year": 2015, "source": "RE Business (Apr 2015)"},
    {"store_id": "008", "code": "ESC", "name": "Eastridge Shopping Center",
     "city": "San Jose", "state": "CA", "county": "Santa Clara",
     "open_year": 2015, "source": "RE Business (Apr 2015)"},
    {"store_id": "009", "code": "SSM", "name": "Stratford Square Mall",
     "city": "Bloomingdale", "state": "IL", "county": "DuPage",
     "open_year": 2015, "source": "Malls Wiki (opened 2015, closed 2020)"},
    {"store_id": "010", "code": "EXM", "name": "Exton Square Mall",
     "city": "Exton", "state": "PA", "county": "Chester",
     "open_year": 2015, "source": "RE Business (PA location, 2015)"},
    {"store_id": "011", "code": "SVM", "name": "Sunvalley Mall",
     "city": "Concord", "state": "CA", "county": "Contra Costa",
     "open_year": 2015, "source": "Store number / wave estimate"},
    {"store_id": "012", "code": "SCG", "name": "Silver City Galleria",
     "city": "Taunton", "state": "MA", "county": "Bristol",
     "open_year": 2015, "source": "WBSM (Dec 26, 2015)"},

    # === 2016 wave (8 planned from RE Business) ===
    {"store_id": "013", "code": "GVM", "name": "Grapevine Mills",
     "city": "Grapevine", "state": "TX", "county": "Tarrant",
     "open_year": 2016, "source": "Store number estimate"},
    {"store_id": "014", "code": "GLC", "name": "Great Lakes Crossing",
     "city": "Auburn Hills", "state": "MI", "county": "Oakland",
     "open_year": 2016, "source": "Store number estimate"},
    {"store_id": "015", "code": "FSM", "name": "Four Seasons Town Centre",
     "city": "Greensboro", "state": "NC", "county": "Guilford",
     "open_year": 2016, "source": "Store number estimate"},
    {"store_id": "016", "code": "STC", "name": "Shops at South Town",
     "city": "Sandy", "state": "UT", "county": "Salt Lake",
     "open_year": 2016, "source": "Store number estimate"},
    {"store_id": "017", "code": "SWP", "name": "Southwest Plaza",
     "city": "Littleton", "state": "CO", "county": "Jefferson",
     "open_year": 2016, "source": "Store number estimate"},
    {"store_id": "018", "code": "BWM", "name": "Broadway Mall",
     "city": "Hicksville", "state": "NY", "county": "Nassau",
     "open_year": 2016, "source": "Store number estimate"},
    {"store_id": "019", "code": "GLM", "name": "Great Lakes Mall",
     "city": "Mentor", "state": "OH", "county": "Lake",
     "open_year": 2016, "source": "Store number estimate"},
    {"store_id": "020", "code": "CCM", "name": "Coronado Center",
     "city": "Albuquerque", "state": "NM", "county": "Bernalillo",
     "open_year": 2016, "source": "Store number estimate"},

    # === 2017 wave ===
    {"store_id": "021", "code": "FVM", "name": "Fox Valley Mall",
     "city": "Aurora", "state": "IL", "county": "Kane",
     "open_year": 2017, "source": "Malls Wiki (opened 2017)"},
    {"store_id": "022", "code": "MCM", "name": "Millcreek Mall",
     "city": "Erie", "state": "PA", "county": "Erie",
     "open_year": 2017, "source": "Store number estimate"},
    {"store_id": "023", "code": "NWD", "name": "Northwoods Mall",
     "city": "Peoria", "state": "IL", "county": "Peoria",
     "open_year": 2017, "source": "Malls Wiki (Nov 18, 2017)"},
    {"store_id": "024", "code": "FFC", "name": "Fairfield Commons",
     "city": "Beavercreek", "state": "OH", "county": "Greene",
     "open_year": 2017, "source": "Store number estimate"},
    {"store_id": "025", "code": "MEM", "name": "Maine Mall",
     "city": "South Portland", "state": "ME", "county": "Cumberland",
     "open_year": 2017, "source": "Store number estimate"},
    {"store_id": "026", "code": "LAS", "name": "Meadows Mall",
     "city": "Las Vegas", "state": "NV", "county": "Clark",
     "open_year": 2017, "source": "Store number estimate"},
    {"store_id": "027", "code": "RNO", "name": "Meadowood Mall",
     "city": "Reno", "state": "NV", "county": "Washoe",
     "open_year": 2017, "source": "Store number estimate"},
    {"store_id": "028", "code": "GWM", "name": "Gateway Mall",
     "city": "Lincoln", "state": "NE", "county": "Lancaster",
     "open_year": 2017, "source": "Store number estimate"},

    # === 2018 wave ===
    {"store_id": "029", "code": "SRM", "name": "Southridge Mall",
     "city": "Greendale", "state": "WI", "county": "Milwaukee",
     "open_year": 2018, "source": "Store number estimate"},
    {"store_id": "030", "code": "NRM", "name": "Northridge Mall",
     "city": "Salinas", "state": "CA", "county": "Monterey",
     "open_year": 2018, "source": "Store number estimate"},
    {"store_id": "031", "code": "TTC", "name": "Towson Town Center",
     "city": "Towson", "state": "MD", "county": "Baltimore",
     "open_year": 2018, "source": "Store number estimate"},
    {"store_id": "032", "code": "HYM", "name": "Holyoke Mall",
     "city": "Holyoke", "state": "MA", "county": "Hampden",
     "open_year": 2018, "source": "Store number estimate"},
    {"store_id": "033", "code": "SLM", "name": "Southland Mall",
     "city": "Hayward", "state": "CA", "county": "Alameda",
     "open_year": 2018, "source": "Store number estimate"},
    {"store_id": "034", "code": "PPM", "name": "Park Place Mall",
     "city": "Tucson", "state": "AZ", "county": "Pima",
     "open_year": 2018, "source": "Store number estimate"},
    {"store_id": "035", "code": "RVM", "name": "Galleria at Roseville",
     "city": "Roseville", "state": "CA", "county": "Placer",
     "open_year": 2018, "source": "Store number estimate"},
    {"store_id": "036", "code": "VRC", "name": "Valley River Center",
     "city": "Eugene", "state": "OR", "county": "Lane",
     "open_year": 2018, "source": "Store number estimate"},

    # === 2019 wave ===
    {"store_id": "037", "code": "QSM", "name": "Quail Springs Mall",
     "city": "Oklahoma City", "state": "OK", "county": "Oklahoma",
     "open_year": 2019, "source": "Store number estimate"},
    {"store_id": "038", "code": "SHM", "name": "South Hill Mall",
     "city": "Puyallup", "state": "WA", "county": "Pierce",
     "open_year": 2019, "source": "Store number estimate"},
    {"store_id": "039", "code": "VCM", "name": "Vancouver Mall",
     "city": "Vancouver", "state": "WA", "county": "Clark",
     "open_year": 2019, "source": "Store number estimate"},
    {"store_id": "040", "code": "NSM", "name": "North Star Mall",
     "city": "San Antonio", "state": "TX", "county": "Bexar",
     "open_year": 2019, "source": "Store number estimate"},
    {"store_id": "041", "code": "BTC", "name": "Burbank Town Center",
     "city": "Burbank", "state": "CA", "county": "Los Angeles",
     "open_year": 2019, "source": "Store number estimate"},
    {"store_id": "042", "code": "TES", "name": "Town East Square",
     "city": "Wichita", "state": "KS", "county": "Sedgwick",
     "open_year": 2019, "source": "Store number estimate"},
    {"store_id": "043", "code": "DFM", "name": "Deptford Mall",
     "city": "Deptford", "state": "NJ", "county": "Gloucester",
     "open_year": 2019, "source": "Store number estimate"},
    {"store_id": "044", "code": "PCC", "name": "Park City Center",
     "city": "Lancaster", "state": "PA", "county": "Lancaster",
     "open_year": 2019, "source": "Store number estimate"},
    {"store_id": "045", "code": "PMM", "name": "Potomac Mills",
     "city": "Woodbridge", "state": "VA", "county": "Prince William",
     "open_year": 2019, "source": "Store number estimate"},
    {"store_id": "046", "code": "CLM", "name": "Cumberland Mall",
     "city": "Atlanta", "state": "GA", "county": "Cobb",
     "open_year": 2019, "source": "Store number estimate"},
    {"store_id": "047", "code": "PLM", "name": "Pembroke Lakes Mall",
     "city": "Pembroke Pines", "state": "FL", "county": "Broward",
     "open_year": 2019, "source": "Store number estimate"},
    {"store_id": "048", "code": "FDP", "name": "Fashion District Philadelphia",
     "city": "Philadelphia", "state": "PA", "county": "Philadelphia",
     "open_year": 2019, "source": "Store number estimate"},
    {"store_id": "049", "code": "TMP", "name": "Promenade Temecula",
     "city": "Temecula", "state": "CA", "county": "Riverside",
     "open_year": 2019, "source": "Store number estimate"},

    # === 2020-2024 wave (slower due to COVID, then acceleration) ===
    {"store_id": "050", "code": "CRG", "name": "Galleria at Crystal Run",
     "city": "Middletown", "state": "NY", "county": "Orange",
     "open_year": 2021, "source": "Store number estimate (COVID gap)"},
    {"store_id": "051", "code": "WLB", "name": "Willowbrook Mall",
     "city": "Houston", "state": "TX", "county": "Harris",
     "open_year": 2021, "source": "Store number estimate"},
    {"store_id": "052", "code": "DBK", "name": "Deerbrook Mall",
     "city": "Humble", "state": "TX", "county": "Harris",
     "open_year": 2022, "source": "Store number estimate"},
    {"store_id": "053", "code": "ATC", "name": "Arrowhead Towne Center",
     "city": "Glendale", "state": "AZ", "county": "Maricopa",
     "open_year": 2022, "source": "Store number estimate"},
    {"store_id": "054", "code": "JFM", "name": "Jefferson Mall",
     "city": "Louisville", "state": "KY", "county": "Jefferson",
     "open_year": 2022, "source": "Store number estimate"},
    {"store_id": "055", "code": "LVO", "name": "Las Vegas South Premium Outlets",
     "city": "Las Vegas", "state": "NV", "county": "Clark",
     "open_year": 2023, "source": "Store number estimate"},
    {"store_id": "056", "code": "PBO", "name": "Westfield Plaza Bonita",
     "city": "National City", "state": "CA", "county": "San Diego",
     "open_year": 2023, "source": "Store number estimate"},
    {"store_id": "057", "code": "STM", "name": "Mall at Stonecrest",
     "city": "Stonecrest", "state": "GA", "county": "DeKalb",
     "open_year": 2023, "source": "Store number estimate"},
    {"store_id": "058", "code": "MVJ", "name": "Shops at Mission Viejo",
     "city": "Mission Viejo", "state": "CA", "county": "Orange",
     "open_year": 2023, "source": "Store number estimate"},
    {"store_id": "059", "code": "STG", "name": "Stonestown Galleria",
     "city": "San Francisco", "state": "CA", "county": "San Francisco",
     "open_year": 2023, "source": "Store number estimate"},
    {"store_id": "060", "code": "CHF", "name": "Chandler Fashion Center",
     "city": "Chandler", "state": "AZ", "county": "Maricopa",
     "open_year": 2023, "source": "Store number estimate"},
    {"store_id": "061", "code": "DBF", "name": "Danbury Fair",
     "city": "Danbury", "state": "CT", "county": "Fairfield",
     "open_year": 2024, "source": "Round1 IR (Mar 9, 2024)"},
    {"store_id": "062", "code": "GUR", "name": "Gurnee Mills",
     "city": "Gurnee", "state": "IL", "county": "Lake",
     "open_year": 2024, "source": "Malls Wiki (Aug 31, 2024)"},
    {"store_id": "063", "code": "JSG", "name": "Mills at Jersey Gardens",
     "city": "Elizabeth", "state": "NJ", "county": "Union",
     "open_year": 2024, "source": "Store number estimate"},
    {"store_id": "064", "code": "MLP", "name": "Menlo Park Mall",
     "city": "Edison", "state": "NJ", "county": "Middlesex",
     "open_year": 2024, "source": "Store number estimate"},
]


def main():
    out_csv = os.path.join(OUTPUT_DIR, "round1_usa_stores.csv")
    fields = [
        "store_id", "code", "name", "city", "state",
        "county", "open_year", "source",
    ]
    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(ROUND1_USA_STORES)

    out_json = os.path.join(OUTPUT_DIR, "round1_usa_stores.json")
    with open(out_json, "w") as f:
        json.dump(ROUND1_USA_STORES, f, indent=2)

    print(f"Compiled {len(ROUND1_USA_STORES)} Round1 USA stores")
    print(f"  CSV: {out_csv}")
    print(f"  JSON: {out_json}")

    by_year = {}
    for s in ROUND1_USA_STORES:
        by_year.setdefault(s["open_year"], []).append(s["code"])
    print("\nStores by opening year:")
    for yr in sorted(by_year):
        print(f"  {yr}: {len(by_year[yr])} stores — {', '.join(by_year[yr])}")

    by_state = {}
    for s in ROUND1_USA_STORES:
        by_state.setdefault(s["state"], []).append(s)
    print(f"\nStates with Round1: {len(by_state)}")
    for st in sorted(by_state):
        print(f"  {st}: {len(by_state[st])} stores")


if __name__ == "__main__":
    main()
