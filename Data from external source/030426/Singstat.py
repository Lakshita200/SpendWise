import requests
import time
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

FOOD_TABLE = "M213761"

# ---------------------------
# Helpers
# ---------------------------

def parse_key_date(key):
    key = key.replace(" Numeric","").replace(" Text","").strip()
    for fmt in ["%Y %b", "%b %Y"]:
        try:
            return datetime.strptime(key, fmt)
        except:
            pass
    return None

def get_two_latest(columns):
    dated = []
    for col in columns:
        key = col["key"].replace(" Numeric","").replace(" Text","").strip()
        dt = parse_key_date(key)
        if dt:
            dated.append((dt, key))

    dated.sort()
    if len(dated) >= 2:
        return dated[-2][1], dated[-1][1]
    return None, None

def get_value(row, key):
    if not key:
        return None

    for col in row["columns"]:
        k = col["key"].replace(" Numeric","").replace(" Text","").strip()
        if k == key:
            v = col["value"]
            if v not in (None, "", "-", "na"):
                return str(v)

    return None

def calc_trend(curr, prev):
    try:
        diff = float(curr) - float(prev)
        if diff > 0:
            return f"▲ {diff:.2f}", "📈 Rising"
        elif diff < 0:
            return f"▼ {abs(diff):.2f}", "📉 Falling"
        else:
            return "— 0.00", "➡ Stable"
    except:
        return "N/A", "N/A"

# ---------------------------
# MAIN DASHBOARD
# ---------------------------

def show_cpi_dashboard():
    print("\n⏳ Fetching Singapore CPI data...\n")

    summary_url = "https://tablebuilder.singstat.gov.sg/api/table/tabledata/M213751"

    try:
        r = requests.get(summary_url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        rows = r.json()["Data"]["row"]
    except Exception as e:
        print("❌ Error fetching data:", e)
        return

    prev_key, curr_key = get_two_latest(rows[0]["columns"])

    print("█" * 80)
    print(f"📊 SINGAPORE CPI DASHBOARD  ({prev_key} → {curr_key})")
    print("█" * 80)

    # OVERALL CPI
    for row in rows:
        if row["rowText"].strip().lower() == "all items":
            curr = get_value(row, curr_key)
            prev = get_value(row, prev_key)
            change, trend = calc_trend(curr, prev)

            print("\n── OVERALL CPI ──")
            print(f"All Items: {prev} → {curr}   {change}   {trend}")
            break

    # CATEGORY SUMMARY ✅ FIXED INDENTATION
    print("\n── CATEGORY SUMMARY ──")
    print(f"{'Category':<40} {prev_key:>10} {curr_key:>10} {'Change':>10}")

    category_map = {
        "Food & Non-Alcoholic Beverages": ["food"],
        "Housing & Utilities": ["housing"],
        "Transport": ["transport"],
        "Health": ["health"],
        "Education": ["education"],
        "Household Durables & Services": ["household"]
    }

    printed = set()

    for row in rows:
        name = row["rowText"].strip().lower()

        for cat, keywords in category_map.items():
            if cat in printed:
                continue

            if any(k in name for k in keywords):
                curr = get_value(row, curr_key)
                prev = get_value(row, prev_key)

                if not curr:
                    continue

                change, _ = calc_trend(curr, prev)

                print(f"{cat:<40} {prev:>10} {curr:>10} {change:>10}")
                printed.add(cat)
                break

    # FOOD DETAILS
    time.sleep(1)

    try:
        food_url = f"https://tablebuilder.singstat.gov.sg/api/table/tabledata/{FOOD_TABLE}"
        r = requests.get(food_url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        food_rows = r.json()["Data"]["row"]
    except Exception as e:
        print("\n❌ Failed to fetch food data:", e)
        return  # ✅ now correct

    prev_key, curr_key = get_two_latest(food_rows[0]["columns"])

    print("\n── FOOD PRICE DETAILS ──")
    print(f"{'Item':<45} {prev_key:>10} {curr_key:>10} {'Change':>10}")

    count = 0
    for row in food_rows:
        item = row.get("rowText", "").strip()

        if not item:
            continue

        curr = get_value(row, curr_key)
        prev = get_value(row, prev_key)

        if not curr:
            continue

        change, _ = calc_trend(curr, prev)

        print(f"{item:<45} {prev:>10} {curr:>10} {change:>10}")

        count += 1
        if count >= 25:
            break

    print("\n" + "█" * 80)
    print("💡 Dashboard: Summary (all sectors) + Food (detailed items)")
    print("█" * 80 + "\n")


# RUN
if __name__ == "__main__":
    show_cpi_dashboard()
