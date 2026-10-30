import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


REPOSITORY = Path(__file__).resolve().parents[1]
SCRIPT = REPOSITORY / "scripts/ports.sh"
LSOF = shutil.which("lsof")


class PortsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="dotfiles-ports-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.rows = self.root / "listeners"
        self.rows.write_text(
            "p2000000000\ncnode worker\nf4\nn[::1]:8080\nf5\nn[::1]:8080\n"
            "p2000000001\ncpython\nf6\nn*:3000\n"
        )
        self.environment = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.defpath,
                                TEST_ROWS=str(self.rows), TEST_ROOT=str(self.root))
        self.stub("lsof", 'cat "$TEST_ROWS"; exit "${TEST_LSOF_STATUS:-0}"')
        self.stub("fzf", '''
cat > "$TEST_ROOT/table"
printf '%s\\n' "$@" > "$TEST_ROOT/fzf-args"
[ "${TEST_CANCEL:-0}" = 1 ] && exit 130
printf '%s\\n' "${TEST_KEY:-}"
sed -n '2p' "$TEST_ROOT/table"
''')
        self.stub("ps", '''
if [ "$1" = eww ]; then
  printf '%s\\n' "${TEST_PS:-node server.js}"
else
  printf '%s\\n' 'node server.js'
fi
''')
        self.stub("herdr", '''
printf '%s\\n' "$@" > "$TEST_ROOT/herdr-args"
printf '%s' "${HERDR_SOCKET_PATH:-}" > "$TEST_ROOT/herdr-socket"
''')

    def stub(self, name, body):
        executable = self.bin / name
        executable.write_text("#!/bin/sh\n" + body + "\n")
        executable.chmod(0o755)

    def run_ports(self, *arguments, input="q", **environment):
        return subprocess.run(
            ["bash", str(SCRIPT), *arguments], text=True, input=input,
            env=self.environment | environment, capture_output=True, timeout=10,
        )

    def test_list_sorts_ports_deduplicates_and_keeps_ipv6_and_command_spaces(self):
        result = self.run_ports("--list")
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(len(lines), 3)
        self.assertTrue(lines[1].startswith("3000"))
        self.assertIn("node worker", lines[2])
        self.assertIn("[::1]:8080", lines[2])
        self.assertFalse((self.root / "table").exists())

    def test_query_and_cancel(self):
        result = self.run_ports("node server", TEST_CANCEL="1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--query=node server\n", (self.root / "fzf-args").read_text())
        self.assertFalse((self.root / "herdr-args").exists())

    def test_jump_reads_target_workspace_and_socket_with_spaces(self):
        result = self.run_ports(
            TEST_KEY="ctrl-j", HERDR_SOCKET_PATH="/tmp/wrong-session.sock",
            TEST_PS="node app HERDR_WORKSPACE_ID=w7 "
                    "HERDR_SOCKET_PATH=/tmp/session with spaces.sock OTHER=value",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / "herdr-args").read_text(), "workspace\nfocus\nw7\n")
        self.assertEqual((self.root / "herdr-socket").read_text(),
                         "/tmp/session with spaces.sock")
        self.assertNotIn("OTHER=value", result.stdout)

    def test_jump_without_workspace_explains_failure(self):
        result = self.run_ports(input="j")
        self.assertEqual(result.returncode, 1)
        self.assertIn("no Herdr workspace detected", result.stderr)
        self.assertFalse((self.root / "herdr-args").exists())

    def test_empty_list_is_normal_but_lsof_errors_fail(self):
        self.rows.write_text("")
        result = self.run_ports(TEST_LSOF_STATUS="1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("No visible TCP listeners", result.stdout)
        result = self.run_ports(TEST_LSOF_STATUS="2")
        self.assertEqual(result.returncode, 2)

    def test_stale_listener_is_not_signalled(self):
        self.stub("fzf", '''
cat > "$TEST_ROOT/table"
: > "$TEST_ROWS"
printf 'ctrl-k\\n'
sed -n '2p' "$TEST_ROOT/table"
''')
        result = self.run_ports()
        self.assertEqual(result.returncode, 1)
        self.assertIn("selected listener no longer exists", result.stderr)

    @unittest.skipUnless(LSOF, "requires lsof")
    def test_stops_a_real_tcp_listener(self):
        process = subprocess.Popen(
            [sys.executable, "-u", "-c",
             'import socket,time; s=socket.socket(); s.bind(("127.0.0.1",0)); '
             's.listen(); print(s.getsockname()[1],flush=True); time.sleep(30)'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        def cleanup():
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=5)
            process.stdout.close()
            process.stderr.close()
        self.addCleanup(cleanup)
        port = process.stdout.readline().strip()
        if not port:
            error = process.stderr.read()
            if "PermissionError" in error:
                self.skipTest("sandbox does not allow binding a local TCP socket")
            self.fail(error)
        self.stub("lsof", 'exec "$TEST_LSOF" "$@" -a -p "$TEST_PID"')
        result = self.run_ports(TEST_KEY="ctrl-k", TEST_LSOF=LSOF,
                                TEST_PID=str(process.pid))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(port, (self.root / "table").read_text())
        self.assertIn("Sent SIGTERM", result.stdout)
        self.assertEqual(process.wait(timeout=5), -15)


if __name__ == "__main__":
    unittest.main()
