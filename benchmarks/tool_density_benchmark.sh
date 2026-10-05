#!/usr/bin/env bash

# Directory for temporary files
TMPDIR=$(mktemp -d)

# Create a tiny dummy file for view_file demonstration
echo "dummy" > "$TMPDIR/dummy.txt"

# List of commands to execute (25 total). Using simple native commands.
commands=(
  "true"
  "echo hello"
  "ls -1 ."
  "cat $TMPDIR/dummy.txt"
  "date"
  "uname -a"
  "pwd"
  "whoami"
  "uptime"
  "df -h ."
  "du -sh $TMPDIR"
  "arch"
  "printf 'test'"
  "head -n 1 $TMPDIR/dummy.txt"
  "tail -n 1 $TMPDIR/dummy.txt"
  "sleep 0.01"
  "true"
  "echo benchmark"
  "ls $TMPDIR"
  "cat $TMPDIR/dummy.txt"
  "date +%s"
  "echo end"
  "false || true"   # always succeed
  "printf 'done'"
  "uname -r"
)

# JSON array initialization
json_output="["
first=true

for cmd in "${commands[@]}"; do
  start_ms=$(date +%s%3N)
  # Execute the command, capturing any output (ignored)
  eval $cmd >/dev/null 2>&1
  end_ms=$(date +%s%3N)
  latency=$((end_ms - start_ms))
  # Build JSON object
  if $first; then
    first=false
  else
    json_output+=" ,"
  fi
  json_output+=$(printf '{"command":"%s","start_ms":%s,"end_ms":%s,"latency_ms":%s}' "$cmd" "$start_ms" "$end_ms" "$latency")
done

json_output+="]"

# Write results to artifact file (will be created as an artifact)
output_path="/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/benchmarks/tool_density_results.json"
printf "%s" "$json_output" > "$output_path"

# Clean up temporary directory
rm -rf "$TMPDIR"

echo "Benchmark completed. Results written to $output_path"
