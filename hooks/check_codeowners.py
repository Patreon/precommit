__codeowner__ = "@Patreon/be-core"

import argparse
import os
import re
import subprocess
import sys
from functools import lru_cache
from identify.identify import tags_from_path
from typing import Pattern

from .util import cmd_output

# An empty string can be used as a code owner to bypass check, could be modifiable as an argument
SENTINEL_VALUE = ''


@lru_cache()
def has_initializer_pattern(
    directory: str, pattern: Pattern
) -> bool:
    """
    Returns true if the directory initializer has any *non-empty* matches, false otherwise
    """
    module_init_path = os.path.join(directory, "__init__.py")

    if os.path.exists(module_init_path):
        with open(module_init_path) as module_initializer:
            match = re.search(pattern, module_initializer.read())
            # Return false if attribution is sentinel value
            return match.group(1).strip() != SENTINEL_VALUE if match else False
    else:
        return False


def execute(args):
    """
    If any modules do not have a code owner attribution, returns non-zero exit code.
    """
    errors = []
    owner = None

    if args.auto_fix:
        try:
            owner = cmd_output("git", "config", "user.team").strip()
        except subprocess.CalledProcessError:
            print(
                "Unable to fix attribution: missing `user.team` in git config. "
                "See teams listed here https://github.com/orgs/Patreon/teams. To set your team: \n"
                "git config --global user.team @Patreon/<your-team>\n"
            )
            args.auto_fix = False

    pattern = re.compile(
        f"^{args.variable_name}"
        + r"[^\w\d]=\s*['\"]((?:.+|"
        + re.escape(SENTINEL_VALUE)  # Match either at least one character, or sentinel value
        + r"))['\"]",
        re.MULTILINE,
    )

    files = args.filenames
    if args.since_master:
        try:
            merge_base = cmd_output("git", "merge-base", "--fork-point", "origin/master").strip()
            all_changes = cmd_output("git", "diff", "--name-only", merge_base).splitlines()
            py_changes = filter(lambda file: "python" in tags_from_path(file), all_changes)
            files = (open(file, mode="r+", encoding="utf-8") for file in py_changes)
        except Exception as e:
            print(e)
            pass

    for file in files:
        file_contents = file.read()

        try:
            found_match = bool(re.findall(pattern, file_contents))
            if not found_match:
                # Check inheritance from parent packages' initializers
                parents = []
                filename = file.name
                for _ in range(filename.count('/')):
                    filename, _ = os.path.split(filename)
                    parents.append(filename)

                found_match = any([has_initializer_pattern(directory, pattern) for directory in parents])
                if not found_match and args.auto_fix:
                    file.seek(0)
                    file.write(f'{args.variable_name} = "{owner}"\n\n')
                    file.write(file_contents)
                    file.truncate()
                    file.close()

                elif not found_match:
                    errors.append(f"missing {args.variable_name}: {file.name}")
        finally:
            file.close()

    for error in errors:
        print(error)

    return len(errors)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "filenames",
        nargs="*",
        metavar="FILE",
        type=argparse.FileType(mode="r+", encoding="utf-8"),
        help="Filenames to be checked.",
    )
    parser.add_argument(
        "-f",
        "--auto-fix",
        action="store_true",
        help="Automatically add codeowner from git config, default False",
    )
    parser.add_argument(
        "--variable-name",
        help="Variable name that is assigned the codeowner",
    )
    parser.add_argument(
        "--since-master",
        action="store_true",
        help="Ignore the files in this commit, run on all files since origin/master, default False",
    )

    return execute(parser.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
