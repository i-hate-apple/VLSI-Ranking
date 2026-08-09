import unittest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from pipeline import fetch_dblp_papers

class TestDBLPPapers(unittest.TestCase):
    @patch('pipeline.requests.get')
    def test_fetch_dblp_papers_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'''<?xml version="1.0" encoding="US-ASCII"?>
<dblpperson name="Anantha P. Chandrakasan" pid="c/AnanthaChandrakasan" n="465">
    <r>
        <article key="journals/jssc/Smith23">
            <author>John Smith</author>
            <author>Anantha P. Chandrakasan</author>
            <title>A 60-GHz Low-Noise mmWave Divider-Less Fractional-N Cascaded PLL Achieving -250.2-dB FoM <i>in 28-nm CMOS.</i></title>
            <journal>IEEE J. Solid-State Circuits</journal>
            <year>2023</year>
            <ee>https://www.wikidata.org/entity/Q11111111</ee>
            <ee>https://doi.org/10.1109/JSSC.2023.1234567</ee>
        </article>
    </r>
    <r>
        <inproceedings key="conf/isscc/Doe24">
            <author>Jane Doe</author>
            <title>Another paper</title>
            <booktitle>ISSCC</booktitle>
            <year>2024</year>
            <ee>https://doi.org/10.1109/ISSCC.2024.7654321</ee>
        </inproceedings>
    </r>
    <r>
        <article key="journals/corr/abs-2401-00001" publtype="informal">
            <author>Jane Doe</author>
            <title>Informal preprint paper</title>
            <journal>CoRR</journal>
            <year>2024</year>
            <ee>https://doi.org/10.48550/arXiv.2401.00001</ee>
        </article>
    </r>
</dblpperson>'''
        mock_get.return_value = mock_response

        papers = fetch_dblp_papers('c/AnanthaChandrakasan')
        
        self.assertEqual(len(papers), 2)
        
        self.assertEqual(papers[0]['title'], 'A 60-GHz Low-Noise mmWave Divider-Less Fractional-N Cascaded PLL Achieving -250.2-dB FoM in 28-nm CMOS.')
        self.assertEqual(papers[0]['year'], 2023)
        self.assertEqual(papers[0]['venue'], 'IEEE J. Solid-State Circuits')
        self.assertEqual(papers[0]['authors'], ['John Smith', 'Anantha P. Chandrakasan'])
        self.assertEqual(papers[0]['doi'], '10.1109/JSSC.2023.1234567')

        self.assertEqual(papers[1]['title'], 'Another paper')
        self.assertEqual(papers[1]['year'], 2024)
        self.assertEqual(papers[1]['venue'], 'ISSCC')
        self.assertEqual(papers[1]['authors'], ['Jane Doe'])
        self.assertEqual(papers[1]['doi'], '10.1109/ISSCC.2024.7654321')

    @patch('pipeline.requests.get')
    def test_fetch_dblp_papers_missing_fields(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'''<?xml version="1.0" encoding="US-ASCII"?>
<dblpperson name="Unknown" pid="u/Unknown" n="1">
    <r>
        <article key="journals/jssc/Unknown">
            <!-- Missing title, venue, year, doi, authors -->
        </article>
    </r>
</dblpperson>'''
        mock_get.return_value = mock_response

        papers = fetch_dblp_papers('u/Unknown')
        
        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0]['title'], '')
        self.assertEqual(papers[0]['year'], None)
        self.assertEqual(papers[0]['venue'], '')
        self.assertEqual(papers[0]['authors'], [])
        self.assertEqual(papers[0]['doi'], '')

    @patch('pipeline.requests.get')
    def test_fetch_dblp_papers_url_construction(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'<dblpperson></dblpperson>'
        mock_get.return_value = mock_response

        fetch_dblp_papers('c/AnanthaChandrakasan')
        mock_get.assert_called_once()
        self.assertEqual(mock_get.call_args[0][0], 'https://dblp.org/pid/c/AnanthaChandrakasan.xml')
        self.assertIn('User-Agent', mock_get.call_args[1]['headers'])

if __name__ == '__main__':
    unittest.main()
