#!/usr/local/bin/python3

import argparse
import sys
import time

SAMPLE_RATE=44100

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
This is a really basic tool to mix multiple wav files
(stereo, 16-bit, 44.1khz) into a single wav output
"""
parser = argparse.ArgumentParser(description=DESC)
parser.add_argument("files", nargs="+", help="input wav files (need at least 2)")
parser.add_argument("-o", "--output", required=True, help = "write wav output to file")
args = parser.parse_args()

output = args.output
files = args.files
num = len(files)

# Check we have at least 2 args, must be paths to WAV files
if num < 2:
    sys.exit(" -- ERROR: Must have at least two filename arguments")

print_timer()
print("Starting wav_mixer...")

# Load the libs that do the heavy lifting
import soundfile
print_timer()
print(" - Done loading soundfile...")
import librosa
print_timer()
print(" - Done loading librosa...")

# Load the input file data
data = []
for file in files:
    print_timer()
    print(" * Starting filename \"" + file + "\"...")
    y, sr = librosa.load(file, sr=SAMPLE_RATE, mono=False)
    data.append((y,sr))
    print_timer()
    print(" * Finished filename \"" + file + "\"...")

print_timer()
print(" - Mix audio tracks...")
# Accumulators for mixing, starting with first track
y_out = data[0][0]

for d in data[1:]:
    y_out = y_out + d[0]

print_timer()
print(" - Finished mixing...")

soundfile.write(output, y_out.T, sr)
print_timer()
print(" - Finished writing output to \"" + output + "\"...")

print_timer()
print("Done")
