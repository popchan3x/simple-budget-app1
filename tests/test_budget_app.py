import json
import os
import tempfile
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "budget_app.py"


class BudgetAppTests(unittest.TestCase):
    def setUp(self):
        self.original_cwd = Path.cwd()
        self.tmp = tempfile.TemporaryDirectory()
        os.chdir(self.tmp.name)
        self.data_file = Path("budget_data.json")
        self.seed = {"records": [
            {"date": "2026-10-02", "category": "Food", "amount": -100},
            {"date": "2026-10-02", "category": "Salary", "amount": 500},
        ]}
        self.data_file.write_text(json.dumps(self.seed), encoding="utf-8")
        self.app = AppTest.from_file(str(APP)).run()
        self.assertFalse(self.app.exception)

    def tearDown(self):
        os.chdir(self.original_cwd)
        self.tmp.cleanup()

    def records(self):
        return json.loads(self.data_file.read_text(encoding="utf-8"))["records"]

    def test_unconfirmed_click_and_confirmation_alone_preserve_records(self):
        before = self.data_file.read_bytes()
        self.app.sidebar.button[0].click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.data_file.read_bytes(), before)
        self.app.sidebar.checkbox[0].check().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.data_file.read_bytes(), before)

    def test_confirmed_delete_refreshes_ui_resets_confirmation_and_persists(self):
        self.app.sidebar.checkbox[0].check().run()
        self.app.sidebar.button[0].click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.records(), [])
        self.assertEqual(len(self.app.dataframe), 0)
        self.assertEqual(len(self.app.subheader), 0)
        self.assertFalse(self.app.sidebar.checkbox[0].value)
        self.assertEqual(len(self.app.sidebar.success), 1)
        restarted = AppTest.from_file(str(APP)).run()
        self.assertFalse(restarted.exception)
        self.assertEqual(len(restarted.dataframe), 0)
        self.assertEqual(len(restarted.info), 1)
        # An old confirmation must not authorize deletion of new records.
        self.data_file.write_text(json.dumps(self.seed), encoding="utf-8")
        self.app.run()
        self.app.sidebar.button[0].click().run()
        self.assertEqual(self.records(), self.seed["records"])

    def test_empty_delete_and_add_income_expense(self):
        self.data_file.write_text('{"records": []}', encoding="utf-8")
        self.app.run()
        self.app.sidebar.checkbox[0].check().run()
        self.app.sidebar.button[0].click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.records(), [])
        self.app.text_input[0].set_value("Food")
        self.app.number_input[0].set_value(120.0)
        self.app.button[0].click().run()
        self.assertEqual(self.records()[-1]["amount"], -120)
        self.app.text_input[0].set_value("Salary")
        self.app.number_input[0].set_value(500.0)
        self.app.checkbox[0].check()
        self.app.button[0].click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.records()[-1]["amount"], 500)
        self.assertIn("380", self.app.subheader[0].value)
        restarted = AppTest.from_file(str(APP)).run()
        self.assertFalse(restarted.exception)
        self.assertEqual(len(restarted.dataframe[0].value), 2)
        self.assertIn("380", restarted.subheader[0].value)


if __name__ == "__main__":
    unittest.main()
