import asyncio
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from ddump.api.dump import Dump
from ddump.api.dump import Dump__start__end


class Api:
    def stock_basic(self, status):
        return pd.DataFrame([{"ts_code": "000001.SZ", "status": status}])

    def daily(self, start_date, end_date):
        return pd.DataFrame([{"trade_date": start_date, "close": 1.0}])


class ApiDumpStorageTest(unittest.TestCase):
    def test_local_dump_storage_still_works(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "stock_basic"
            dump = Dump(Api(), root, ["status"])
            dump.set_parameters("stock_basic", status="L")

            self.assertFalse(dump.exists(timeout=0))

            asyncio.run(dump.download(use_await=False, kw=["status"]))
            dump.save()

            self.assertTrue((root / "L.parquet").exists())
            self.assertTrue(dump.exists(timeout=0))
            self.assertEqual(
                dump.load().to_dict("records"),
                [{"ts_code": "000001.SZ", "status": "L"}],
            )

    def test_remote_dump_storage_uses_fsspec_url(self):
        fsspec = self._require_fsspec()
        fs = fsspec.filesystem("memory")
        self._remove(fs, "/ddump-test/basic")

        dump = Dump(Api(), "memory://ddump-test/basic", ["status"])
        dump.set_parameters("stock_basic", status="L")

        self.assertEqual(dump.file_path, "memory://ddump-test/basic/L.parquet")
        self.assertFalse(dump.exists(timeout=0))

        asyncio.run(dump.download(use_await=False, kw=["status"]))
        dump.save()

        self.assertTrue(dump.exists(timeout=0))
        self.assertEqual(
            dump.load().to_dict("records"),
            [{"ts_code": "000001.SZ", "status": "L"}],
        )

    def test_remote_range_exists_uses_object_listing(self):
        fsspec = self._require_fsspec()
        fs = fsspec.filesystem("memory")
        self._remove(fs, "/ddump-test/daily")

        existing = Dump__start__end(Api(), "memory://ddump-test/daily", "start_date", "end_date")
        existing.set_parameters("daily", start_date="20240101", end_date="20240131")
        asyncio.run(existing.download(use_await=False, kw=["start_date", "end_date"]))
        existing.save()

        bounded = Dump__start__end(Api(), "memory://ddump-test/daily", "start_date", "end_date")
        bounded.set_parameters("daily", start_date="20240115", end_date="20240115")

        self.assertTrue(bounded.exists(file_timeout=3600, data_timeout=86400 * 10))

    def _require_fsspec(self):
        try:
            import fsspec
        except ImportError:
            self.skipTest("fsspec is not installed")
        return fsspec

    def _remove(self, fs, path):
        if fs.exists(path):
            fs.rm(path, recursive=True)


if __name__ == "__main__":
    unittest.main()
