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

# The show: hue-sweep intro, roll call, parallel execution, colour bar, and
# the finale -- the per-character true-colour ASCII art plus the greeting.
# --max 12 keeps the roll call short so the finale stays on screen.
Type "bash run.sh --max 12 --jobs 12"
Enter
Sleep 40

# Hold on the final rainbow Hello World! for a beat.
Sleep 4