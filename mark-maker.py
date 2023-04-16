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
    y_stamp, sr = librosa.load(stamp, sr=SAMPLE_RATE, mono=True)
    y_stamp_silent = np.zeros(y_stamp.shape)
    left = np.array([y_stamp, y_stamp_silent], dtype=np.float32)
    right = np.array([y_stamp_silent, y_stamp], dtype=np.float32)
    center = np.array([y_stamp, y_stamp], dtype=np.float32)
    silence5s = np.zeros((2,sr*5), dtype=np.float32)

    # Start with 5 second of silence and then build
    watermark = np.zeros((2,sr*5), dtype=np.float32)
    while watermark.shape[1] < target_shape[1]:
        watermark = np.concatenate((watermark.T, center.T)).T
        watermark = np.concatenate((watermark.T, silence5s.T)).T
        watermark = np.concatenate((watermark.T, left.T)).T
        watermark = np.concatenate((watermark.T, silence5s.T)).T
        watermark = np.concatenate((watermark.T, right.T)).T
        watermark = np.concatenate((watermark.T, silence5s.T)).T
    # Trim the watermark to the same size as requested
    watermark = watermark.T[:target_shape[1]].T
    return watermark


def main():
    print_timer()
    print("Starting mark-maker...")

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
