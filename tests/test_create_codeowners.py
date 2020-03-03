__codeowner__ = "@Patreon/be-core"

import shutil
import tempfile
import unittest
from unittest.mock import patch

from hooks.create_codeowners import CODEOWNERS_DELIMITER
from hooks.create_codeowners import main
from hooks.util import FAIL
from hooks.util import PASS


class TestCreateCodeowners(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.codeowner_declaration = "__codeowner__"
        self.codeowners_file = tempfile.NamedTemporaryFile(dir=self.temp_dir, delete=False)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir)

    @staticmethod
    def write_file(file, contents: str):
        file.seek(0)
        file.write(contents.encode())
        file.seek(0)

    @staticmethod
    def read_file(file) -> str:
        return file.read().decode("utf-8")

    def execute_hook(self):
        return main(
            [
                f"--codeowners-path={self.codeowners_file.name}",
                rf"--regex-pattern={self.codeowner_declaration}\s*=\s*['\"]([\S\s]+)['\"]",
            ]
        )

    @patch("builtins.print")
    def test_verify_throws_if_codeowner_is_missing_delimiter(self, mock_print):
        self.write_file(self.codeowners_file, "")

        result = self.execute_hook()

        self.assertEqual(result, FAIL)

        (first_arg,), kwargs = mock_print.call_args
        self.assertIn("missing delimiter", first_arg)
        mock_print.assert_called_once()

    @patch("hooks.create_codeowners.get_all_files", return_value=[])
    def test_does_not_overwrite_content_above_delimiter(self, mock_get_all_files):
        self.write_file(
            self.codeowners_file,
            (
                "content above the delimiter should not be erased\n"
                f"{CODEOWNERS_DELIMITER}"
                "content below should be erased\n"
            ),
        )

        result = self.execute_hook()

        self.assertEqual(result, PASS)
        self.assertIn("above", self.codeowners_file.read().decode("utf-8"))
        self.assertNotIn("below", self.read_file(self.codeowners_file))

    @patch("hooks.create_codeowners.get_all_files")
    def test_writes_files_with_codeowners(self, mock_get_all_files):
        file_with_owner = tempfile.NamedTemporaryFile(dir=self.temp_dir)
        file_without_owner = tempfile.NamedTemporaryFile(dir=self.temp_dir)
        self.write_file(self.codeowners_file, CODEOWNERS_DELIMITER)
        self.write_file(
            file_with_owner, f'{self.codeowner_declaration} = "@Patreon/bigbadwolf"\n'
        )
        self.write_file(file_without_owner, "import os\n")
        mock_get_all_files.return_value = [
            file_with_owner.name,
            file_without_owner.name,
        ]

        result = self.execute_hook()

        self.assertEqual(result, PASS)
        self.assertIn(file_with_owner.name, self.read_file(self.codeowners_file))
        self.assertNotIn(file_without_owner.name, self.read_file(self.codeowners_file))

    @patch("hooks.create_codeowners.get_all_files")
    def test_files_with_spaces_are_escaped(self, mock_get_all_files):
        file_with_spaces = tempfile.NamedTemporaryFile(prefix="this file has spaces")
        self.write_file(self.codeowners_file, CODEOWNERS_DELIMITER)
        self.write_file(
            file_with_spaces, f'{self.codeowner_declaration} = "@Patreon/bigbadwolf"\n'
        )
        mock_get_all_files.return_value = [file_with_spaces.name]

        result = self.execute_hook()

        self.assertEqual(result, PASS)
        self.assertIn(
            "this\\ file\\ has\\ spaces", self.read_file(self.codeowners_file)
        )

    @patch("hooks.create_codeowners.get_all_files")
    def test_owner_in_initializer_strips_filename(self, mock_get_all_files):
        init_file_with_owner = tempfile.NamedTemporaryFile(
            dir=self.temp_dir, suffix="__init__.py"
        )
        self.write_file(self.codeowners_file, CODEOWNERS_DELIMITER)
        self.write_file(
            init_file_with_owner,
            f'{self.codeowner_declaration} = "@Patreon/bigbadwolf"\n',
        )

        mock_get_all_files.return_value = [init_file_with_owner.name]
        result = self.execute_hook()

        self.assertEqual(result, PASS)
        self.assertIn(
            init_file_with_owner.name.replace("__init__.py", "**/*.py"),
            self.read_file(self.codeowners_file),
        )
        self.assertNotIn(
            init_file_with_owner.name, self.read_file(self.codeowners_file)
        )

    @patch("hooks.create_codeowners.get_all_files", side_effect=Exception("whatever"))
    def test_reports_error_on_error(self, mock_get_all_files):
        self.write_file(self.codeowners_file, CODEOWNERS_DELIMITER)

        result = self.execute_hook()

        assert result == FAIL
