import unittest
from unittest.mock import patch, MagicMock
from src.nim_client import NIMClient

class TestNIMClient(unittest.TestCase):
    @patch("src.nim_client.requests.post")
    def test_chat_completion_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Hello, I am Googooli!"
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        client = NIMClient(api_key="fake_key")
        messages = [{"role": "user", "content": "Hi"}]
        reply = client.chat_completion(messages)

        self.assertEqual(reply.get("content"), "Hello, I am Googooli!")
        mock_post.assert_called_once()

    @patch("src.nim_client.requests.post")
    def test_chat_completion_error(self, mock_post):
        mock_post.side_effect = Exception("Connection Timeout")

        client = NIMClient(api_key="fake_key")
        with self.assertRaises(Exception):
            client.chat_completion([{"role": "user", "content": "Hi"}])

if __name__ == "__main__":
    unittest.main()
