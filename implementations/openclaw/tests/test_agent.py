import unittest
from unittest.mock import patch, MagicMock
from src.config import Config
from src.agent import OpenClawAgent

class TestOpenClawAgent(unittest.TestCase):
    @patch("src.agent.NIMClient.chat_completion")
    @patch("src.agent.GoogooliClient.query_context")
    def test_handle_message_with_context(self, mock_query, mock_chat):
        mock_query.return_value = "Mocked Obsidian context"
        mock_chat.return_value = {"role": "assistant", "content": "Mocked AI Response"}

        config = Config(env_path="non_existent")
        agent = OpenClawAgent(config)
        reply = agent.handle_message("test query")

        self.assertEqual(reply, "Mocked AI Response")
        mock_query.assert_called_once_with("test query")
        mock_chat.assert_called_once()
        
        messages = mock_chat.call_args[0][0]
        self.assertTrue(any("Mocked Obsidian context" in msg["content"] for msg in messages))

    @patch("src.agent.NIMClient.chat_completion")
    @patch("src.agent.GoogooliClient.query_context")
    def test_handle_message_no_context(self, mock_query, mock_chat):
        mock_query.return_value = None
        mock_chat.return_value = {"role": "assistant", "content": "Mocked AI Response"}

        config = Config(env_path="non_existent")
        agent = OpenClawAgent(config)
        reply = agent.handle_message("test query")

        self.assertEqual(reply, "Mocked AI Response")
        mock_query.assert_called_once_with("test query")
        mock_chat.assert_called_once()

        messages = mock_chat.call_args[0][0]
        # Check system instructions are present, but not context
        self.assertTrue(any("Googooli" in msg["content"] for msg in messages if msg["role"] == "system"))
        self.assertEqual(len([msg for msg in messages if msg["role"] == "system"]), 1)

if __name__ == "__main__":
    unittest.main()
