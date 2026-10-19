import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from rapbattle.store import Store, Conflict


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/"store.sqlite"
        self.store=Store(self.path)
        self.store.add_league("ny","org-ny","NY fixture",synthetic=True)

    def tearDown(self):
        self.temp.cleanup()

    def test_scoped_update_cannot_move_record_to_another_tenant(self):
        with self.assertRaises(Conflict):
            self.store.update_settings("ny","org-la","Hijack","UTC",1)
        self.assertEqual(self.store.league("ny")["name"],"NY fixture")
        self.assertEqual(self.store.league("ny")["organization_id"],"org-ny")

    def test_simultaneous_writes_have_one_winner_without_lost_update(self):
        def edit(name):
            try:
                self.store.update_settings("ny","org-ny",name,"UTC",1)
                return "updated"
            except Conflict:
                return "conflict"
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(edit,["Writer A","Writer B"]))
        self.assertCountEqual(results,["updated","conflict"])
        self.assertEqual(self.store.league("ny")["version"],2)

    def test_schema_survives_reopen_and_future_version_is_rejected(self):
        self.assertTrue(Store(self.path).healthy())
        with sqlite3.connect(self.path) as db:
            db.execute("PRAGMA user_version=2")
        with self.assertRaisesRegex(ValueError,"Unsupported"):
            Store(self.path)

    def test_unknown_league_and_injection_are_not_found(self):
        self.assertIsNone(self.store.league("' OR 1=1 --"))
        for slug in ("../ny","NY","ny/other","ny?tenant=la"):
            with self.assertRaises(ValueError):
                self.store.add_league(slug,"org-other","Other")
        self.assertEqual(self.store.league("ny")["name"],"NY fixture")

    def test_duplicate_slug_or_engine_organization_fails_without_overwrite(self):
        for slug,org in (("ny","new-org"),("other","org-ny")):
            with self.assertRaises(sqlite3.IntegrityError):
                self.store.add_league(slug,org,"Attempt")
        self.assertEqual(self.store.league("ny")["name"],"NY fixture")
