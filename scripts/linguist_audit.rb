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
#
# Compatibility notes, all learned the hard way in CI:
#   * `require "github-linguist"` raises LoadError even when the gem is
#     installed; the entry point that resolves is `linguist`.
#   * Depending on which file loaded, the namespace is either `Linguist` or
#     `GitHub::Linguist`, so both are probed.

require "json"
require "fileutils"

begin
  require "github-linguist"
rescue LoadError
  require "linguist"
end

LIB = if defined?(GitHub::Linguist)
        GitHub::Linguist
      elsif defined?(Linguist)
        Linguist
      else
        warn "no Linguist namespace after requiring the gem"
        exit 2
      end

root = ARGV[0] || File.expand_path("..", __dir__)
Dir.chdir(root)

# Repository.new(repo_root, commit_sha, api_endpoint = nil) -- the commit is
# mandatory in this version; "HEAD" resolves the checked-out tree, which is what
# the working copy is.
repo = LIB::Repository.new(root, ARGV[1] || "HEAD")

langs = if repo.respond_to?(:rb_languages)
          repo.rb_languages
        elsif repo.respond_to?(:languages)
          repo.languages
        else
          warn "Repository exposes neither rb_languages nor languages"
          exit 2
        end

buckets = Hash.new { |h, k| h = [] }
langs.each do |language, blob|
  next if language.nil?
  path = blob.respond_to?(:path) ? blob.path : nil
  next if path.nil?
  next unless path.start_with?("hello/core/")
  buckets[language.name] << path
end

payload = {
  "generated_by" => "scripts/linguist_audit.rb",
  "namespace" => LIB.name,
  "core_languages_detected" => buckets.size,
  "core_files_detected" => buckets.values.map(&:size).sum,
  "buckets" => buckets.sort.to_h.transform_values { |v| v.sort }
}

FileUtils.mkdir_p("logs")
File.write(File.join(root, "logs", "linguist_audit.json"),
           JSON.pretty_generate(payload))

puts "namespace                  : #{LIB.name}"
puts "languages detected in core : #{payload['core_languages_detected']}"
puts "files detected in core     : #{payload['core_files_detected']}"

multi = payload["buckets"].select { |_, v| v.size > 1 }
unless multi.empty?
  puts
  puts "buckets holding more than one file (these absorbed our files):"
  multi.sort_by { |_, v| -v.size }.each { |name, files| puts format("  %-34s %d", name, files.size) }
end

exit 0