import requests
import xml.etree.ElementTree as ET
import csv
import io
import time
import sys
import os

HARDWARE_VENUES = {"DAC", "ICCAD", "ISCA", "MICRO", "HPCA", "ASPLOS", "ISSCC", "CICC", "VLSI"}

print("Downloading CSRankings data...")
try:
    cs_url = 'https://raw.githubusercontent.com/emeryberger/CSrankings/gh-pages/csrankings.csv'
    cs_data = requests.get(cs_url).text
    cs_reader = csv.DictReader(io.StringIO(cs_data))
    
    candidates = list(cs_reader)
            
except Exception as e:
    print(f"Failed to fetch CSRankings data: {e}")
    sys.exit(1)

print(f"Found {len(candidates)} total faculty across all global institutions.")
print("Querying DBLP to filter for active hardware researchers (this will take ~12 hours to complete)...")
print("Checkpointing is ENABLED. You can stop (Ctrl+C) and restart this script at any time without losing progress.")

# Load already processed faculty names to allow for resume
processed_names = set()
output_file = '../data/faculty_institutions.csv'

if os.path.exists(output_file):
    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if len(row) > 1:
                processed_names.add(row[1])
    mode = 'a'
else:
    mode = 'w'

with open(output_file, mode, newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    if mode == 'w':
        writer.writerow(['id', 'name', 'affiliation', 'homepage', 'scholarid', 'dblpid', 'subareas'])
    
    fac_idx = len(processed_names) + 1
    
    for i, candidate in enumerate(candidates):
        name = candidate['name']
        affiliation = candidate['affiliation']
        
        if name in processed_names:
            continue
            
        print(f"[{i+1}/{len(candidates)}] Checking {name} ({affiliation})...", end='', flush=True)
        
        # 1. Find PID via DBLP Search API
        search_url = f"https://dblp.org/search/author/api?q={requests.utils.quote(name)}&format=json"
        try:
            res = requests.get(search_url, timeout=10)
            time.sleep(1.2) # Mandatory DBLP delay
            
            if res.status_code != 200:
                print(" API Error")
                continue
                
            data = res.json()
            hits = data.get('result', {}).get('hits', {}).get('hit', [])
            if not hits:
                print(" Not found in DBLP")
                continue
                
            # Take the most likely hit (first one)
            pid = hits[0]['info'].get('url', '').replace('https://dblp.org/pid/', '')
            if not pid:
                print(" No PID")
                continue
                
            # 2. Fetch their XML to verify if they are a hardware researcher
            xml_url = f"https://dblp.org/pid/{pid}.xml"
            xml_res = requests.get(xml_url, timeout=10)
            time.sleep(1.2) # Mandatory DBLP delay
            
            if xml_res.status_code != 200:
                print(" XML Fetch Error")
                continue
                
            root = ET.fromstring(xml_res.text)
            
            is_hardware = False
            for pub in root.findall('.//r'):
                venue_node = pub.find('.//booktitle')
                if venue_node is not None and venue_node.text:
                    if any(hv in venue_node.text.upper() for hv in HARDWARE_VENUES):
                        is_hardware = True
                        break
                        
            if is_hardware:
                print(" MATCH! Added to list.")
                fac_id = f"f{fac_idx}"
                writer.writerow([fac_id, name, affiliation, candidate['homepage'], candidate['scholarid'], pid, ''])
                f.flush()
                fac_idx += 1
            else:
                print(" Skipped (No hardware papers)")
                
            # Mark as processed even if skipped to save time on resume
            processed_names.add(name)
            
        except Exception as e:
            print(f" Error: {e}")
            time.sleep(2) # Backoff on error

print(f"\nFinished! Found {fac_idx-1} active hardware researchers from all global institutions.")
print("Data saved to data/faculty_institutions.csv")
