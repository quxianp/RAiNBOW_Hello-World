#!/usr/bin/env ruby
# frozen_string_literal: true

# Audit how GitHub Linguist actually classifies every file in hello/core/.
#
#   ruby scripts/linguist_audit.rb [repo_root]
#
# Writes logs/linguist_audit.json and prints a short summary to stdout.
#
# Why this exists: GET /repos/.../languages reports 631 language names for 694
# core files, and 64 of our configured names are absent while HTML, INI, Python,
# Shell, JavaScript, C, Java and friends each report several *more* files than we
# have for them. Those extra files are ours, misclassified. This runs Linguist's
# own code -- the same engine GitHub runs -- so the answer is authoritative
# rather than inferred from byte arithmetic.

require "json"
require "fileutils"

begin
  # The gem is named `github-linguist`, but in recent releases the entry point
  # is lib/linguist.rb: requiring the gem name raises
  #   cannot load such file -- github-linguist (LoadError)
  # even though `gem list` shows it installed. Try both.
  require "github-linguist"
rescue LoadError
  require "linguist"
end

root = ARGV[0] || File.expand_path("..", __dir__)
Dir.chdir(root)

repo = GitHub::Linguist::Repository.new(root)

buckets = Hash.new { |h, k| h = [] }
repo.rb_languages.each do |language, blob|
  path = blob.respond_to?(:path) ? blob.path : nil
  next if path.nil?
  next unless path.start_with?("hello/core/")
  buckets[language.name] << path
end

payload = {
  "generated_by" => "scripts/linguist_audit.rb",
  "core_languages_detected" => buckets.size,
  "core_files_detected" => buckets.values.map(&:size).sum,
  "buckets" => buckets.sort.to_h.transform_values { |v| v.sort }
}

FileUtils.mkdir_p("logs")
File.write(File.join(root, "logs", "linguist_audit.json"),
           JSON.pretty_generate(payload))

puts "languages detected in hello/core : #{payload['core_languages_detected']}"
puts "files detected in hello/core    : #{payload['core_files_detected']}"

multi = payload["buckets"].select { |_, v| v.size > 1 }
unless multi.empty?
  puts "\nbuckets holding more than one file (these absorbed our files):"
  multi.sort_by { |_, v| -v.size }.each { |name, files| puts format("  %-32s %d", name, files.size) }
end

exit 0