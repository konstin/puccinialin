from io import StringIO
from unittest import TestCase
from unittest.mock import patch

from puccinialin._target import get_triple


class GetTripleTest(TestCase):
    def test_pypy_uses_multiarch_for_target(self):
        config_vars = {
            "SOABI": "pypy311-pp73",
            "MULTIARCH": "x86_64-linux-gnu",
        }

        with patch(
            "puccinialin._target.sysconfig.get_config_var",
            side_effect=config_vars.get,
        ):
            target = get_triple(StringIO())

        self.assertEqual(target, "x86_64-unknown-linux-gnu")
