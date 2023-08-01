#!/usr/bin/env python3

import argparse
import sys
import time
import json

BLEEP_TYPES = [ 'reverse', 'beep', 'silence', 'fuzz' ]
BLEEP = BLEEP_TYPES[0]
MARK_STRENGTH = 4

def get_fuzz_filler(length, data):
    return np.random.rand(length ,2)

def get_silence_filler(length, data):
    return np.zeros((length ,2))

def get_beep_filler(length, data):
    return np.random.rand(length ,2)

def get_reverse_filler(length, data):
    return np.flip(data, axis=0)

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
This is a really basic tool to bleep segments of an audio file
based on a word list and lyrics JSON cutlist
"""
parser = argparse.ArgumentParser(description=DESC)
parser.add_argument("file", help="input wav file to bleep")
parser.add_argument("-l", "--lyrics", required=True, help = "lyrics JSON file for the input track")
parser.add_argument("-w", "--wordlist", required=True, help = "list of words (in JSON file) to bleep")
parser.add_argument("-o", "--output", required=True, help = "write to output file")
parser.add_argument("-b", "--bleep", required=False, help = "type of bleep to use (default: fuzz)")
parser.add_argument("-m", "--mark", required=False, help = "strength of the multiplier for the bleep (default: 4)")
args = parser.parse_args()

lyrics = args.lyrics
wordlist = args.wordlist
output = args.output
file = args.file
if args.bleep is not None and args.bleep in BLEEP_TYPES:
    BLEEP = args.bleep
if args.mark is not None:
    MARK_STRENGTH = int(args.mark)

if BLEEP == "beep":
    get_filler = get_beep_filler
elif BLEEP == "reverse":
    get_filler = get_reverse_filler
elif BLEEP == "silence":
    get_filler = get_silence_filler
else:
    get_filler = get_fuzz_filler

print_timer()
print("Starting bleep-blaster...")
print_timer()
print(f" - Using bleep type of {BLEEP}")
print_timer()
print(" - Loading librosa...")
import librosa
import soundfile as sf
print_timer()
print(" - Loading numpy...")
import numpy as np
print_timer()
print(" * Loading filename \"" + file + "\"...")
y, sr = librosa.load(file, sr=None, mono=False)
print_timer()
print(" * Loading lyrics cutlist and wordlist...")
cutlist = []
with open(lyrics, 'r') as f:
    lyrics = json.load(f)
with open(wordlist, 'r') as f:
    wordlist = json.load(f)
for seg in lyrics['segments']:
    for word in seg['words']:
        if word['text'].strip().lower() in wordlist:
            if word['start'] != word['end']:
                cutlist.append((word['text'].strip().lower(), word['start'], word['end']))
print_timer()
print(f" * Doing math for cutlist ({len(cutlist)})...")
data = y.T
for word, c1, c2 in cutlist:
    cut1 = int(c1 * sr)
    cut2 = int(c2 * sr)
    fill = get_filler(cut2-cut1, data[cut1:cut2])
    scale = np.sqrt(np.mean(data[cut1:cut2]**2))
    fill = fill * scale * MARK_STRENGTH
    data = np.concatenate((data[:cut1], fill, data[cut2:]))
    print(f" - Bleeped \"{word}\" from {c1} - {c2}")

print_timer()
print(f" * Writing output file ...")
sf.write(output, data, sr)

print_timer()
print("Done")
