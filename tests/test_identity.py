import json
import subprocess
import unittest
from unittest.mock import patch

from rapbattle.engine_contract import ENGINE_REVISION
from rapbattle.identity import NodeEngine, IdentityError, EngineUnavailable, Principal


class NodeEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine=NodeEngine("/fixture/engine")
        self.token="Bearer "+"a"*43

    def result(self,value,returncode=0):
        return subprocess.CompletedProcess([],returncode,json.dumps(value),"private diagnostic")

    def test_exact_revision_and_scoped_identity_required(self):
        payload={"revision":ENGINE_REVISION,"principal":{
            "accountId":"account","sessionId":"session","organizationId":"ny"}}
        with patch("rapbattle.identity.subprocess.run",return_value=self.result(payload)) as run:
            self.assertEqual(self.engine.authorize(self.token,"ny","content.view_private"),Principal("account","session","ny"))
            args,kwargs=run.call_args
            self.assertNotIn(self.token," ".join(args[0]))
            self.assertIn(self.token,kwargs["input"])
            self.assertEqual(kwargs["timeout"],5)
            self.assertEqual(json.loads(kwargs["input"])["organizationId"],"ny")

    def test_unknown_revision_or_cross_tenant_principal_never_authorized(self):
        values=[{"revision":"main","principal":{}},
                {"revision":ENGINE_REVISION,"principal":{"accountId":"a","sessionId":"s","organizationId":"la"}},
                {"revision":ENGINE_REVISION,"principal":{"accountId":"","sessionId":"s","organizationId":"ny"}},
                {"revision":ENGINE_REVISION,"principal":None}]
        for value in values:
            with self.subTest(value=value),patch("rapbattle.identity.subprocess.run",return_value=self.result(value)):
                with self.assertRaises(EngineUnavailable):
                    self.engine.authorize(self.token,"ny","content.view_private")

    def test_auth_errors_are_distinct_from_service_failure(self):
        for code in ("expired","revoked","forbidden","invalid","missing"):
            with self.subTest(code=code),patch("rapbattle.identity.subprocess.run",return_value=self.result({"revision":ENGINE_REVISION,"error":code})):
                with self.assertRaises(IdentityError) as error:
                    self.engine.authorize(self.token,"ny","content.view_private")
                self.assertEqual(error.exception.code,code)

    def test_process_failure_and_timeout_do_not_leak_diagnostics(self):
        for outcome in (self.result({},1),subprocess.CompletedProcess([],0,"not-json token-secret", "db-secret"),
                        subprocess.CompletedProcess([],0,"x"*9000,"db-secret")):
            with patch("rapbattle.identity.subprocess.run",return_value=outcome):
                with self.assertRaises(EngineUnavailable) as error:
                    self.engine.authorize(self.token,"ny","content.view_private")
                self.assertNotIn("secret",str(error.exception))
        with patch("rapbattle.identity.subprocess.run",side_effect=subprocess.TimeoutExpired("node",5)):
            self.assertFalse(self.engine.ready())

    def test_invalid_requests_never_invoke_subprocess(self):
        with patch("rapbattle.identity.subprocess.run") as run:
            for token in (None,"Bearer short","Basic anything","Bearer "+"a"*43+"\n"):
                with self.assertRaises(IdentityError):
                    self.engine.authorize(token,"ny","content.view_private")
            with self.assertRaises(IdentityError):
                self.engine.authorize(self.token,"ny","platform.manage")
            run.assert_not_called()

    def test_unready_bridge_fails_closed_without_fixture_checkout(self):
        # Real subprocess invocation: no engine checkout, no database, no credentials.
        missing=NodeEngine("/nonexistent-rap-fixture-checkout")
        self.assertFalse(missing.ready())
        with self.assertRaises(EngineUnavailable):
            missing.authorize(self.token,"ny","content.view_private")
