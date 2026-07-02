import unittest
import os
import tempfile
from src.config import Config

class TestConfig(unittest.TestCase):
    def test_load_from_env_file(self):
        # Create a temporary env file
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_env:
            temp_env.write("NVIDIA_API_KEY=test_nvidia_key\n")
            temp_env.write("NVIDIA_MODEL_NAME=test_model\n")
            temp_env.write("# Comment line\n")
            temp_env_name = temp_env.name

        try:
            config = Config(env_path=temp_env_name)
            self.assertEqual(config.nvidia_api_key, "test_nvidia_key")
            self.assertEqual(config.nvidia_model_name, "test_model")
        finally:
            os.remove(temp_env_name)

    def test_system_env_priority(self):
        os.environ["NVIDIA_API_KEY"] = "sys_key"
        try:
            config = Config(env_path="non_existent_file")
            self.assertEqual(config.nvidia_api_key, "sys_key")
        finally:
            del os.environ["NVIDIA_API_KEY"]

if __name__ == "__main__":
    unittest.main()
