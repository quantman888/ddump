import tempfile
import unittest
from pathlib import Path

import pandas as pd


class ParquetTest(unittest.TestCase):
    def test_read_parquet_directory_with_empty_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "b"
            root.mkdir()

            dr = pd.date_range(start="2022-01-01", end="2022-01-10", freq="D")
            df = pd.DataFrame(index=dr)
            df["A"] = pd.to_datetime("today")
            df["B"] = 1.0
            df["C"] = "a"
            df["D"] = 2

            df.head(1).to_parquet(root / "0.parquet")
            df.head(0).to_parquet(root / "1.parquet")
            df.head(0).to_parquet(root / "2.parquet")
            df.to_parquet(root / "3.parquet")

            loaded = pd.read_parquet(root)

            self.assertFalse(loaded.empty)


if __name__ == "__main__":
    unittest.main()
