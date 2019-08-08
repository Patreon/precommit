from os import path

from unittest.mock import Mock

from hooks.create_codeowners import CODEOWNERS_DELIMITER
from hooks.create_codeowners import main
from hooks.util import FAIL
from hooks.util import PASS

regex_pattern = "--regex-pattern=__codeowner__\\s*=\\s*['\"]([\\S\\s]+)['\"]"


def create_file(tmpdir, filename, contents=""):
    file = tmpdir.join(filename)
    file.write(contents)
    return file


def test_delimiter_missing(tmpdir, capsys):
    codeowners_file = create_file(tmpdir, "CODEOWNERS")

    result = main(
        [
            f"--codeowners-path={codeowners_file.strpath}",
            regex_pattern,
        ]
    )
    out, _ = capsys.readouterr()

    assert result == FAIL
    assert "missing delimiter" in out


def test_preserves_contents_above_delimiter(tmpdir):
    codeowners_file = create_file(
        tmpdir,
        "CODEOWNERS",
        f"""
        path/to/file @Aesop
        path/to/file @Frog
        path/to/file @Ox
        {CODEOWNERS_DELIMITER}
        path/to/file @TownMouse
    """,
    )

    result = main(
        [
            f"--codeowners-path={codeowners_file.strpath}",
            regex_pattern,
        ]
    )

    assert result == PASS
    assert (
        """
        path/to/file @Aesop
        path/to/file @Frog
        path/to/file @Ox"""
        in codeowners_file.read()
    )
    assert (
        "path/to/file @TownMouse"
        not in codeowners_file.read()
    )


def test_includes_attributed_files(tmpdir, monkeypatch):
    codeowners_file = create_file(
        tmpdir, "CODEOWNERS", CODEOWNERS_DELIMITER
    )
    source_file_with_attribution = create_file(
        tmpdir,
        "a.py",
        '__codeowner__ = "@Patreon/bigbadwolf"',
    )
    source_file_without_attribution = create_file(
        tmpdir, "b.py", "import os"
    )

    monkeypatch.setattr(
        "subprocess.check_output",
        Mock(
            return_value="\n".join(
                [
                    source_file_with_attribution.strpath,
                    source_file_without_attribution.strpath,
                ]
            )
        ),
    )

    result = main(
        [
            f"--codeowners-path={codeowners_file.strpath}",
            regex_pattern,
        ]
    )

    assert result == PASS
    _, generated_entries = codeowners_file.read().split(
        CODEOWNERS_DELIMITER
    )
    assert (
        generated_entries
        == f"{source_file_with_attribution.strpath} @Patreon/bigbadwolf\n"
    )


def test_attribution_for_initializer(tmpdir, monkeypatch):
    init = create_file(
        tmpdir,
        "__init__.py",
        '__codeowner__ = "@Patreon/team"',
    )
    source_file_with_attribution = create_file(
        tmpdir,
        "a.py",
        '__codeowner__ = "@Patreon/bigbadwolf, @Patreon/littlered"',
    )
    codeowners_file = create_file(
        tmpdir, "CODEOWNER", CODEOWNERS_DELIMITER
    )

    monkeypatch.setattr(
        "subprocess.check_output",
        Mock(
            return_value="\n".join(
                [
                    init.strpath,
                    source_file_with_attribution.strpath,
                ]
            )
        ),
    )

    result = main(
        [
            f"--codeowners-path={codeowners_file.strpath}",
            regex_pattern,
        ]
    )

    assert result == PASS
    _, generated_entries = codeowners_file.read().split(
        CODEOWNERS_DELIMITER
    )
    assert (
        generated_entries
        == f"{path.dirname(init.strpath)}/ @Patreon/team\n{source_file_with_attribution.strpath} @Patreon/bigbadwolf, @Patreon/littlered\n"
    )
