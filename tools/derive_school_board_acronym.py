import json
import re
from urllib.parse import urlparse

# Load the existing JSON
with open("../data/20251030_school_boards.json", "r", encoding="utf-8") as f:
    data = json.load(f)

fields = data["fields"]
records = data["records"]

# Insert new field definition after "Board Name"
insert_index = next(i for i, f in enumerate(fields) if f["id"] == "Board Name") + 1
fields.insert(insert_index, {
    "id": "Board Acronym",
    "type": "text",
    "info": {
        "notes": "Acronym derived from the website domain (e.g., ADSB for www.adsb.on.ca)",
        "type_override": "text",
        "frictionless_dict": [{"type": "string", "name": "Board Acronym"}]
    }
})

# Derive acronyms and insert into records
for record in records:
    website = record[-1]
    if website:
        domain = urlparse(website).netloc.lower()
        # Strip common prefixes/suffixes
        domain = re.sub(r"^(www\.|school\.|.*//)", "", domain)
        acronym = re.split(r"[.\-]", domain)[0].upper()
    else:
        acronym = None
    record.insert(insert_index, acronym)

# Save updated JSON
with open("../data/school_boards_with_acronyms.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Updated file written: school_boards_with_acronyms.json")
