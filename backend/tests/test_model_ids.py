"""
Test that all OpenRouter model IDs used in the codebase are valid.

Validates against the live OpenRouter /api/v1/models endpoint.
"""
import json
import sys
import urllib.request
import unittest
from unittest.mock import patch, MagicMock

# Add parent to path so we can import the modules
sys.path.insert(0, '/home/user/proex')


class TestModelIDs(unittest.TestCase):
    """Validate model IDs against the live OpenRouter API."""

    @classmethod
    def setUpClass(cls):
        """Fetch the list of valid model IDs from OpenRouter."""
        try:
            req = urllib.request.Request('https://openrouter.ai/api/v1/models')
            resp = urllib.request.urlopen(req, timeout=15)
            data = json.loads(resp.read())
            cls.valid_models = {m['id'] for m in data.get('data', [])}
            print(f"\nFetched {len(cls.valid_models)} valid models from OpenRouter")
        except Exception as e:
            cls.valid_models = set()
            print(f"\nWARNING: Could not fetch models from OpenRouter: {e}")

    def test_llm_processor_models_are_valid(self):
        """Test that all model IDs in LLMProcessor are valid on OpenRouter."""
        self.assertTrue(len(self.valid_models) > 0, "Could not fetch models from OpenRouter API")

        from backend.app.core.llm_processor import LLMProcessor

        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test-key'}):
            processor = LLMProcessor()

        for tier, model_id in processor.models.items():
            with self.subTest(tier=tier, model_id=model_id):
                self.assertIn(
                    model_id, self.valid_models,
                    f"Model '{model_id}' (tier={tier}) is NOT a valid OpenRouter model ID"
                )
                print(f"  OK: {tier} -> {model_id}")

    def test_fallback_models_are_valid(self):
        """Test that all fallback model IDs are also valid."""
        self.assertTrue(len(self.valid_models) > 0, "Could not fetch models from OpenRouter API")

        from backend.app.core.llm_processor import LLMProcessor

        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test-key'}):
            processor = LLMProcessor()

        for primary, fallbacks in processor._fallback_models.items():
            for fb in fallbacks:
                with self.subTest(primary=primary, fallback=fb):
                    self.assertIn(
                        fb, self.valid_models,
                        f"Fallback model '{fb}' (for {primary}) is NOT valid"
                    )
                    print(f"  OK: fallback {fb} (for {primary})")

    def test_known_invalid_models_not_present(self):
        """Ensure historically problematic model IDs are not in use."""
        from backend.app.core.llm_processor import LLMProcessor

        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test-key'}):
            processor = LLMProcessor()

        invalid_models = [
            "google/gemini-2.0-flash",       # Missing version suffix
            "google/gemini-flash-1.5",       # Wrong format
            "google/gemini-exp-1206:free",   # Expired
            "anthropic/claude-3.7-sonnet",   # Never existed
            "google/gemini-2.5-pro",         # Not a valid ID
        ]

        all_used = set(processor.models.values())
        for fb_list in processor._fallback_models.values():
            all_used.update(fb_list)

        for invalid in invalid_models:
            self.assertNotIn(
                invalid, all_used,
                f"Known-invalid model '{invalid}' is still referenced in code"
            )

    def test_call_llm_fallback_on_invalid_model(self):
        """Test that _call_llm falls back when primary model returns 400."""
        from backend.app.core.llm_processor import LLMProcessor

        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test-key'}):
            processor = LLMProcessor()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"test": true}'

        call_count = 0
        def mock_create(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Error code: 400 - not a valid model ID")
            return mock_response

        processor.client = MagicMock()
        processor.client.chat.completions.create = mock_create

        result = processor._call_llm(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": "test"}]
        )

        self.assertEqual(call_count, 2, "Should have tried fallback after primary failed")
        self.assertEqual(result, mock_response)

    def test_call_llm_raises_non_model_errors(self):
        """Test that _call_llm does NOT fallback on rate limit or other errors."""
        from backend.app.core.llm_processor import LLMProcessor

        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test-key'}):
            processor = LLMProcessor()

        def mock_create(**kwargs):
            raise Exception("Error code: 429 - Rate limit exceeded")

        processor.client = MagicMock()
        processor.client.chat.completions.create = mock_create

        with self.assertRaises(Exception) as ctx:
            processor._call_llm(
                model="openai/gpt-4o-mini",
                messages=[{"role": "user", "content": "test"}]
            )
        self.assertIn("429", str(ctx.exception))


class TestLogoScraperModel(unittest.TestCase):
    """Test logo scraper model configuration."""

    @classmethod
    def setUpClass(cls):
        try:
            req = urllib.request.Request('https://openrouter.ai/api/v1/models')
            resp = urllib.request.urlopen(req, timeout=15)
            data = json.loads(resp.read())
            cls.valid_models = {m['id'] for m in data.get('data', [])}
        except Exception:
            cls.valid_models = set()

    def test_logo_scraper_model_is_valid(self):
        """Check that the model used in logo_scraper.py is valid."""
        self.assertTrue(len(self.valid_models) > 0, "Could not fetch models")

        # Read the file and extract the model ID
        with open('/home/user/proex/backend/app/core/logo_scraper.py', 'r') as f:
            content = f.read()

        import re
        matches = re.findall(r'model="([^"]+)"', content)
        for model_id in matches:
            with self.subTest(model_id=model_id):
                self.assertIn(
                    model_id, self.valid_models,
                    f"Logo scraper model '{model_id}' is NOT valid"
                )
                print(f"  OK: logo_scraper -> {model_id}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
