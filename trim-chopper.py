#!/usr/bin/env python3

import argparse
import sys
import time
import uuid

TRIM = 5
SIZE = 30

# Timer helper function
time_start = time.perf_counter()
time_last = 0

def print_timer():
    global time_start, time_last
    now = time.perf_counter()
    print("[%05.2f][%05.2f]" % (now-time_start, now-time_last), end=" ")
    time_last = now

# Parse the args
DESC="""
This is a really basic tool to chop an audio file into
smaller files based on time
"""
parser = argparse.ArgumentParser(description=DESC)
parser.add_argument("file", help="input wav file to chop")
parser.add_argument("-o", "--output", required=True, help = "write segments to output directory")
parser.add_argument("-t", "--trim", required=False, help = "seconds to from start and end of input (default: 5)")
parser.add_argument("-s", "--size", required=False, help = "length (in seconds) of each segment (default: 30)")
args = parser.parse_args()

output = args.output
file = args.file
if args.trim is not None:
    TRIM = float(args.trim)
if args.size is not None:
    SIZE = float(args.size)

print_timer()
print("Starting trim-chopper...")
print_timer()
print(f" - Using trim of {TRIM} and segment size {SIZE}")
print_timer()
print(" - Loading librosa...")
import librosa
import soundfile as sf
print_timer()
print(" - Loading numpy...")
import numpy as np
print_timer()
print(" * Loading filename \"" + file + "\"...")
y, sr = librosa.load(file, sr=22050, mono=True)
print_timer()
print(" * Doing math...")
trimmed = y.T[int(TRIM*sr):-1*int(TRIM*sr)]
s_count = int(len(trimmed) / (SIZE*sr))

counter = 0
segments = []
while counter < s_count:
    segment = trimmed[int(counter*SIZE*sr):int((counter+1)*SIZE*sr)]
    segments.append(segment)
    counter += 1

print_timer()
print(f" * Breaking into {len(segments)} pieces...")
filebase = f"{output}/{str(uuid.uuid4())}"
for x, s in enumerate(segments):
    print_timer()
    print(f" - Writing segment {x:02} to file...")
    sf.write(filebase + f"-{x:02}.mp3", s, sr)

print_timer()
print("Done")
