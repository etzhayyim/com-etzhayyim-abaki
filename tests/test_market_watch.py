import copy
import datetime as dt
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('watch', ROOT/'scripts/market_watch.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
TODAY = dt.date(2026, 10, 13)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.catalog = w.load(ROOT/'evidence/coverage-catalog.json')
        self.case = w.load(ROOT/'evidence/cases/au-supermarket-retailing.json')

    def test_real_cases_build_without_inventing_shares(self):
        with tempfile.TemporaryDirectory() as tmp:
            cases = w.build(ROOT/'evidence/cases', tmp, self.catalog, TODAY)
            self.assertEqual(len(cases), 3)
            self.assertTrue(all(c['metrics']['hhi'] is None for c in cases))
            coverage = w.load(Path(tmp)/'coverage.json')
            self.assertEqual(len(coverage['cells']), 251*21)
            self.assertEqual(sum(c['status']=='has-evidence-case' for c in coverage['cells']), 3)
            self.assertFalse(w.load(Path(tmp)/'receipt.json')['remote_publication_verified'])

    def test_missing_claim_evidence_refused(self):
        self.case['claims'][0]['source_refs'] = ['invented']
        with self.assertRaisesRegex(ValueError, 'evidence'):
            w.validate(self.case, self.catalog, TODAY)

    def test_secondary_source_cannot_support_official_classification(self):
        self.case['sources'][0]['kind'] = 'secondary'
        with self.assertRaisesRegex(ValueError, 'official finding'):
            w.validate(self.case, self.catalog, TODAY)

    def test_court_finding_requires_court_attribution(self):
        self.case = w.load(ROOT/'evidence/cases/us-google-general-search.json')
        self.case['classification_basis']['court_name'] = ''
        with self.assertRaisesRegex(ValueError, 'court attribution'):
            w.validate(self.case, self.catalog, TODAY)

    def shares(self, values):
        self.case['classification'] = 'concentration-screen'
        self.case['shares'] = [dict(entity_id=e['id'], percent=p, source_refs=e['source_refs'],
                                  period=self.case['period'], denominator=self.case['denominator'])
                               for e,p in zip(self.case['entities'], values)]

    def test_partial_shares_are_bounds_not_exact_hhi(self):
        self.shares([40,30])
        w.validate(self.case, self.catalog, TODAY)
        m = w.metrics(self.case)
        self.assertIsNone(m['hhi'])
        self.assertIsNone(m['cr2'])
        self.assertEqual(m['hhi_bounds'], [2500,3400])

    def test_complete_shares_and_control_aggregation(self):
        self.shares([50,30,20])
        self.case['shares_complete'] = True
        self.assertEqual(w.metrics(w.validate(self.case,self.catalog,TODAY))['hhi'],3800)
        self.case['entities'][1]['control_group'] = self.case['entities'][0]['control_group']
        with self.assertRaisesRegex(ValueError,'subsidiaries'):
            w.validate(self.case,self.catalog,TODAY)

    def test_share_mismatch_nan_and_overflow_refused(self):
        for value in (float('nan'), -1, 101):
            self.shares([value])
            with self.assertRaises(ValueError):
                w.validate(self.case,self.catalog,TODAY)
        self.shares([60,50])
        with self.assertRaisesRegex(ValueError,'exceed'):
            w.validate(self.case,self.catalog,TODAY)
        self.shares([40])
        self.case['shares'][0]['period']='another year'
        with self.assertRaisesRegex(ValueError,'incompatible'):
            w.validate(self.case,self.catalog,TODAY)

    def test_stale_case_does_not_refresh_itself(self):
        result=w.assess(self.case, TODAY+dt.timedelta(days=31))
        self.assertEqual(result['freshness'],'review-overdue')
        self.assertEqual(result['reviewed_on'],'2026-10-13')

    def test_queue_prioritizes_gaps_and_exposes_overdue_cases(self):
        self.assertEqual(w.queue(self.catalog,'AU','G',1,[self.case],TODAY)[0]['status'],'research-required')
        rows=w.queue(self.catalog,'AU','G',1,[self.case],TODAY+dt.timedelta(days=31))
        self.assertEqual(rows[0]['region'],'AU')
        self.assertEqual(rows[0]['status'],'review-overdue')
        with self.assertRaises(ValueError):
            w.queue(self.catalog,'invented','G')

    def test_future_evidence_refused(self):
        self.case['sources'][0]['accessed_on']='2027-01-01'
        with self.assertRaisesRegex(ValueError,'dates'):
            w.validate(self.case,self.catalog,TODAY)


if __name__ == '__main__':
    unittest.main()
