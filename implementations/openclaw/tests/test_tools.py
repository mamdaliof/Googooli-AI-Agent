import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock, PropertyMock
from src.tools import execute_tool

class TestTools(unittest.TestCase):
    def test_file_operations(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test.txt")
            write_res = execute_tool("write_file", {"path": file_path, "content": "Hello Tools!"})
            self.assertIn("Successfully wrote", write_res)
            
            read_res = execute_tool("read_file", {"path": file_path})
            self.assertEqual(read_res, "Hello Tools!")

            list_res = execute_tool("list_directory", {"path": temp_dir})
            self.assertEqual(list_res, "test.txt")

    @patch("src.tools.requests.post")
    @patch("src.config.Config.tavily_api_key", new_callable=PropertyMock)
    def test_google_web_search_ddg(self, mock_tavily_key, mock_post):
        mock_tavily_key.return_value = None
        mock_response = MagicMock()
        mock_response.text = '<td><a href="http://test.url" class="result-link">Test Title</a></td><td class="result-snippet">This is test snippet</td>'
        mock_post.return_value = mock_response

        res = execute_tool("google_web_search", {"query": "test"})
        self.assertIn("http://test.url", res)

    @patch("src.tools.requests.post")
    @patch("src.config.Config.tavily_api_key", new_callable=PropertyMock)
    def test_google_web_search_tavily(self, mock_tavily_key, mock_post):
        mock_tavily_key.return_value = "mock-key"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "title": "Tavily Test",
                    "url": "http://tavily.test.url",
                    "content": "Tavily content"
                }
            ]
        }
        mock_post.return_value = mock_response

        res = execute_tool("google_web_search", {"query": "test"})
        self.assertIn("http://tavily.test.url", res)

    @patch("src.tools.subprocess.run")
    def test_notebooklm_tools(self, mock_run):
        mock_res = MagicMock()
        mock_res.stdout = "Mocked NotebookLM Output"
        mock_res.stderr = ""
        mock_res.returncode = 0
        mock_run.return_value = mock_res

        res_list = execute_tool("notebooklm_list", {})
        self.assertIn("Mocked NotebookLM Output", res_list)

        res_create = execute_tool("notebooklm_create", {"title": "Test Title"})
        self.assertIn("Mocked NotebookLM Output", res_create)

        res_ask = execute_tool("notebooklm_ask", {"notebook_id": "123", "question": "What's up?"})
        self.assertIn("Mocked NotebookLM Output", res_ask)

        res_add = execute_tool("notebooklm_add_source", {
            "notebook_id": "123",
            "source_path_or_url": "test.pdf",
            "source_type": "file"
        })
        self.assertIn("Mocked NotebookLM Output", res_add)

    @patch("src.tools.subprocess.run")
    def test_context7_tools(self, mock_run):
        mock_res = MagicMock()
        mock_res.stdout = "Mocked Context7 Output"
        mock_res.stderr = ""
        mock_res.returncode = 0
        mock_run.return_value = mock_res

        res_query = execute_tool("context7_query", {"project_identifier": "org/repo", "query": "docs"})
        self.assertIn("Mocked Context7 Output", res_query)

        res_search = execute_tool("context7_search", {"term": "query"})
        self.assertIn("Mocked Context7 Output", res_search)

    @patch("src.tools.requests.get")
    def test_download_file(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b"%PDF Mock PDF Content"]
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as temp_dir:
            dest = os.path.join(temp_dir, "test.pdf")
            res = execute_tool("download_file", {"url": "http://example.com/test.pdf", "destination_path": dest})
            self.assertIn("Successfully downloaded", res)
            self.assertTrue(os.path.exists(dest))
            with open(dest, "rb") as f:
                self.assertEqual(f.read(), b"%PDF Mock PDF Content")

if __name__ == "__main__":
    unittest.main()
