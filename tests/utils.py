import os
import unittest


def skipUnlessPathExists(path):
    return unittest.skipUnless(
        os.path.exists(path),
        (
            f'File or directory at path "{path}" '
            f"used in test is not available in the system"
        ),
    )
