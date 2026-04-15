import json
from datetime import datetime

# Load from local JSON file instead of API
JSON_FILE = r"C:\Users\pushp\Downloads\M213751.json"

# ---------------------------
# Helpers
# ---------------------------

def parse_key_date(key):
    """Parse date key like '2026 Feb' or 'Feb 2026'"""
    key = key.strip()
    for fmt in ["%Y %b", "%b %Y"]:
        try:
            return datetime.strptime(key, fmt)
        except:
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
    except:
        return "N/A", "N/A"

# ---------------------------
# MAIN DASHBOARD
# ---------------------------

def show_cpi_dashboard():
    print("\n⏳ Loading Singapore CPI data from JSON file...\n")

    # Load from JSON file
    with open(JSON_FILE, 'r') as f:
        data = json.load(f)
    
    rows = data.get('row', [])
    
    if not rows:
        print("❌ No data found in JSON file. Exiting.")
        return

    print(f"✅ Loaded {len(rows)} categories from file")

    prev_key, curr_key = get_two_latest(rows[0]["columns"])
    if not prev_key or not curr_key:
        print("❌ Could not determine date keys. Exiting.")
        return

    print("█" * 90)
    print(f"📊 SINGAPORE CPI DASHBOARD  ({prev_key} → {curr_key})")
    print("█" * 90)

    # OVERALL CPI - Find "All Items" row
    print("\n── OVERALL CPI ──")
    for row in rows:
        if row.get("rowText", "").strip().lower() == "all items":
            curr = get_value(row, curr_key)
            prev = get_value(row, prev_key)
            if curr and prev:
                change, trend = calc_trend(curr, prev)
                print(f"All Items: {prev} → {curr}   {change}   {trend}")
            break

    # PRINT ALL 207 CATEGORIES
    print(f"\n── ALL CPI CATEGORIES ({prev_key} → {curr_key}) ──")
    print(f"{'Category':<60} {prev_key:>10} {curr_key:>10} {'Change':>10}")
    print("─" * 95)
    
    count = 0
    for row in rows:
        item = row.get("rowText", "").strip()
        series_no = row.get("SeriesNo", "")
        
        if not item:
            continue
        
        curr = get_value(row, curr_key)
        prev = get_value(row, prev_key)
        
        # Print EVERY row that has data
        if curr:
            change, _ = calc_trend(curr, prev)
            prev_str = prev if prev else "N/A"
            
            # Add indentation based on seriesNo depth for visual hierarchy
            depth = len(series_no.split('.')) - 1 if series_no else 0
            indent = "  " * min(depth, 5)  # Cap indent at 5 levels
            
            # Format item name with indent
            display_item = (indent + item)[:60]
            
            print(f"{display_item:<60} {prev_str:>10} {curr:>10} {change:>10}")
            count += 1
    
    print("─" * 95)
    print(f"\n  ✅ Printed {count}/{len(rows)} categories (all with data)")

    print("\n" + "█" * 90)
    print("💡 Dashboard loaded from local JSON file")
    print(f"   File: {JSON_FILE}")
    print(f"   Total categories: {len(rows)}")
    print("█" * 90 + "\n")


# RUN
if __name__ == "__main__":
    show_cpi_dashboard()