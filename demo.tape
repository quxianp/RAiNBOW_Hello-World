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

# The show is animated throughout: 24-frame intro sweep, the roll call
# streaming in, a progress bar across the language-execution window, a bar fill,
# an art reveal, the spectral sweep and the hue-sweep hold.
#
# The sleep below used to be tuned against a comment claiming motion lasted
# ~77 % of the runtime. It does not: run.sh finishes in about 9 s on a warm
# runner, so a 32 s sleep left 25 s -- 72 % of the recording -- as a still frame
# on the final screen. Measured with scripts/measure_motion.py, which reported
# 367 of 418 transitions frozen.
#
# 18 s keeps real margin over the observed ~10 s and still leaves a held final
# frame, which is what a viewer wants at the end. If the execution window grows
# on slower runners this is the number to revisit -- and the measurement, not
# the guess, is what should decide it.
# --max 12 keeps the roll call short so the finale stays on screen.
Type "bash run.sh --max 12 --jobs 12"
Enter
Sleep 18

# Hold on the final rainbow Hello World! for a beat.
Sleep 4