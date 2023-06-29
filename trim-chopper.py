#!/usr/bin/env python3

import os
import shutil
import argparse
import sys
import time
import uuid
import subprocess

TRIM = 5
SIZE = 30
MAX = 0
WORK_DIR = '/tmp/SCRATCH'
FFMPEG_BIN = '/usr/bin/ffmpeg'

# Timer helper function
time_start = time.perf_counter()
time_last = 0

def print_timer():
    global time_start, time_last
    now = time.perf_counter()
    print("[%05.2f][%05.2f]" % (now-time_start, now-time_last), end=" ")
    time_last = now

# Copied helper functions from lab-director's helpers.py
def make_nonsilent_wave(infile, outfile):
    # Build the command line to run
    cmdline = []
    cmdline.append(FFMPEG_BIN)
    cmdline.extend([ "-i", infile,
                     "-af", "silenceremove=stop_periods=-1:stop_duration=0.1:stop_threshold=-36dB",
                     "-ac", "1",
                     "-ss", "0",
                     outfile, "-y"
                   ])
    process = subprocess.Popen(cmdline,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               universal_newlines=True)
    process.wait()
    return outfile

scratch_dirs = []
def create_scratch_dir():
    path = WORK_DIR + f"/{str(uuid.uuid4())}"
    os.makedirs(path, exist_ok=True)
    scratch_dirs.append(path)
    return path

def destroy_scratch_dir(path):
    if path in scratch_dirs:
        shutil.rmtree(path)
        scratch_dirs.remove(path)

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
parser.add_argument("-m", "--max", required=False, help = "max number of segments to output (default: all)")
parser.add_argument("-n", "--nonsilent", default=False, action=argparse.BooleanOptionalAction, help = "automatically remove silence from segments")
args = parser.parse_args()

output = args.output
file = args.file
if args.trim is not None:
    TRIM = float(args.trim)
if args.size is not None:
    SIZE = float(args.size)
if args.max is not None:
    MAX = float(args.max)

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
if args.nonsilent:
    print_timer()
    print(f" * Removing silence from file \"{file}\"...")
    scratch = create_scratch_dir()
    temp = str(uuid.uuid4())
    nonsilent = f"{scratch}/{temp}.wav"
    make_nonsilent_wave(file, nonsilent)
    file = nonsilent
print_timer()
print(" * Loading filename \"" + file + "\"...")
y, sr = librosa.load(file, sr=None, mono=False)
if args.nonsilent:
    destroy_scratch_dir(scratch)
print_timer()
print(" * Doing math...")
trimmed = y.T[int(TRIM*sr):-1*int(TRIM*sr)] if TRIM != 0 else y.T
SIZE = len(trimmed) / sr if SIZE == 0 else SIZE
s_count = int(len(trimmed) / (SIZE*sr))
s_count = MAX if MAX > 0 and s_count > MAX else s_count

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
