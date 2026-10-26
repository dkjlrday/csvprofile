import csv
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "csvprofile.py"


def run(*args):
    # 显式指定 encoding：中文 Windows 的默认编码是 GBK，
    # 而子进程输出的是 UTF-8，text=True 不指定编码会解码失败。
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


def test_missing_file():
    result = run("nope.csv")
    assert result.returncode == 2, result
    assert "找不到文件" in result.stderr, result.stderr


def test_profile_basic():
    data = HERE / "_sample.csv"
    data.write_text(
        "name,age,city,active\n"
        "ada,36,Beijing,yes\n"
        "lin,28,Shanghai,no\n"
        "zhou,,Beijing,yes\n",
        encoding="utf-8",
    )
    result = run(str(data), "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    by_name = {c["name"]: c for c in payload}
    assert by_name["age"]["type"] == "integer", by_name["age"]
    assert by_name["city"]["type"] == "string", by_name["city"]
    assert by_name["name"]["missing"] == 0
    data.unlink()


def test_placeholder_free():
    text = (HERE / "README.md").read_text(encoding="utf-8")
    assert "<your-" not in text.lower()
    assert "TODO" not in text


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
    print("all tests passed")
