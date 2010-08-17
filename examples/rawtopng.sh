#!/bin/sh

for f in "$@"; do
    convert -size 1024x512 -depth 8 rgb:"$f" "$f".png
done
