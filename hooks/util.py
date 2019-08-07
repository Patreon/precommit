import subprocess
from typing import Optional

PASS = 0
FAIL = 1


def cmd_output(*cmd) -> Optional[str]:
    """
    Run command with arguments and return its output
    :param cmd: A string, or a sequence of program arguments.
    :return: The standard output (None if not captured)
    """
    return subprocess.check_output(cmd, encoding='utf-8')
