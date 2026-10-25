#!/usr/bin/env python3
"""csvprofile —— 读一份 CSV，告诉你每列到底是什么样子。

不做数据清洗，只做"体检"：列类型猜测、缺失率、唯一值数量、取值分布。

用法:
    python csvprofile.py data.csv
    python csvprofile.py data.csv --top 5
    python csvprofile.py data.csv --json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

MAX_VALUES = 100_000  # 超过这个行数就只统计前 N 行，避免在大文件上卡死


@dataclass
class Column:
    name: str
    total: int = 0
    missing: int = 0
    values: Counter = field(default_factory=Counter)
    numeric: int = 0
    integer: int = 0
    boolish: int = 0
    dateish: int = 0

    @property
    def present(self) -> int:
        return self.total - self.missing

    def guess_type(self) -> str:
        if self.present == 0:
            return "empty"
        if self.integer == self.present:
            return "integer"
        if self.numeric == self.present:
            return "number"
        if self.boolish == self.present:
            return "boolean"
        if self.dateish == self.present:
            return "date"
        return "string"

    def top(self, n: int) -> list[tuple[str, int]]:
        return self.values.most_common(n)

    def as_dict(self, top_n: int) -> dict:
        return {
            "name": self.name,
            "type": self.guess_type(),
            "total": self.total,
            "missing": self.missing,
            "missing_rate": round(self.missing / self.total, 4) if self.total else 0.0,
            "unique": len(self.values),
            "top": [{"value": v, "count": c} for v, c in self.top(top_n)],
        }


TRUE_WORDS = {"true", "false", "yes", "no", "y", "n", "0", "1"}
DATE_HINT_CHARS = set("-/:年月日")


def _looks_numeric(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True


def _looks_integer(value: str) -> bool:
    try:
        int(value)
    except ValueError:
        return False
    return True


def _looks_date(value: str) -> bool:
    if len(value) < 6:
        return False
    if not any(ch in DATE_HINT_CHARS for ch in value):
        return False
    digits = sum(ch.isdigit() for ch in value)
    return digits >= 4


def profile(path: Path, top_n: int = 3) -> list[Column]:
    columns: dict[str, Column] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return []
        for name in reader.fieldnames:
            columns[name] = Column(name=name)
        for index, row in enumerate(reader):
            if index >= MAX_VALUES:
                break
            for name, column in columns.items():
                raw = row.get(name)
                value = "" if raw is None else raw.strip()
                column.total += 1
                if not value:
                    column.missing += 1
                    continue
                column.values[value] += 1
                if _looks_integer(value):
                    column.integer += 1
                    column.numeric += 1
                elif _looks_numeric(value):
                    column.numeric += 1
                elif value.lower() in TRUE_WORDS:
                    column.boolish += 1
                elif _looks_date(value):
                    column.dateish += 1
    return list(columns.values())


def render(columns: list[Column], top_n: int) -> str:
    if not columns:
        return "没有读到任何列。"
    width = max(len(c.name) for c in columns)
    lines = []
    for column in columns:
        rate = (column.missing / column.total * 100) if column.total else 0.0
        lines.append(
            f"{column.name.ljust(width)}  {column.guess_type():<8}"
            f"  缺失 {column.missing:>6}/{column.total:<6} ({rate:5.1f}%)"
            f"  唯一 {len(column.values):>6}"
        )
        for value, count in column.top(top_n):
            lines.append(f"{'':{width}}    · {value[:40]!r} × {count}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="csvprofile",
        description="读取 CSV，输出每列的类型猜测、缺失率与高频取值",
    )
    parser.add_argument("path", help="CSV 文件路径")
    parser.add_argument("--top", type=int, default=3, help="每列展示的高频取值个数（默认 3）")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出")
    args = parser.parse_args(argv)

    path = Path(args.path)
    if not path.exists():
        print(f"csvprofile: 找不到文件 {path}", file=sys.stderr)
        return 2

    columns = profile(path, top_n=max(1, args.top))
    if args.json:
        print(json.dumps([c.as_dict(max(1, args.top)) for c in columns], ensure_ascii=False, indent=2))
    else:
        print(render(columns, max(1, args.top)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
