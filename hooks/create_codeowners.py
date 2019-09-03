__codeowner__ = "@Patreon/be-core"

import argparse
import itertools
import os
import re
import sys
from typing import Generator
from typing import Iterable
from typing import Match
from typing import Pattern
from typing import Tuple

from .util import FAIL
from .util import PASS
from .util import cmd_output

CODEOWNERS_DELIMITER = "# END\n"


def file_owner(
    file_path: str, author_regex: Pattern[str]
) -> Generator[Tuple[str, Match[str]], None, None]:
    """
    For the given file, yields the file_path, code owner if declared
    """
    with open(file_path, errors="ignore") as file:
        for line in file:
            match = author_regex.search(line)
            if match:
                yield file_path, match.group(1)
                break


def get_all_files() -> Iterable[str]:
    """
    Get a list of all files managed by git
    """
    all_git_files = cmd_output(
        "git", "ls-files"
    ).splitlines()
    return itertools.filterfalse(
        os.path.isdir, all_git_files
    )


def execute(args):
    """
    For each file managed by Git, if it contains the regex pattern, append the author to the codeowners file
    """
    # TODO create codeowners file if not exists?
    with open(args.codeowners_path) as codeowners_file:
        try:
            manual_entries, _ = codeowners_file.read().split(
                CODEOWNERS_DELIMITER
            )
        except ValueError:
            print(
                f'{args.codeowners_path} missing delimiter "{CODEOWNERS_DELIMITER}", did you remove it?'
            )
            return FAIL

    regex = re.compile(args.regex_pattern)
    with open(args.codeowners_path, "w+") as codeowners_file:
        codeowners_file.write(manual_entries + CODEOWNERS_DELIMITER)
        for file in get_all_files():
            for file_path, owners in file_owner(
                file, regex
            ):
                # if initializer has declaration, assume owner wants ownership over whole package
                file_path = file_path.replace(
                    "__init__.py", "**/*.py"
                )
                codeowners_file.write(
                    f"{file_path} {owners}\n"
                )

    return PASS


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--codeowners-path",
        help="Path to the CODEOWNERS file.",
        required=True,
    )
    parser.add_argument(
        "--regex-pattern",
        help="Regex with single capture group used to get a file's owner(s) from an attribution.",
        required=True,
    )

    return execute(parser.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
