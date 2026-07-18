import importlib.util
from pathlib import Path
import pickle
import tempfile
import unittest


MODULE_PATH = Path(__file__).parents[1] / "herbs" / "persistence.py"
SPEC = importlib.util.spec_from_file_location("persistence", MODULE_PATH)
persistence = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(persistence)


class LegacyPickleTests(unittest.TestCase):
    def test_success_and_failure_return_the_same_shape(self):
        with tempfile.TemporaryDirectory() as folder:
            valid_path = Path(folder) / "valid.pkl"
            invalid_path = Path(folder) / "invalid.pkl"
            with valid_path.open("wb") as stream:
                pickle.dump({"answer": 42}, stream)
            invalid_path.write_bytes(b"not a pickle")

            data, error = persistence.load_legacy_pickle(valid_path)
            self.assertEqual(data, {"answer": 42})
            self.assertIsNone(error)

            data, error = persistence.load_legacy_pickle(invalid_path)
            self.assertIsNone(data)
            self.assertIsInstance(error, str)

    def test_missing_file_returns_an_error_tuple(self):
        data, error = persistence.load_legacy_pickle("does-not-exist.pkl")
        self.assertIsNone(data)
        self.assertIn("Unable to read file", error)


if __name__ == "__main__":
    unittest.main()
