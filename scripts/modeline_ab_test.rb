#!/usr/bin/env ruby
# frozen_string_literal: true

# Do our per-file Linguist modelines help or hurt?
#
#   ruby scripts/modeline_ab_test.rb
#
# Measures github-linguist's language count twice on the same checkout:
#
#   A  as committed            (modelines present)
#   B  modelines removed       (same bytes, same file sizes, only the modeline
#                               line deleted and the gap padded with spaces)
#
# Because the byte totals are held constant, the only variable is how Linguist
# classifies each file. Any difference in the language set is caused by the
# modelines, not by the balancing.
#
# Why this matters: `hello/core/html+erb/hello.erb` carries
#   # -*- mode: html+erb -*-
# and Linguist's Strategy::Modeline resolves the mode through
# Language.find_by_alias. `.html` is claimed by both HTML and Ecmarkup, and
# `.erb`/`.ecr`/`.phtml`/`.cshtml` are all HTML-adjacent, so a modeline that
# resolves to the wrong language actively *creates* a fold rather than fixing
# one. This measures which way it goes.

require "json"
require "open3"
require "set"

ROOT = ARGV[0] || File.expand_path("..", __dir__)
Dir.chdir(ROOT)

LINE_RE = /-\*-/

def breakdown
  out, err, status = Open3.capture3("github-linguist")
  unless status.success?
    warn "github-linguist exited #{status.exitstatus}"
    warn err.lines.first(10).join
    exit 1
  end
  out.lines.filter_map do |l|
    m = l.match(/\A\s*([\d.]+)\s*%\s+(\d+)\s+(\S.*?)\s*\z/)
    next unless m

    { "language" => m[3].strip, "bytes" => m[2].to_i }
  end
end

before = breakdown
puts "A (as committed)      : #{before.length} languages, " \
     "#{before.sum { |b| b['bytes'] }} counted bytes"

changed = 0
Dir.glob("hello/core/**/*").each do |path|
  next unless File.file?(path)

  raw = File.binread(path)
  next unless raw.include?("-*-")

  kept = raw.lines.reject { |l| l.include?(LINE_RE) }.join
  next if kept.bytesize == raw.bytesize

  # Pad back to the exact original size so byte shares cannot move.
  File.binwrite(path, kept + (" " * (raw.bytesize - kept.bytesize)))
  changed += 1
end
puts "modelines stripped from #{changed} files (sizes preserved)"

after = breakdown
puts "B (modelines removed) : #{after.length} languages, " \
     "#{after.sum { |b| b['bytes'] }} counted bytes"

set_a = before.map { |b| b["language"] }.to_set
set_b = after.map { |b| b["language"] }.to_set

puts
puts "languages only WITH modelines (#{(set_a - set_b).size}):"
puts "  #{(set_a - set_b).to_a.sort.first(40).join(', ')}" unless (set_a - set_b).empty?
puts
puts "languages only WITHOUT modelines (#{(set_b - set_a).size}):"
puts "  #{(set_b - set_a).to_a.sort.first(40).join(', ')}" unless (set_b - set_a).empty?

payload = {
  "generated_by" => "scripts/modeline_ab_test.rb",
  "with_modelines" => { "languages" => before.length,
                        "bytes" => before.sum { |b| b["bytes"] } },
  "without_modelines" => { "languages" => after.length,
                           "bytes" => after.sum { |b| b["bytes"] } },
  "only_with_modelines" => (set_a - set_b).to_a.sort,
  "only_without_modelines" => (set_b - set_a).to_a.sort
}
File.write("logs/modeline_ab.json", JSON.pretty_generate(payload))

# Restore, so the job's workspace is left as it was checked out.
system("git checkout -- hello/core > /dev/null 2>&1")
puts
puts "verdict: modelines " \
     "#{before.length > after.length ? 'HELP' : (before.length == after.length ? 'are neutral' : 'HURT')}" \
     " (#{before.length} vs #{after.length} languages)"

exit 0