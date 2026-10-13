# VHS tape -- RAiNBOW_Hello-World
#
#   vhs demo.tape            -> assets/hello-world.gif
#
# scripts/record_demo.sh drives this and then transcodes to MP4.
#
# NOTE: the command is invoked as `bash run.sh`, not `./run.sh`. An earlier
# revision used `./run.sh` and every recorded GIF ended on
#   bash: ./run.sh: Permission denied
# because the file was stored in git with mode 100644. run.sh now carries the
# executable bit (see scripts/validate_delivery.py, which fails the build if it
# ever regresses), but invoking bash explicitly makes the recording immune to the
# whole class of problem.
#
# Every Sleep below is set by measurement, not by taste. scripts/measure_motion.py
# reports frame-to-frame coverage for the recorded GIF and
# scripts/check_demo_motion.py refuses to publish one that does not move. When
# those two disagree with a number written here, the number here is the one that
# is wrong.

Output assets/hello-world.gif

Set Shell "bash"
Set FontSize 20
Set Width 1200
Set Height 800
Set PlaybackSpeed 1.0
Set Theme '{"background":"#0d1117","foreground":"#ffffff","accent":"#58a6ff"}'
# 0.05 s per character is ~2 s to type the show's command line. That typing is
# the single largest block of low-motion time in the take, so it is fast enough
# to read and slow enough to follow.
Set TypingSpeed 0.05

# A cold open: the hue sweep runs before anything else, so the video begins with
# colour and movement rather than a blank screen and a blinking cursor.
#
# The three flags are all load-bearing. `--force-animation` overrides
# rainbow.py's isatty() check, which otherwise emits a single static frame when
# stdout is not a terminal -- and a recorder's stdout is not a terminal, which is
# how the earlier attempt at this produced ten seconds of one frame repeated (see
# logs/ERRORS.log, E31).
Type "bash scripts/rainbow.py --sweep 26 --sweep-only --force-animation"
Enter
Sleep 2

# The show. `--max 12` keeps the roll call short so the finale stays on screen.
#
# FORCE_HOLD=1 because the closing hold is guarded on `[ -t 1 ]`, false whenever
# stdout is a pipe -- and a recorder drives run.sh exactly that way.
#
# The sleep is the show's ~16 s plus its 10 s closing hold, which loops until
# spent. An earlier tape slept 18 s, which truncated the hold and froze the last
# nine seconds of the take; before that it slept 32 s on the belief that motion
# lasted 77 % of the runtime, which it did not. Both numbers came from reasoning
# about a program. The one that worked came from timing it.
Type "FORCE_HOLD=1 bash run.sh --max 12 --jobs 12"
Enter
Sleep 28

# A held final frame, which is what a viewer wants at the end rather than a cut.
Sleep 4
