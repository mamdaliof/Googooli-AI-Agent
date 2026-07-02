import unittest
from unittest.mock import patch, MagicMock
from src.googooli_client import GoogooliClient

class TestGoogooliClient(unittest.TestCase):
    @patch("src.googooli_client.requests.get")
    def test_query_context_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"context": "Obsidian note context details."}
        mock_get.return_value = mock_response

        client = GoogooliClient(api_url="http://fake-api", api_key="fake_key")
        result = client.query_context("neural network")

        self.assertEqual(result, "Obsidian note context details.")
        mock_get.assert_called_once()

    @patch("src.googooli_client.requests.get")
    def test_query_context_failure(self, mock_get):
        mock_get.side_effect = Exception("HTTP 500 Server Error")

        client = GoogooliClient(api_url="http://fake-api", api_key="fake_key")
        result = client.query_context("neural network")

        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()
