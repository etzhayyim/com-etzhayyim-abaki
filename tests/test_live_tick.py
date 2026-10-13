import datetime as dt
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
live=module('live','live_tick.py');watch=module('watch','market_watch.py')

class LiveTests(unittest.TestCase):
    def setUp(self):
        self.catalog=live.read(ROOT/'evidence/coverage-catalog.json')
        self.today=dt.date(2026,10,13)
    def test_rotation_changes_country_before_industry(self):
        first=live.choose(self.catalog,{},[],self.today)
        second=live.choose(self.catalog,{'cursor':first['cursor']+1},[],self.today)
        self.assertEqual((first['region'],first['industry']),('JP','J'))
        self.assertNotEqual(first['region'],second['region'])
        self.assertEqual(first['industry'],second['industry'])
    def test_overdue_refresh_precedes_discovery(self):
        case=live.read(ROOT/'evidence/cases/us-google-general-search.json')
        today=self.today+dt.timedelta(days=31)
        task=live.choose(self.catalog,{},[case],today)
        self.assertEqual(task['case_id'],case['id'])
        task=live.choose(self.catalog,{'attempts':[{'case_id':case['id'],'date':today.isoformat()}]},[case],today)
        self.assertEqual(task['kind'],'discovery')
    def test_mismatched_scope_cannot_publish(self):
        task=live.choose(self.catalog,{},[],self.today)
        with self.assertRaisesRegex(ValueError,'scope'):
            live.validate_proposal({'status':'no-evidence','region':'US','industry':'J'},task,self.catalog,self.today,watch)
    def test_no_evidence_requires_actual_source(self):
        task=live.choose(self.catalog,{},[],self.today)
        proposal={'status':'no-evidence','region':'JP','industry':'J','note':'No compatible data found; not proof of competition.','sources':[]}
        with self.assertRaisesRegex(ValueError,'actually read'):
            live.validate_proposal(proposal,task,self.catalog,self.today,watch)
    def test_private_host_and_credentials_refused(self):
        for url in ['http://example.com','https://user:secret@example.com','https://127.0.0.1','https://example.com/?token=secret']:
            with self.assertRaises(ValueError):live.public_url(url)
    def test_source_excerpt_is_checked_before_publication(self):
        case=live.read(ROOT/'evidence/cases/au-supermarket-retailing.json')
        task={'kind':'discovery','region':'AU','industry':'G'}
        proposal={'status':'finding','region':'AU','industry':'G','case':case}
        def refuse(source):raise ValueError('Supporting excerpt absent')
        with self.assertRaisesRegex(ValueError,'excerpt absent'):
            live.validate_proposal(proposal,task,self.catalog,self.today,watch,fetch=refuse)

if __name__=='__main__':unittest.main()
