#!/usr/bin/env python3

import argparse
import sys
import time
import json

BLEEP_TYPES = [ 'fuzz', 'beep', 'silence', 'reverse' ]
BLEEP = BLEEP_TYPES[0]
BLEEP_BUFFER = 5
MARK_STRENGTH = 4
FREQUENCY = 12000

def get_fuzz_filler(length, data):
    return np.random.rand(length ,2)

def get_silence_filler(length, data):
    return np.zeros((length ,2))

def get_beep_filler(length, data):
    base = np.linspace(0, 1, length, endpoint=False)
    beep_data = np.sin(2 * np.pi * FREQUENCY * base)
    return np.array([beep_data, beep_data]).T

def get_reverse_filler(length, data):
    return np.flip(data, axis=0)

def get_filler_for_bleep(bleep):
    if bleep == "beep":
        return get_beep_filler
    elif bleep == "reverse":
        return get_reverse_filler
    elif bleep == "silence":
        return get_silence_filler
    else:
        return get_fuzz_filler

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
parser.add_argument("-l", "--lyrics", required=False, help = "lyrics JSON file for the input track")
parser.add_argument("-w", "--wordlist", required=False, help = "list of words (in JSON file) to bleep")
parser.add_argument("-o", "--output", required=True, help = "write WAV audio to output file")
parser.add_argument("-c", "--cutout", required=False, help = "write JSON cutlist to output file")
parser.add_argument("-u", "--user", required=False, help = "use manual cutlist to create output")
parser.add_argument("-b", "--bleep", required=False, help = "type of bleep to use (default: fuzz)")
parser.add_argument("-m", "--mark", required=False, help = "strength of the multiplier for the bleep (default: 4)")
parser.add_argument("-B", "--buffer", required=False, help = "percent buffer each side of bleeped word (default: 5)")
args = parser.parse_args()

lyrics = args.lyrics
wordlist = args.wordlist
output = args.output
file = args.file
cutout = args.cutout
user = args.user

# Sanity check the optional args
if not (wordlist and lyrics) and not user:
    print("Either wordlist and lyrics, or a user arg is required, exiting")
    sys.exit(-1)

if args.bleep is not None and args.bleep in BLEEP_TYPES:
    BLEEP = args.bleep
if args.mark is not None:
    MARK_STRENGTH = int(args.mark)
if args.buffer is not None:
    BLEEP_BUFFER = int(args.buffer)

print_timer()
print("Starting bleep-blaster...")
print_timer()
print(f" - Using bleep type of {BLEEP}")
print_timer()
print(f" - Using bleep buffer of {BLEEP_BUFFER}%")
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
cutlist = []
if user:
    print(" * Loading user cutlist...")
    with open(user, 'r') as f:
        cutdata = json.load(f)
    BLEEP = cutdata.get('bleep', BLEEP)
    cutlist = [tuple(x) for x in cutdata['radioCutlist']]
else:
    print(" * Loading lyrics cutlist and wordlist...")
    with open(lyrics, 'r') as f:
        lyrics = json.load(f)
    with open(wordlist, 'r') as f:
        wordlist = json.load(f)
    for seg in lyrics['segments']:
        for word in seg['words']:
            for version in [ 'text', 'word' ]:
                try:
                    if word[version].strip().lower() in wordlist or (word[version] != '[*]' and '*' in word[version]):
                        if word['start'] != word['end']:
                            cutlist.append((word[version].strip().lower(), word['start'], word['end']))
                except:
                    pass
print_timer()
print(f" * Doing math for cutlist ({len(cutlist)})...")
get_filler = get_filler_for_bleep(BLEEP)
data = y.T
for word, c1, c2 in cutlist:
    gap = c2-c1
    buffer = gap * (BLEEP_BUFFER / 100)
    cut1 = int((c1-buffer) * sr)
    cut2 = int((c2+buffer) * sr)
    cut1 = cut1 if cut1 > 0 else 0
    cut2 = cut2 if cut2 < len(data) else len(data)
    fill = get_filler(cut2-cut1, data[cut1:cut2])
    scale = np.sqrt(np.mean(data[cut1:cut2]**2))
    fill = fill * scale * MARK_STRENGTH
    data = np.concatenate((data[:cut1], fill, data[cut2:]))
    print(f" - Bleeped \"{word}\" from {c1} - {c2}")

print_timer()
print(f" * Writing output file ...")
sf.write(output, data, sr)
if cutout:
    content = json.dumps(cutlist)
    with open(cutout, 'w') as f:
        f.write(content)

print_timer()
print("Done")
