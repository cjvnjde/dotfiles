#!/usr/bin/env bash

parallel_init() {
  parallel_pids=()
  parallel_labels=()
  parallel_head=0
  parallel_tail=0
  parallel_failed=0
  trap parallel_cleanup EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM
}

parallel_reap() {
  local status=0
  wait "${parallel_pids[$parallel_head]}" || status=$?
  if [ "$status" -ne 0 ]; then
    printf '[ERR ] %s failed (exit %s).\n' "${parallel_labels[$parallel_head]}" "$status" >&2
    parallel_failed=1
  fi
  unset 'parallel_pids[parallel_head]' 'parallel_labels[parallel_head]'
  parallel_head=$((parallel_head + 1))
}

parallel_run() {
  local label="$1"
  local monitor_enabled=0
  shift

  # Give each worker a process group so cancellation also reaches its commands.
  case "$-" in *m*) monitor_enabled=1 ;; esac
  set -m
  (
    set +m
    trap - EXIT INT TERM
    "$@"
  ) <&0 &
  parallel_pids[parallel_tail]=$!
  parallel_labels[parallel_tail]="$label"
  parallel_tail=$((parallel_tail + 1))
  if [ "$monitor_enabled" -eq 0 ]; then
    set +m
  fi
}

parallel_wait() {
  while [ "$parallel_head" -lt "$parallel_tail" ]; do
    parallel_reap
  done
  parallel_head=0
  parallel_tail=0
  [ "$parallel_failed" -eq 0 ]
}

parallel_cleanup() {
  local index
  for ((index = parallel_head; index < parallel_tail; index++)); do
    kill -TERM -- "-${parallel_pids[$index]}" 2>/dev/null || true
  done
  for ((index = parallel_head; index < parallel_tail; index++)); do
    wait "${parallel_pids[$index]}" 2>/dev/null || true
  done
  parallel_head=0
  parallel_tail=0
}
