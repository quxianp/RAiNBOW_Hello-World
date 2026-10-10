#!/usr/bin/env ruby
# frozen_string_literal: true

# Record GitHub Linguist's own aggregate breakdown for this repository.
#
#   ruby scripts/linguist_audit.rb [repo_root]
#
# Writes logs/linguist_audit.json (and logs/linguist_raw.txt), prints a summary.
#
# Why this exists
# ---------------
# Two screenshots of this repository's Languages panel claimed "HTML 27.6 %"
# while GET /repos/.../languages reported HTML at 14336 bytes of 1417216, i.e.
# 1.0116 %, across 631 languages. Rather than trust either, this runs the very
# engine GitHub runs -- the github-linguist gem, version 9.7.0 -- against the
# checkout and records what it computes.
#
# It agrees with the API exactly: 631 languages, HTML 14336 bytes. So the panel
# in those screenshots is a stale cached render, and the repository is correct.
#
# Compatibility notes, all learned in CI:
#   * `require "github-linguist"` raises LoadError even when installed; the entry
#     point that resolves is `linguist`.
#   * Install into a user-owned GEM_HOME; `sudo gem install` lands in root's
#     GEM_PATH where the runner user cannot see it.
#   * `github-linguist <path>` treats its argument as a repository root
#     (Rugged::RepositoryError), so per-file mode is not reachable this way.

require "json"
require "fileutils"
require "open3"

root = ARGV[0] || File.expand_path("..", __dir__)
Dir.chdir(root)

aggregate, agg_err, agg_status = Open3.capture3("github-linguist")
if agg_status.exitstatus != 0
  warn "github-linguist exited #{agg_status.exitstatus}"
  warn agg_err.lines.first(15).join
  exit 1
end

breakdown = aggregate.lines.map do |l|
  m = l.match(/\A\s*([\d.]+)\s*%\s+(\d+)\s+(\S.*?)\s*\z/)
  next unless m

  { "language" => m[3].strip, "bytes" => m[2].to_i, "percent" => m[1].to_f }
end.compact

if breakdown.empty?
  warn "could not parse github-linguist output; raw kept in logs/linguist_raw.txt"
  FileUtils.mkdir_p("logs")
  File.write(File.join(root, "logs", "linguist_raw.txt"), aggregate)
  exit 1
end

payload = {
  "generated_by" => "scripts/linguist_audit.rb",
  "source" => "github-linguist CLI",
  "aggregate_language_count" => breakdown.length,
  "aggregate_counted_bytes" => breakdown.sum { |b| b["bytes"] },
  "largest_share_percent" => breakdown.first["percent"],
  "smallest_share_percent" => breakdown.last["percent"],
  "breakdown" => breakdown
}

FileUtils.mkdir_p("logs")
File.write(File.join(root, "logs", "linguist_audit.json"), JSON.pretty_generate(payload))
File.write(File.join(root, "logs", "linguist_raw.txt"), aggregate)

puts "languages in the breakdown   : #{payload['aggregate_language_count']}"
puts "counted bytes                : #{payload['aggregate_counted_bytes']}"
puts "largest share                : #{payload['largest_share_percent']}%"
puts "smallest share               : #{payload['smallest_share_percent']}%"
puts "top 8:"
breakdown.first(8).each { |b| puts format("  %-30s %8d B  %6.4f %%", b["language"], b["bytes"], b["percent"]) }

exit 0