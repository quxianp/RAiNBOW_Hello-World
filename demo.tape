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

# No cold open. One was tried: a hue sweep typed and run before the show, on the
# theory that a video should begin with colour rather than a blinking cursor. A
# contact sheet of the resulting take (scripts/inspect_frames.py) showed it cost
# about four seconds of typing -- VHS types at 50 ms a character and the command
# is 68 characters -- to buy a little over one second of visible sweep, and the
# first frame was still blank. The cursor is the better opening.
Type "clear"
Enter
Type "FORCE_HOLD=1 bash run.sh --max 12 --jobs 12"
Enter
Sleep 28

# A held final frame, which is what a viewer wants at the end rather than a cut.
Sleep 4
