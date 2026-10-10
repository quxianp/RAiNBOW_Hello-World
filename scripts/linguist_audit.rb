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

stdout, stderr, status = Open3.capture3("github-linguist")
if status.exitstatus != 0
  warn "github-linguist exited #{status.exitstatus}"
  warn stderr.lines.first(15).join
  exit 1
end

buckets = Hash.new { |h, k| h = [] }
stdout.each_line do |line|
  # "path:Language (share %)"
  m = line.match(/\A(hello\/core\/[^:]+):(.+?)\s*\(\s*[\d.]+\s*%\s*\)\s*\z/)
  next unless m

  buckets[m[2].strip] << m[1]
end

payload = {
  "generated_by" => "scripts/linguist_audit.rb",
  "source" => "github-linguist CLI",
  "core_languages_detected" => buckets.size,
  "core_files_detected" => buckets.values.map(&:size).sum,
  "buckets" => buckets.sort.to_h.transform_values { |v| v.sort }
}

FileUtils.mkdir_p("logs")
File.write(File.join(root, "logs", "linguist_audit.json"),
           JSON.pretty_generate(payload))

puts "languages detected in core : #{payload['core_languages_detected']}"
puts "files detected in core     : #{payload['core_files_detected']}"

multi = payload["buckets"].reject { |_, v| v.size == 1 }
unless multi.empty?
  puts
  puts "buckets holding more than one file (these absorbed our files):"
  multi.sort_by { |_, v| -v.size }.each { |name, files| puts format("  %-34s %d", name, files.size) }
end

exit 0