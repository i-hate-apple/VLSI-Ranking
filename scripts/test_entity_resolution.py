import unittest
from pipeline import resolve_author_entity, calculate_geometric_mean, process_paper, dedup_papers

class TestEntityResolution(unittest.TestCase):
    def setUp(self):
        self.faculty_id_by_name = {
            "john doe": "jdoe1",
            "j. doe": "jdoe1",
            "jane smith": "jsmith2"
        }

    def test_exact_match(self):
        self.assertEqual(resolve_author_entity("John Doe", self.faculty_id_by_name), "jdoe1")
        self.assertEqual(resolve_author_entity("Jane Smith", self.faculty_id_by_name), "jsmith2")

    def test_alias_match(self):
        self.assertEqual(resolve_author_entity("J. Doe", self.faculty_id_by_name), "jdoe1")

    def test_case_insensitive_match(self):
        self.assertEqual(resolve_author_entity("JOHN DOE", self.faculty_id_by_name), "jdoe1")
        self.assertEqual(resolve_author_entity("jane smith ", self.faculty_id_by_name), "jsmith2")

    def test_no_match(self):
        self.assertIsNone(resolve_author_entity("Alan Turing", self.faculty_id_by_name))

class TestGeometricMean(unittest.TestCase):
    def test_calculate_geometric_mean(self):
        subareas = {"EDA": 3.0, "Architecture": 8.0}
        # ( (3+1) * (8+1) ) ^ (1/2) = (4 * 9) ^ 0.5 = 36 ^ 0.5 = 6.0
        self.assertAlmostEqual(calculate_geometric_mean(subareas), 6.0)

    def test_empty_subareas(self):
        self.assertEqual(calculate_geometric_mean({}), 0.0)

class TestPaperProcessing(unittest.TestCase):
    def setUp(self):
        self.venue_subareas = {"isscc": "Circuits", "dac": "EDA"}
        self.faculty_id_by_name = {
            "alice": "fac1",
            "bob": "fac2"
        }

    def test_fractional_credit(self):
        paper = {
            "venue": "dac",
            "authors": ["Alice", "Bob", "Charlie", "Dave"]
        }
        subarea, matched_ids, adjusted_count = process_paper(paper, self.venue_subareas, self.faculty_id_by_name)
        
        self.assertEqual(subarea, "EDA")
        self.assertSetEqual(matched_ids, {"fac1", "fac2"})
        # 4 total authors means each matched faculty gets 0.25 credit
        self.assertEqual(adjusted_count, 0.25)

class TestDeduplication(unittest.TestCase):
    def test_dedup_by_doi(self):
        papers = [
            {"title": "A Great Paper", "doi": "10.1109/ISSCC.2023.1"},
            {"title": "A Great Paper (Preprint)", "doi": "10.1109/ISSCC.2023.1"},
            {"title": "Another Paper", "doi": "10.1109/ISSCC.2023.2"}
        ]
        deduped = dedup_papers(papers)
        self.assertEqual(len(deduped), 2)
        titles = {p["title"] for p in deduped}
        # The first paper with a DOI is kept
        self.assertIn("A Great Paper", titles)
        self.assertIn("Another Paper", titles)

    def test_dedup_by_title_and_year(self):
        papers = [
            {"title": "Towards Faster Chips", "year": 2022, "doi": ""},
            {"title": "Towards Faster Chips!", "year": 2022, "doi": ""},
            {"title": "Towards Faster Chips", "year": 2023, "doi": ""}
        ]
        deduped = dedup_papers(papers)
        self.assertEqual(len(deduped), 2)
        
    def test_no_dedup_missing_info(self):
        papers = [
            {"title": "", "year": None, "doi": ""},
            {"title": "", "year": None, "doi": ""}
        ]
        deduped = dedup_papers(papers)
        self.assertEqual(len(deduped), 2)

if __name__ == "__main__":
    unittest.main()
