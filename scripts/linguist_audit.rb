#!/usr/bin/env ruby
# frozen_string_literal: true

# Audit how GitHub Linguist classifies every file in hello/core/.
#
#   ruby scripts/linguist_audit.rb [repo_root]
#
# Writes logs/linguist_audit.json and prints a summary.
#
# Why this exists: GET /repos/.../languages reports 631 language names for 694
# core files, and 64 of our configured names are absent while HTML, INI, Python,
# Shell, JavaScript, C, Java and friends each report several *more* files than we
# have for them. Those extra files are ours, misclassified.
#
# Implementation note: this shells out to the `github-linguist` CLI rather than
# using the library API. The library route kept failing on internal setup --
# `Linguist::Repository` needs a commit, and `Source::Rugged#lookup` then
# demands a Rugged repository it has not been given (four CI runs lost to that).
# The CLI wires all of that up itself and prints the mapping we actually want:
#
#     hello/core/fish/hello.fish:Fish (0.14 %)

require "json"
require "fileutils"
require "open3"

root = ARGV[0] || File.expand_path("..", __dir__)
Dir.chdir(root)

aggregate, agg_err, agg_status = Open3.capture3("github-linguist")
if agg_status.exitstatus != 0
  warn "github-linguist (aggregate) exited #{agg_status.exitstatus}"
  warn agg_err.lines.first(15).join
  exit 1
end

# With no arguments the CLI prints the aggregate breakdown
# ("1.01%   14336      HTML"). Given a path it prints one line per file, which
# is what we actually want.
stdout, stderr, status = Open3.capture3("github-linguist", "hello/core")
if status.exitstatus != 0
  warn "github-linguist (per-file) exited #{status.exitstatus}"
  warn stderr.lines.first(15).join
  exit 1
end

breakdown = aggregate.lines.map do |l|
  m = l.match(/\A\s*([\d.]+)\s*%\s+(\d+)\s+(\S.*?)\s*\z/)
  next unless m

  { "language" => m[3].strip, "bytes" => m[2].to_i, "percent" => m[1].to_f }
end.compact

core_mentions = stdout.lines.count { |l| l.include?("hello/core/") }
puts "raw stdout lines            : #{stdout.lines.count}"
puts "lines mentioning hello/core : #{core_mentions}"
if core_mentions.zero?
  puts "WARNING: the CLI never mentioned hello/core; first lines it did print:"
  stdout.lines.first(5).each { |l| puts "  #{l.rstrip}" }
  puts "stderr head:"
  stderr.lines.first(5).each { |l| puts "  #{l.rstrip}" }
end

buckets = Hash.new { |h, k| h = [] }
unparsed = []

stdout.each_line do |line|
  l = line.rstrip
  next if l.strip.empty?

  path = nil
  lang = nil

  # Layout A: "path:Language (12.34 %)"
  if (m = l.match(%r{\A(.+?):([^()]+?)\s*\(\s*[\d.]+\s*%\s*\)\s*\z}))
    path = m[1].strip
    lang = m[2].strip
  # Layout B: "12.34 %  Language<pad>path"
  elsif (m = l.match(/\A\s*([\d.]+)\s*%\s+(\S.*?)\s{2,}(\S.*)\s*\z/))
    lang = m[2].strip
    path = m[3].strip
  end

  if path && lang && path.start_with?("hello/core/")
    buckets[lang] << path
  elsif l.include?("hello/core/")
    unparsed << l
  end
end

# Always keep the raw output: it is the ground truth for parsing and costs
# little, and it is what makes a future format change diagnosable.
FileUtils.mkdir_p("logs")
File.write(File.join(root, "logs", "linguist_raw.txt"), stdout)

payload = {
  "generated_by" => "scripts/linguist_audit.rb",
  "source" => "github-linguist CLI",
  "aggregate_language_count" => breakdown.length,
  "aggregate_counted_bytes" => breakdown.sum { |b| b["bytes"] },
  "core_languages_detected" => buckets.size,
  "core_files_detected" => buckets.values.map(&:size).sum,
  "breakdown" => breakdown,
  "buckets" => buckets.sort.to_h.transform_values { |v| v.sort }
}

FileUtils.mkdir_p("logs")
File.write(File.join(root, "logs", "linguist_audit.json"),
           JSON.pretty_generate(payload))

puts "aggregate languages        : #{payload['aggregate_language_count']}"
puts "aggregate counted bytes    : #{payload['aggregate_counted_bytes']}"
puts "languages detected in core : #{payload['core_languages_detected']}"
puts "files detected in core     : #{payload['core_files_detected']}"

unless unparsed.empty?
  puts
  puts "WARNING: #{unparsed.length} core lines did not match a known layout; first 5:"
  unparsed.first(5).each { |l| puts "  #{l}" }
  puts "raw output kept in logs/linguist_raw.txt"
end

multi = payload["buckets"].reject { |_, v| v.size == 1 }
unless multi.empty?
  puts
  puts "buckets holding more than one file (these absorbed our files):"
  multi.sort_by { |_, v| -v.size }.each { |name, files| puts format("  %-34s %d", name, files.size) }
end

exit 0