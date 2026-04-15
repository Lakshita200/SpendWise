import json
import requests
from datetime import datetime

# ---------------------------
# SingStat Table Builder API
# Table M213751 = Singapore CPI (2024 Base Year, Monthly)
# ---------------------------

API_URL = "https://tablebuilder.singstat.gov.sg/api/table/tabledata/M213751"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CPI-Dashboard/1.0)",
    "Accept": "application/json",
}

# ---------------------------
# Helpers
# ---------------------------

def parse_key_date(key):
    """Parse date key like '2026 Feb' or 'Feb 2026'"""
    key = key.strip()
    for fmt in ["%Y %b", "%b %Y"]:
        try:
            return datetime.strptime(key, fmt)
        except Exception:
            pass
    return None

def get_two_latest(columns):
    """Extract the two most recent date keys from columns"""
    dated = []
    for col in columns:
        key = col["Key"].strip()
        dt = parse_key_date(key)
        if dt:
            dated.append((dt, key))
    dated.sort()
    if len(dated) >= 2:
        return dated[-2][1], dated[-1][1]
    return None, None

def get_value(row, key):
    """Get value for a specific key from a row's columns"""
    if not key:
        return None
    for col in row["columns"]:
        k = col["Key"].strip()
        if k == key:
            v = col["Value"]
            if v not in (None, "", "-", "na", "NA"):
                return str(v)
    return None

def calc_trend(curr, prev):
    """Calculate and format trend indicator"""
    try:
        diff = float(curr) - float(prev)
        if diff > 0:
            return f"▲ {diff:.2f}", "📈 Rising"
        elif diff < 0:
            return f"▼ {abs(diff):.2f}", "📉 Falling"
        else:
            return "— 0.00", "➡ Stable"
    except Exception:
        return "N/A", "N/A"

# ---------------------------
# Fetch data from API
# ---------------------------

def fetch_cpi_data():
    """
    Fetch CPI data from SingStat Table Builder API.
    Returns the list of rows on success, None on failure.

    API endpoint:
      GET https://tablebuilder.singstat.gov.sg/api/table/tabledata/M213751

    Optional query parameters (all have sensible defaults, so omitting them
    returns the full dataset in the same JSON schema your original code expects):
      - offset / limit  : pagination (default returns all rows)
      - seriesNoORrowNo : filter to specific series numbers
      - isNARemoved     : "true" omits rows that are entirely N/A
    """
    print("⏳ Fetching Singapore CPI data from SingStat API...")
    print(f"   URL: {API_URL}\n")

    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        print("❌ Connection error — check your internet connection.")
        return None
    except requests.exceptions.Timeout:
        print("❌ Request timed out. Try again in a moment.")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP error: {e}")
        return None

    try:
        data = response.json()
    except json.JSONDecodeError:
        print("❌ Could not parse API response as JSON.")
        return None

    # The SingStat API wraps everything under a "Data" key
    rows = (
        data.get("Data", {}).get("row")          # typical structure
        or data.get("data", {}).get("row")        # alternate casing
        or data.get("row")                        # flat structure (matches original JSON)
        or []
    )

    if not rows:
        print("❌ No rows found in API response.")
        print("   Raw response keys:", list(data.keys()))
        return None

    return rows

# ---------------------------
# MAIN DASHBOARD
# ---------------------------

def show_cpi_dashboard():
    rows = fetch_cpi_data()
    if rows is None:
        return

    print(f"✅ Retrieved {len(rows)} categories from API")

    # Determine the two most recent periods from the first row's columns
    prev_key, curr_key = get_two_latest(rows[0]["columns"])
    if not prev_key or not curr_key:
        print("❌ Could not determine date keys from the API response. Exiting.")
        return

    print("█" * 90)
    print(f"📊 SINGAPORE CPI DASHBOARD  ({prev_key} → {curr_key})")
    print("█" * 90)

    # ── OVERALL CPI ──
    print("\n── OVERALL CPI ──")
    for row in rows:
        if row.get("rowText", "").strip().lower() == "all items":
            curr = get_value(row, curr_key)
            prev = get_value(row, prev_key)
            if curr and prev:
                change, trend = calc_trend(curr, prev)
                print(f"All Items: {prev} → {curr}   {change}   {trend}")
            break

    # ── ALL CATEGORIES ──
    print(f"\n── ALL CPI CATEGORIES ({prev_key} → {curr_key}) ──")
    print(f"{'Category':<60} {prev_key:>10} {curr_key:>10} {'Change':>10}")
    print("─" * 95)

    count = 0
    for row in rows:
        item = row.get("rowText", "").strip()
        series_no = row.get("seriesNo", row.get("SeriesNo", ""))

        if not item:
            continue

        curr = get_value(row, curr_key)
        prev = get_value(row, prev_key)

        if curr:
            change, _ = calc_trend(curr, prev)
            prev_str = prev if prev else "N/A"

            # Visual hierarchy via indentation based on series number depth
            depth = len(str(series_no).split(".")) - 1 if series_no else 0
            indent = "  " * min(depth, 5)
            display_item = (indent + item)[:60]

            print(f"{display_item:<60} {prev_str:>10} {curr:>10} {change:>10}")
            count += 1

    print("─" * 95)
    print(f"\n  ✅ Printed {count}/{len(rows)} categories (all with data)")

    print("\n" + "█" * 90)
    print("💡 Data sourced live from SingStat Table Builder API")
    print(f"   Endpoint : {API_URL}")
    print(f"   Periods  : {prev_key} → {curr_key}")
    print(f"   Categories: {len(rows)}")
    print("█" * 90 + "\n")


# RUN
if __name__ == "__main__":
    show_cpi_dashboard()
