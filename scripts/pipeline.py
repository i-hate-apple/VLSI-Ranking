import csv
import json
import os
import requests
import xml.etree.ElementTree as ET
from collections import defaultdict
import time

def load_csv(filepath):
    """Load a CSV file and return a list of dictionaries."""
    data = []
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
    return data

def resolve_author_entity(author_name, faculty_id_by_name):
    """
    Match an author name from an API to a faculty ID using exact match and aliases.
    Returns the matched faculty ID or None.
    """
    author_name_lower = author_name.lower().strip()
    return faculty_id_by_name.get(author_name_lower)

def fetch_semantic_scholar_papers(scholar_id):
    """Fetch papers for a given Semantic Scholar author ID."""
    if not scholar_id:
        return []
        
    papers = []
    offset = 0
    limit = 100
    
    while True:
        url = f"https://api.semanticscholar.org/graph/v1/author/{scholar_id}/papers"
        params = {
            "fields": "title,year,venue,authors.name,externalIds",
            "offset": offset,
            "limit": limit
        }
        
        try:
            # We add a sleep to respect basic rate limits without API key (1 request/sec)
            time.sleep(1.2)
            response = requests.get(url, params=params, timeout=10)
            
            # TODO: Add retry-with-backoff on 429 responses before this scales to a larger faculty list.
            # Currently it will break out and silently produce incomplete data for that faculty member.
            if response.status_code == 429:
                pass # placeholder for future backoff logic
                
            if response.status_code == 404:
                break
            response.raise_for_status()
            data = response.json()
            
            for item in data.get('data', []):
                # normalize to our expected format
                authors = [a.get('name', '') for a in item.get('authors', [])]
                doi = item.get('externalIds', {}).get('DOI', '')
                paper_obj = {
                    'title': item.get('title', ''),
                    'year': item.get('year'),
                    'venue': item.get('venue', ''),
                    'authors': authors,
                    'doi': doi
                }
                papers.append(paper_obj)
            
            if 'next' in data and data['next'] > 0:
                offset = data['next']
            else:
                break
                
        except Exception as e:
            print(f"Error fetching Semantic Scholar papers for {scholar_id}: {e}")
            break
            
    return papers

def fetch_dblp_papers(dblp_id):
    """Fetch papers for a given DBLP author ID (PID)."""
    if not dblp_id:
        return []
    
    url = f"https://dblp.org/pid/{dblp_id}.xml"
    papers = []
    
    headers = {
        "User-Agent": "wehateapple/1.0 (https://github.com/i-hate-apple/vlsiranking)"
    }
    
    try:
        # Courtesy delay
        time.sleep(1.2)
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        
        # Papers are wrapped in <r> elements inside the root <dblpperson>
        for r in root.findall('r'):
            # The actual publication node is usually <article> or <inproceedings>
            pub_node = None
            if len(r) > 0:
                pub_node = r[0]
            
            if pub_node is None or pub_node.tag not in ('article', 'inproceedings'):
                continue
                
            if pub_node.get('publtype') == 'informal':
                continue
                
            title_node = pub_node.find('title')
            title = ''.join(title_node.itertext()).strip() if title_node is not None else ''
            
            year_str = pub_node.findtext('year', default='')
            year = int(year_str) if year_str.isdigit() else None
            
            venue = pub_node.findtext('journal')
            if not venue:
                venue = pub_node.findtext('booktitle')
            venue = venue or ''
            
            authors = [a.text for a in pub_node.findall('author') if a.text]
            
            doi = ''
            for ee in pub_node.findall('ee'):
                if ee.text and 'doi.org/' in ee.text:
                    doi = ee.text.strip()
                    break
            
            if doi.startswith('https://doi.org/'):
                doi = doi.replace('https://doi.org/', '')
            
            paper_obj = {
                'title': title,
                'year': year,
                'venue': venue,
                'authors': authors,
                'doi': doi
            }
            papers.append(paper_obj)
            
    except Exception as e:
        print(f"Error fetching DBLP papers for {dblp_id}: {e}")
        
    return papers

def calculate_geometric_mean(subareas_dict):
    """Calculate the geometric mean of publication counts across active sub-areas."""
    if not subareas_dict:
        return 0.0
    product = 1.0
    for count in subareas_dict.values():
        product *= (count + 1)
    return product ** (1 / len(subareas_dict))

