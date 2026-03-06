#!/usr/bin/env bash
# Compile: 与 scripts/farm_compile.sh run_new_oceanbase() 对齐（REPO=server + cmake）。
# 不调用 frame.sh/main()，避免 Jenkins 依赖（dmidecode、/etc/hosts、git clone）。
# 流程：build.sh $BUILD_TARGET --init --make，再打包 observer/obproxy 到 SEEKDB_TASK_DIR。
# Required env: GITHUB_WORKSPACE, SEEKDB_TASK_DIR
# Optional: RELEASE_MODE, FORWARDING_HOST, MAKE, MAKE_ARGS
set -e

WORKSPACE="${GITHUB_WORKSPACE:?}"
TASK_DIR="${SEEKDB_TASK_DIR:?}"

# 与 farm_compile.sh 一致
export GITHUB_WORKSPACE="$WORKSPACE"
export SEEKDB_TASK_DIR="$TASK_DIR"
export REPO="server"
export PACKAGE_TYPE="${RELEASE_MODE:+release}"
export PACKAGE_TYPE="${PACKAGE_TYPE:-debug}"
export CREATE_AGENTSERVER=0
export CREATE_LIBOBSERVER_SO=0
export ENABLE_LIBOBLOG=0
export MAKE="${MAKE:-make}"
export MAKE_ARGS="${MAKE_ARGS:--j32}"
export TARGET="observer"
export PATH="$WORKSPACE/deps/3rd/usr/local/oceanbase/devtools/bin:$PATH"
cd "$WORKSPACE"
mkdir -p "$TASK_DIR"


BUILD_TARGET="${PACKAGE_TYPE:-debug}"
set +e
if [[ -x "$WORKSPACE/build.sh" ]]; then
  sh -x build.sh $BUILD_TARGET --init || return
  compile_ret=$?
  cd build_* || return
  start=$(date +%s)
  time $MAKE $MAKE_ARGS $TARGET
  ret=$?
else
  echo "[compile.sh] No build.sh, skip."
  compile_ret=0
fi
set -e

# 产物落到 build_* 或当前目录，打包 observer/obproxy 为 zst 并拷贝到任务目录（对应 farm 的 mv $BINARY $BINARY_PATH）
for binary in observer obproxy; do
  for base in . build_debug build_release build; do
    if [[ -f "$WORKSPACE/$base/$binary" ]]; then
      cp -f "$WORKSPACE/$base/$binary" "$WORKSPACE/$binary" 2>/dev/null || true
      break
    fi
  done
  if [[ -f "$WORKSPACE/$binary" ]]; then
    command -v zstd >/dev/null 2>&1 && zstd -f "$WORKSPACE/$binary" || true
    [[ -f "$WORKSPACE/$binary.zst" ]] && cp -f "$WORKSPACE/$binary.zst" "$TASK_DIR/" || true
  fi
done

exit "$compile_ret"
