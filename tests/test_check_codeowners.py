__codeowner__ = "@Patreon/be-core"

import subprocess
from unittest.mock import Mock

from hooks.check_codeowners import main
from hooks.check_codeowners import SENTINEL_VALUE

variable_name = "__codeowner__"


def test_empty_file_fails_check(tmpdir, capsys):
    file = tmpdir.join("file.py")
    file.write_binary(b"")

    result = main(
        [f"--variable-name={variable_name}", file.strpath]
    )
    out, _ = capsys.readouterr()

    assert result == 1
    assert f"missing {variable_name}: {file.strpath}" in out


def test_multiple_files(tmpdir, capsys):
    file_1 = tmpdir.join("file.py")
    file_1.write_binary(b"")
    file_2 = tmpdir.join("file2.py")
    file_2.write_binary(b"")

    result = main(
        [
            f"--variable-name={variable_name}",
            file_1.strpath,
            file_2.strpath,
        ]
    )
    out, _ = capsys.readouterr()

    assert result == 2
    assert file_1.strpath in out
    assert file_2.strpath in out


def test_codeowner_inherited_from_init(tmpdir, capsys):
    file = tmpdir.join("file.py")
    file.write_binary(b"")
    module_init = tmpdir.join("__init__.py")
    module_init.write(f'{variable_name} = "test-user"')

    result = main(
        [f"--variable-name={variable_name}", file.strpath]
    )

    assert result == 0


def test_codeowner_not_inherited_from_empty_init(
    tmpdir, capsys
):
    file = tmpdir.join("file.py")
    file.write_binary(b"")
    module_init = tmpdir.join("__init__.py")
    module_init.write(
        f'{variable_name} = "{SENTINEL_VALUE}"\n"""\nsome random docstring\n"""'
    )

    result = main(
        [f"--variable-name={variable_name}", file.strpath]
    )

    assert result == 1


def test_sentinel_codeowner_value_no_error(tmpdir, capsys):
    file = tmpdir.join("file.py")
    file.write(f'__codeowner__ = "{SENTINEL_VALUE}"')

    result = main(
        [f"--variable-name={variable_name}", file.strpath]
    )

    assert result == 0


def test_codeowner_inherited_from_nested_init(tmpdir, capsys):
    file = (
        tmpdir.mkdir("sub").mkdir("nested").join("file.py")
    )
    file.write_binary(b"")
    module_init = tmpdir.join("__init__.py")
    module_init.write(f'{variable_name} = "test-user"')

    result = main(
        [f"--variable-name={variable_name}", file.strpath]
    )

    assert result == 0


def test_codeowner_not_first_line(tmpdir, capsys):
    file = tmpdir.join("file.py")
    file.write(
        f'"""\nsome random docstring\n"""\n{variable_name} = "nitro"\n'
    )

    result = main(
        [f"--variable-name={variable_name}", file.strpath]
    )

    assert result == 0


def test_codeowner_multiple_teams(tmpdir, capsys):
    file = tmpdir.join("file.py")
    file.write(
        f'{variable_name} = "@Patreon/workers, @Patreon/supreme"\n'
    )

    result = main(
        [f"--variable-name={variable_name}", file.strpath]
    )

    assert result == 0


def test_autofix(tmpdir, capsys, monkeypatch):
    file = tmpdir.join("file.py")
    contents = b""
    file.write_binary(contents)

    expected_codeowner = "@Patreon/tooling"
    monkeypatch.setattr(
        "subprocess.check_output",
        Mock(return_value=expected_codeowner),
    )

    result = main(
        [
            f"--variable-name={variable_name}",
            "--auto-fix",
            file.strpath,
        ]
    )

    assert result == 0
    assert (
        file.read_text(encoding="utf-8")
        == f'{variable_name} = "{expected_codeowner}"\n\n'
    )


def test_autofix_no_team_set(tmpdir, capsys, monkeypatch):
    file_1 = tmpdir.join("file.py")
    file_1.write_binary(b"")
    file_2 = tmpdir.join("file2.py")
    file_2.write_binary(b"")

    monkeypatch.setattr(
        "subprocess.check_output",
        Mock(
            side_effect=subprocess.CalledProcessError(1, "")
        ),
    )

    result = main(
        [
            f"--variable-name={variable_name}",
            "--auto-fix",
            file_1.strpath,
            file_2.strpath,
        ]
    )
    out, _ = capsys.readouterr()

    assert result == 2
    assert (
        "Unable to fix attribution: missing `user.team`"
        in out
    )
