#!/bin/sh

files=""
for f in "$@"; do
    files="$files gray:$f"
done

convert -size 1024x512 -depth 8 $files movie.gif
