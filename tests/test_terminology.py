import unittest

from rapbattle.terminology import presentation,term,heading,TERMS


class TerminologyTests(unittest.TestCase):
    def test_upstream_identity_enums_and_private_fields_are_never_rewritten(self):
        record={"id":"event-123","organizationId":"league-45","kind":"event",
                "performer":{"id":"account-1","role":"performer"},
                "score":{"numerator":99,"denominator":100},"status":"DRAFT"}
        result=presentation(record,"event")
        self.assertEqual(result["record"],record)
        self.assertIsNot(result["record"],record)
        result["record"]["performer"]["id"]="changed-view-copy"
        self.assertEqual(record["performer"]["id"],"account-1")
        self.assertEqual(result["label"],"battle")

    def test_unknown_or_markup_kinds_do_not_become_html(self):
        for kind in ("<script>alert(1)</script>","account-token","Battle",None,{}):
            with self.subTest(kind=kind),self.assertRaises(ValueError):
                heading(kind)

    def test_label_counts_do_not_accept_boolean_negative_or_fractional_values(self):
        for count in (True,-1,1.5,"2",None):
            with self.subTest(count=count),self.assertRaises(ValueError):
                term("performer",count)
        self.assertEqual(heading("stage",0),"<h2>Matches</h2>")
        self.assertEqual(heading("performer",1),"<h2>Emcee</h2>")

    def test_vocabulary_is_immutable_and_record_contract_is_explicit(self):
        with self.assertRaises(TypeError):
            TERMS["event"]=("changed","changed")
        for value in (None,[],"raw credential"):
            with self.assertRaises(ValueError):
                presentation(value,"event")


if __name__=="__main__":
    unittest.main()
