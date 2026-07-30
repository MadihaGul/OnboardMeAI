import os
import unittest
from unittest.mock import patch

from app.llm import GeminiProvider, get_llm_provider


class LLMProviderTests(unittest.TestCase):
    @patch.dict(os.environ, {"GOOGLE_API_KEY": "demo-key"}, clear=True)
    def test_get_llm_provider_uses_google_env(self):
        provider = get_llm_provider()
        self.assertIsInstance(provider, GeminiProvider)
        self.assertEqual(provider.api_key, "demo-key")

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "demo-key"}, clear=True)
    def test_default_model_is_lightweight(self):
        provider = get_llm_provider()
        self.assertEqual(provider.model_name, "gemini-3.6-flash")


if __name__ == "__main__":
    unittest.main()