def process_paper(paper, venue_subareas, faculty_id_by_name):
    """
    Process a single paper. Returns the subarea, matched faculty IDs, and the adjusted count.
    """
    venue = paper.get('venue', '')
    if venue is None:
        return None, None, None
    venue = venue.lower().strip()
    if venue not in venue_subareas:
        return None, None, None
        
    subarea = venue_subareas[venue]
    authors = paper.get('authors', [])
    
    # Match authors to faculty IDs
    matched_faculty_ids = set()
    for author in authors:
        fid = resolve_author_entity(author, faculty_id_by_name)
        if fid:
            matched_faculty_ids.add(fid)
            
    # Calculate adjusted count based on TOTAL authors on the paper, not just matched ones
    total_authors = len(authors) if authors else 1
    adjusted_count = 1.0 / total_authors
    
    return subarea, matched_faculty_ids, adjusted_count

def dedup_papers(papers_list):
    """
    Deduplicate a list of papers based on DOI (if available) or normalized title+year.
    """
    deduped = {}
    
    for p in papers_list:
        doi = p.get('doi', '').strip().lower()
        title = p.get('title', '').strip().lower()
        year = p.get('year')
        
        # Normalize title by removing common punctuation for comparison fallback
        norm_title = ''.join(c for c in title if c.isalnum() or c.isspace()).strip()
        
        if doi:
            dedup_key = f"doi:{doi}"
        elif norm_title and year:
            dedup_key = f"title:{norm_title}|year:{year}"
        else:
            # If we don't have enough info to dedup confidently, keep it via a unique id
            dedup_key = f"unmatched:{id(p)}"
            
        # We assume the first paper with a given key is kept
        if dedup_key not in deduped:
            deduped[dedup_key] = p
            
    return list(deduped.values())

def process_data(data_dir, output_file):
    # Load inputs
    faculty = load_csv(os.path.join(data_dir, 'faculty.csv'))
    aliases = load_csv(os.path.join(data_dir, 'aliases.csv'))
    venues = load_csv(os.path.join(data_dir, 'venues.csv'))
    venue_aliases = load_csv(os.path.join(data_dir, 'venue_aliases.csv'))

    # Build lookup dictionaries
    faculty_id_by_name = {}
    faculty_by_id = {}
    for f in faculty:
        faculty_id_by_name[f['name'].lower().strip()] = f['id']
        faculty_by_id[f['id']] = f
    
    for a in aliases:
        faculty_id_by_name[a['alias_name'].lower().strip()] = a['faculty_id']

    venue_subareas = {}
    venue_subarea_by_code = {}
    for v in venues:
        subarea = v['subarea']
        code = v['venue_code'].lower().strip()
        venue_subarea_by_code[code] = subarea
        venue_subareas[code] = subarea
        venue_subareas[v['full_name'].lower().strip()] = subarea
        
    for a in venue_aliases:
        alias = a['alias_name'].lower().strip()
        code = a['venue_code'].lower().strip()
        if code in venue_subarea_by_code:
            venue_subareas[alias] = venue_subarea_by_code[code]

    # Initialize data structure
    institutions_map = defaultdict(lambda: {'name': '', 'country': 'Unknown', 'faculty': []})
    
    # Process each faculty
    for f in faculty:
        inst = f['affiliation']
        institutions_map[inst]['name'] = inst
        
        # Fetch publications from APIs
        s2_papers = fetch_semantic_scholar_papers(f.get('scholarid'))
        dblp_papers = fetch_dblp_papers(f.get('dblpid'))
        
        all_papers = s2_papers + dblp_papers
        
        # Deduplicate papers by title/doi to avoid double counting across APIs.
        papers = dedup_papers(all_papers)
        
        subareas_counts = defaultdict(float)
        trend = defaultdict(float)
        coauthors = set()
        
        for p in papers:
            subarea, matched_faculty_ids, adjusted_count = process_paper(p, venue_subareas, faculty_id_by_name)
            if not subarea:
                continue
                
            if f['id'] in matched_faculty_ids:
                subareas_counts[subarea] += adjusted_count
                if 'year' in p:
                    trend[p['year']] += adjusted_count
                
                # Track co-authors
                for coauthor_id in matched_faculty_ids:
                    if coauthor_id != f['id']:
                        coauthors.add(coauthor_id)

        faculty_data = {
            'id': f['id'],
            'name': f['name'],
            'subareas': dict(subareas_counts),
            'trend': [{'year': k, 'count': v} for k, v in trend.items()],
            'coauthors': list(coauthors),
            'links': {
                'homepage': f['homepage'],
                'scholar': f['scholarid'],
                'dblp': f['dblpid']
            }
        }
        
        institutions_map[inst]['faculty'].append(faculty_data)

    # Format output
    output_data = {
        'institutions': list(institutions_map.values())
    }

    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)

if __name__ == "__main__":
    data_directory = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    output_filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data.json')
    process_data(data_directory, output_filepath)
    print(f"Successfully generated {output_filepath}")
