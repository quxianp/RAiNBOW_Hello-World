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
# ever regresses), but invoking bash explicitly makes the recording immune to
# the whole class of problem.
#
# The show is animated, so the tape has to wait for real motion rather than for a
# prompt: 18 intro frames, then a 44-frame bar fill, then a 30-frame art reveal,
# plus the roll call and the parallel execution in between.

Output assets/hello-world.gif

Set Shell "bash"
Set FontSize 20
Set Width 1200
Set Height 800
Set PlaybackSpeed 1.0
Set Theme '{"background":"#0d1117","foreground":"#ffffff","accent":"#58a6ff"}'
Set TypingSpeed 0.05

Type "clear"
Enter
Sleep 1

# The show: rainbow intro sweep, roll call, parallel execution, easter egg, the
# language bar filling in one language per frame, the block letters wiping in
# left to right, and the true-colour greeting.
# --max 12 keeps the roll call short so the finale stays on screen.
Type "bash run.sh --max 12 --jobs 12"
Enter
Sleep 45

# Hold on the final rainbow Hello World! for a beat.
Sleep 5