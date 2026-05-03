#!/usr/bin/env bash
# Verifies sqlite-vec ABI compatibility.
# sqlite-vec's precompiled linux-x64 binary was built against SQLite 3.45.x.
# System sqlite < 3.45 will silently fail to register vec0 functions.
#
# We use pysqlite3-binary (a Python wheel that bundles its own sqlite),
# so this script verifies that path works rather than the system sqlite.

set -euo pipefail

echo "System sqlite version:"
sqlite3 --version || { echo "  sqlite3 not installed (OK — we use pysqlite3-binary)"; }

echo
echo "Python pysqlite3 version:"
python3 -c "
import pysqlite3 as sqlite3
print(f'  pysqlite3.sqlite_version: {sqlite3.sqlite_version}')
assert tuple(int(x) for x in sqlite3.sqlite_version.split('.')) >= (3, 45, 0), \
    f'pysqlite3 sqlite < 3.45.0 — sqlite-vec will not work'
print('  OK: pysqlite3 sqlite >= 3.45.0')
" || { echo "  FAIL: install with 'uv sync'"; exit 1; }

echo
echo "sqlite-vec extension load test:"
python3 -c "
import pysqlite3 as sqlite3
import sqlite_vec
conn = sqlite3.connect(':memory:')
conn.enable_load_extension(True)
sqlite_vec.load(conn)
row = conn.execute('SELECT vec_version()').fetchone()
print(f'  sqlite-vec version: {row[0]}')
print('  OK: sqlite-vec loaded successfully')
" || { echo "  FAIL: sqlite-vec did not load"; exit 1; }

echo
echo "All checks passed."
