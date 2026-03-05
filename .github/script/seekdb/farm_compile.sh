#!/usr/bin/env bash
# Farm compile: build observer / obproxy in workspace.
# Expects: WORKSPACE, SEEKDB_TASK_DIR, PACKAGE_TYPE (debug|release), REPO=server
set -e

cd "$WORKSPACE"
# Use repo build.sh; debug or release from PACKAGE_TYPE
build_type="${PACKAGE_TYPE:-debug}"
if [[ -x "$WORKSPACE/build.sh" ]]; then
  # CI 下关闭 parser 缓存，避免首次运行读不到 _MD5 报错
  bash "$WORKSPACE/build.sh" "$build_type" --init --make -DNEED_PARSER_CACHE=OFF
else
  echo "[farm_compile.sh] No build.sh in $WORKSPACE, skip."
fi
