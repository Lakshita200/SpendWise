# # # import requests

# # # HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

# # # # These are known SingStat CPI table IDs to try
# # # TABLE_IDS = [
# # #     "M212881",  # CPI All Items & Major Categories (most likely)
# # #     "M212891",
# # #     "M213801",
# # #     "M213001",
# # #     "M213011",
# # #     "M213751",  # your current one (food only)
# # # ]

# # # for tid in TABLE_IDS:
# # #     url = f"https://tablebuilder.singstat.gov.sg/api/table/tabledata/{tid}"
# # #     try:
# # #         r = requests.get(url, headers=HEADERS, timeout=10)
# # #         r.raise_for_status()
# # #         rows = r.json()["Data"]["row"]
# # #         labels = [row["rowText"].strip() for row in rows[:6]]
# # #         print(f"\n✅ {tid}:")
# # #         for l in labels:
# # #             print(f"   {l}")
# # #     except Exception as e:
# # #         print(f"\n❌ {tid}: {e}")


# # import requests

# # HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
# # r = requests.get("https://tablebuilder.singstat.gov.sg/api/table/tabledata/M213751", headers=HEADERS, timeout=20)
# # data = r.json()["Data"]["row"]

# # print("First 10 column keys:")
# # for col in data[0]["columns"][:10]:
# #     print(" ", repr(col["key"]))


# import json
# from urllib.request import Request,urlopen
# hdr = {'User-Agent': 'Mozilla/5.0', "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,/;q=0.8"}
# url = "https://tablebuilder.singstat.gov.sg/api/table/tabledata/M213071?seriesNoORrowNo=1.1&offset=0&limit=3000&sortBy=rowtext%20asc&timeFilter=2023%201H&between=0%2C%209000&search=food"
# request = Request(url,headers=hdr)
# data = urlopen(request).read()
# print(data)



# import json
# import requests

# url = "https://tablebuilder.singstat.gov.sg/api/table/tabledata/M213751"
# params = {
#     "offset": 0,
#     "limit": 10
# }
# headers = {
#     "User-Agent": "Mozilla/5.0",
#     "Accept": "application/json"
# }

# try:
#     response = requests.get(url, params=params, headers=headers, timeout=10)
#     print(f"Status Code: {response.status_code}")
    
#     if response.status_code == 200:
#         data = response.json()
#         print(json.dumps(data, indent=2)[:500])
#     else:
#         print(f"Error response: {response.text}")
        
# except requests.exceptions.RequestException as e:
#     print(f"Request failed: {e}")


import json
from urllib.request import Request, urlopen

# hdr = {
#     'User-Agent': 'Mozilla/5.0',
#     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
# }

# # ✅ Correct: keyword=clothing, searchOption=variable
# url = "https://tablebuilder.singstat.gov.sg/api/table/resourceid?keyword=clothing&searchOption=variable"

# request = Request(url, headers=hdr)
# try:
#     data = urlopen(request).read()
#     print(data.decode('utf-8'))  # Decode bytes to string
# except Exception as e:
#     print(f"Error: {e}")
import requests

BASE_URL = "https://tablebuilder.singstat.gov.sg/api/table"
table_id = "M213751"

# Required headers per SingStat FAQ [[15]]
HEADERS = {
    "user-agent": "Mozilla/5.0",  # Required
    "accept": "application/json"   # Required
}

def fetch_metadata(table_id):
    """Fetch metadata for a table to get series info dynamically"""
    # Remove isTestApi parameter - not documented [[11]]
    url = f"{BASE_URL}/metadata/{table_id}"
    
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        data = r.json()
        
        # Correct path to series data
        records = data.get("Data", {}).get("records", {})
        rows = records.get("row", [])  # ← This is where series info lives
        
        return rows
        
    except requests.exceptions.HTTPError as e:
        if r.status_code == 403:
            print(f"⚠️ 403 Error: Missing required headers. Ensure 'user-agent' and 'accept' are set.")
        else:
            print(f"⚠️ HTTP Error {r.status_code} for {table_id}: {e}")
    except Exception as e:
        print(f"⚠️ Could not fetch metadata for {table_id}: {e}")
    
    return []

# Test it
summary_metadata = fetch_metadata(table_id=table_id)
print(f"Found {len(summary_metadata)} series")
if summary_metadata:
    for item in summary_metadata:  # Print first 3 as sample
        print(f"  - {item.get('rowText')}: {item.get('seriesNo')}")