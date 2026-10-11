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

# The show is animated throughout: 24-frame intro sweep, 24-frame divider, the
# roll call streaming in at 0.12 s per name, a progress bar across the whole
# language-execution window, a 70-frame bar fill, a 50-frame art reveal and a
# 10 s hue-sweep hold. Frame-by-frame measurement put the end of real motion at
# ~77 % of the runtime, so 32 s keeps the tail near 4 s rather than 8 s -- but
# not shorter, because the execution window's length varies with how fast the CI
# runners are and a tighter sleep would cut off the art reveal.
# --max 12 keeps the roll call short so the finale stays on screen.
Type "bash run.sh --max 12 --jobs 12"
Enter
Sleep 32

# Hold on the final rainbow Hello World! for a beat.
Sleep 5