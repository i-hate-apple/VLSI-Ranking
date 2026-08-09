import requests
import xml.etree.ElementTree as ET
import csv
import io
import time
from collections import defaultdict

VENUES = {
    'dac': 'EDA',
    'iccad': 'EDA',
    'isca': 'Computer Architecture',
    'micro': 'Computer Architecture',
    'hpca': 'Computer Architecture',
    'asplos': 'Computer Architecture',
    'isscc': 'Circuits & VLSI Design',
    'cicc': 'Circuits & VLSI Design'
}
YEARS = [2018, 2019, 2020, 2021, 2022, 2023]
TOP_N = 1000

print("Downloading CSRankings affiliations...")
try:
    cs_url = 'https://raw.githubusercontent.com/emeryberger/CSrankings/gh-pages/csrankings.csv'
    cs_data = requests.get(cs_url).text
    cs_reader = csv.DictReader(io.StringIO(cs_data))
    cs_affiliations = {row['name'].strip().lower(): row['affiliation'] for row in cs_reader}
except Exception as e:
    print(f"Failed to fetch CSRankings data: {e}")
    cs_affiliations = {}

author_counts = defaultdict(int)
author_names = {}
author_primary_venue = defaultdict(lambda: defaultdict(int))

print("Fetching DBLP venue data...")
for venue, subarea in VENUES.items():
    for year in YEARS:
        url = f"https://dblp.org/db/conf/{venue}/{venue}{year}.xml"
        try:
            print(f"Fetching {url}...")
            res = requests.get(url, timeout=10)
            time.sleep(0.5) # courtesy delay
            if res.status_code != 200:
                print(f"Skipping {venue} {year}: HTTP {res.status_code}")
                continue
            
            root = ET.fromstring(res.text)
            for author_node in root.findall('.//author'):
                pid = author_node.get('pid')
                name = author_node.text
                if not pid or not name:
                    continue
                # Clean name: remove DBLP numbers
                import re
                clean_name = re.sub(r'\s+\d{4}$', '', name)
                
                author_counts[pid] += 1
                author_names[pid] = clean_name
                author_primary_venue[pid][subarea] += 1
        except Exception as e:
            print(f"Error fetching {url}: {e}")

print(f"Total unique authors found: {len(author_counts)}")

# Sort by publication count in our venues
sorted_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)
top_authors = sorted_authors[:TOP_N]

print(f"Writing top {TOP_N} authors to faculty_bootstrap.csv...")
with open('../data/faculty_bootstrap.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['id', 'name', 'affiliation', 'homepage', 'scholarid', 'dblpid', 'subareas'])
    
    for i, (pid, count) in enumerate(top_authors):
        fac_id = f"f{i+1}"
        name = author_names[pid]
        
        # Try to find affiliation
        affiliation = cs_affiliations.get(name.lower(), 'Unknown')
        
        # Determine primary subarea
        primary_subarea = max(author_primary_venue[pid].items(), key=lambda x: x[1])[0]
        
        writer.writerow([fac_id, name, affiliation, '', '', pid, primary_subarea])

print("Bootstrap complete. Output saved to data/faculty_bootstrap.csv.")
