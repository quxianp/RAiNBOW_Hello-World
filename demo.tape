# VHS tape -- RAiNBOW_Hello-World
#
#   vhs demo.tape            -> assets/hello-world.gif
#
# scripts/record_demo.sh drives this and then transcodes to MP4.
# Kept at 1200x800 / font 20 so the 694-segment bar stays legible.

Output assets/hello-world.gif

Set Shell "bash"
Set FontSize 20
Set Width 1200
Set Height 800
Set PlaybackSpeed 1.0
Set Theme '{"background":"#0d1117","foreground":"#ffffff","accent":"#58a6ff"}'
Set TypingSpeed 0.05

# Let the animation settle before the show starts.
Type "clear"
Enter
Sleep 1

# The show: opening sweep, 694-language roll call, parallel execution,
# ASCII art, the colour bar and the final greeting.
Type "./run.sh --jobs 8"
Enter
Sleep 25

# Hold on the final rainbow Hello World! for a beat.
Sleep 3
