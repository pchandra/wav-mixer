#!/usr/local/bin/python3

import argparse
import sys
import time
import soundfile
import librosa
import numpy as np

SAMPLE_RATE=44100
MARK_STRENGTH = 4

# Timer helper function
time_start = time.perf_counter()
time_last = 0
def print_timer():
    global time_start, time_last
    now = time.perf_counter()
    print("[%05.2f][%05.2f]" % (now-time_start, now-time_last), end=" ")
    time_last = now


def generate_watermark(target_shape, stamp):
    # Build either a stereo or a mono watermark track based on input type
    if len(target_shape) == 2:
        print_timer()
        print(" - Generating STEREO watermark...")
        return _generate_stereo_watermark(target_shape, stamp)
    else:
        print_timer()
        print(" - Generating MONO watermark...")
        return _generate_mono_watermark(target_shape, stamp)

def _generate_mono_watermark(target_shape, stamp):
    y_stamp, sr = librosa.load(stamp, sr=SAMPLE_RATE, mono=True)
    silence5s = np.zeros(sr*5, dtype=np.float32)

    # Start with 5 second of silence and then build
    watermark = np.zeros(sr*5, dtype=np.float32)
    while watermark.shape[0] < target_shape[0]:
        watermark = np.concatenate((watermark, y_stamp))
        watermark = np.concatenate((watermark, silence5s))
    # Trim the watermark to the same size as requested
    watermark = watermark[:target_shape[0]]
    return watermark

def _generate_stereo_watermark(target_shape, stamp):
    # Load the stamp as mono and build a silence track of the same length
    y_stamp, sr = librosa.load(stamp, sr=SAMPLE_RATE, mono=True)
    y_stamp_silent = np.zeros(y_stamp.shape)
    # Make a number of versions with different stereo placement
    versions = []
    farleft = np.array([y_stamp, y_stamp_silent], dtype=np.float32)
    midleft = np.array([y_stamp*0.8, y_stamp*0.2], dtype=np.float32)
    nearleft = np.array([y_stamp*0.6, y_stamp*0.4], dtype=np.float32)
    farright = np.array([y_stamp_silent, y_stamp], dtype=np.float32)
    midright = np.array([y_stamp*0.2, y_stamp*0.8], dtype=np.float32)
    nearright = np.array([y_stamp*0.4, y_stamp*0.6], dtype=np.float32)
    center = np.array([y_stamp*0.5, y_stamp*0.5], dtype=np.float32)
    versions = [ farleft, midleft, nearleft, center, nearright, midright, farright ]
    silence5s = np.zeros((2,sr*5), dtype=np.float32)

    # Start with 5 second of silence and then build
    watermark = np.zeros((2,sr*5), dtype=np.float32)
    while watermark.shape[1] < target_shape[1]:
        this_stamp = versions[int(np.random.random() * len(versions))]
        watermark = np.concatenate((watermark.T, this_stamp.T)).T
        watermark = np.concatenate((watermark.T, silence5s.T)).T
    # Trim the watermark to the same size as requested
    watermark = watermark.T[:target_shape[1]].T
    return watermark


def main():
    print_timer()
    print("Starting mark-maker...")
    global SAMPLE_RATE

    # Parse the args
    DESC="""
    This is a really basic tool to watermark a wav file
    (stereo, 16-bit, 44.1khz) by stamping another wav file on top
    """
    parser = argparse.ArgumentParser(description=DESC)
    parser.add_argument("-i", "--input", required=True, help = "input wav file to watermark")
    parser.add_argument("-o", "--output", required=True, help = "write wav output to file")
    parser.add_argument("-s", "--stamp", required=True, help = "wav file to use for watermark stamp")
    parser.add_argument("-m", "--mark", required=False, help = "set watermarking strength (default: 4)")
    parser.add_argument("-r", "--rate", required=False, help = "resample all inputs to this rate (default: 44100)")
    args = parser.parse_args()

    outfile = args.output
    file = args.input
    stamp = args.stamp
    if args.rate is not None:
        SAMPLE_RATE = int(args.rate)
    if args.mark is not None:
        MARK_STRENGTH = int(args.mark)

    print_timer()
    print(" * Reading input filename \"" + file + "\"...")
    y, sr = librosa.load(file, sr=SAMPLE_RATE, mono=False)
    print_timer()
    print(" - Generating watermark content...")
    y_wtrm = generate_watermark(y.shape, stamp)

    print_timer()
    print(" - Mixing audio tracks...")
    # Mix the watermark into the wav
    y_out = (y + (y_wtrm * MARK_STRENGTH))
    soundfile.write(outfile, y_out.T, sr)
    print_timer()
    print(" - Finished writing output to \"" + outfile + "\"...")


if __name__ == '__main__':
    main()
