"""Read public Cast help only; never generate/import/read a wallet or secret."""
import json
import subprocess


def main():
    rows = []
    for command in (("wallet", "new", "--help"), ("wallet", "address", "--help")):
        argv = ["/opt/zzz-keeper-staging/bin/cast", *command]
        result = subprocess.run(argv, capture_output=True, text=True, timeout=10,
                                env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "COLUMNS": "100"})
        assert len(result.stdout) <= 64 * 1024 and len(result.stderr) <= 4096
        rows.append({"argv": argv, "exit_code": result.returncode,
                     "stdout": result.stdout, "stderr": result.stderr})
    print(json.dumps({"schema": 1, "scope": "public_help_no_wallet_action", "rows": rows}, indent=2))


if __name__ == "__main__":
    main()
