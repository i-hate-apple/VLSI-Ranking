import requests
import xml.etree.ElementTree as ET
import csv
import io
import time
import sys

# Target countries based on user list: US, China, Taiwan, South Korea, Japan, India, Germany, UK, Belgium, Netherlands, France, Singapore
TOP_INSTITUTION_KEYWORDS = [
    # USA
    "Massachusetts Institute of Technology", "Stanford", "Berkeley", "Urbana-Champaign", 
    "Carnegie Mellon", "University of Michigan", "Georgia Institute", "Austin", "Cornell", 
    "Purdue", "Los Angeles", "San Diego", "University of Washington", "Wisconsin", "Princeton",
    # China
    "Tsinghua", "Peking", "Shanghai Jiao Tong", "Zhejiang", "Fudan",
    # Taiwan
    "National Taiwan University", "National Tsing Hua", "Chiao Tung", "Cheng Kung",
    # South Korea
    "KAIST", "Seoul National", "POSTECH",
    # Japan
    "University of Tokyo", "Science Tokyo", "Kyoto University",
    # India
    "IIT Bombay", "IIT Delhi", "IIT Madras", "IIT Kanpur", "IISc",
    # Germany
    "TU Munich", "Aachen", "Dresden", "Karlsruhe",
    # UK
    "Cambridge", "Oxford", "Imperial College", "Edinburgh", "UCL",
    # Belgium
    "KU Leuven",
    # Netherlands
    "Delft", "Eindhoven",
    # France
    "Sorbonne", "Grenoble", "CentraleSupelec",
    # Singapore
    "National University of Singapore", "Nanyang Technological"
]

HARDWARE_VENUES = {"DAC", "ICCAD", "ISCA", "MICRO", "HPCA", "ASPLOS", "ISSCC", "CICC", "VLSI"}

print("Downloading CSRankings data...")
try:
    cs_url = 'https://raw.githubusercontent.com/emeryberger/CSrankings/gh-pages/csrankings.csv'
    cs_data = requests.get(cs_url).text
    cs_reader = csv.DictReader(io.StringIO(cs_data))
    
    candidates = []
    for row in cs_reader:
        affiliation = row['affiliation']
        if any(keyword.lower() in affiliation.lower() for keyword in TOP_INSTITUTION_KEYWORDS):
            candidates.append(row)
            
except Exception as e:
    print(f"Failed to fetch CSRankings data: {e}")
    sys.exit(1)

print(f"Found {len(candidates)} total faculty at top global institutions.")
print("Querying DBLP to filter for active hardware researchers (this will take several hours)...")

valid_faculty = []

with open('../data/faculty_institutions.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['id', 'name', 'affiliation', 'homepage', 'scholarid', 'dblpid', 'subareas'])
    
    fac_idx = 1
    for i, candidate in enumerate(candidates):
        name = candidate['name']
        affiliation = candidate['affiliation']
        
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
                
        except Exception as e:
            print(f" Error: {e}")
            time.sleep(2) # Backoff on error

print(f"\nFinished! Found {fac_idx-1} active hardware researchers from top institutions.")
print("Data saved to data/faculty_institutions.csv")
