import unittest

from rapbattle.engine_contract import EngineBinding, ENGINE_REVISION


class EngineContractTests(unittest.TestCase):
    def test_https_origin_and_exact_revision(self):
        binding = EngineBinding("https://engine.example.test/", ENGINE_REVISION)
        self.assertEqual(binding.health_url, "https://engine.example.test/api/health")
        with self.assertRaises(ValueError):
            EngineBinding("https://engine.example.test", "main")

    def test_unsafe_origins_fail_without_network_access(self):
        for origin in (
            "http://engine.example.test", "https://user:password@engine.example.test",
            "https://engine.example.test/api", "https://engine.example.test?token=fixture",
            "https://engine.example.test/#fragment", "https://engine.example.test:8080",
            "https://engine.example.test:invalid", "https://engine.example.test\\evil",
            "https://engine.example.test\n", "https:///missing-host",
        ):
            with self.subTest(origin=origin), self.assertRaises(ValueError):
                EngineBinding(origin, ENGINE_REVISION)

    def test_public_health_or_domain_lookup_does_not_prove_session(self):
        binding = EngineBinding("https://engine.example.test", ENGINE_REVISION)
        self.assertEqual(binding.readiness(None, False), {
            "ready": False,
            "reasons": ["engine_revision_unverified", "engine_session_unverified"],
        })
        self.assertFalse(binding.readiness(ENGINE_REVISION, False)["ready"])
        self.assertFalse(binding.readiness(None, True)["ready"])
        self.assertFalse(binding.readiness(ENGINE_REVISION, "true")["ready"])
        self.assertTrue(binding.readiness(ENGINE_REVISION, True)["ready"])


if __name__ == "__main__":
    unittest.main()
