#!/usr/bin/env python3

import argparse
import sys
import json
import time
import cairo
from cairo import OPERATOR_CLEAR
import librosa
import numpy as np

BARS = 40
HEIGHT = 100
WIDTH = 500
STEP = 1
MAX = 0.9
COLOR = (0,0,0)

# Timer helper function
time_start = time.perf_counter()
time_last = 0
def print_timer():
    global time_start, time_last
    now = time.perf_counter()
    print("[%05.2f][%05.2f]" % (now-time_start, now-time_last), end=" ")
    time_last = now


def main():
    print_timer()
    print("Starting bar-tender...")
    global BARS
    global HEIGHT
    global WIDTH
    global STEP
    global MAX
    global COLOR

    # Parse the args
    DESC="""
    This is a really basic tool to produce an SVG of the waveform
    data in a wav file
    """
    parser = argparse.ArgumentParser(description=DESC)
    parser.add_argument("-i", "--input", required=True, help = "input wav file to use for waveform data")
    parser.add_argument("-o", "--output", required=True, help = "write SVG output to file")
    parser.add_argument("-p", "--pngout", required=False, help = "write a PNG version of output to file")
    parser.add_argument("-c", "--color", required=False, help = "hex string of the color to use in output (default: 000000)")
    parser.add_argument("-b", "--bars", required=False, help = "number of bars to produce in the SVG (default: 40)")
    parser.add_argument("-s", "--step", required=False, help = "only print a bar for each step count of bars (default: 1)")
    parser.add_argument("-f", "--factor", required=False, help = "the scaling factor (between 0-1) for bars (default: max of RMS)")
    parser.add_argument("-F", "--ffile", required=False, help = "filename to write the scaling factor in JSON")
    parser.add_argument("-H", "--height", required=False, help = "height in pixels of the output (default: 100)")
    parser.add_argument("-W", "--width", required=False, help = "width in pixels of the output (default: 500)")
    parser.add_argument("-n", "--invert", default=False, action=argparse.BooleanOptionalAction, help = "invert black and transparent in output")
    parser.add_argument("-m", "--mirror", default=False, action=argparse.BooleanOptionalAction, help = "mirror bars vertically from the center")
    parser.add_argument("-M", "--max", required=False, help = "max percent of height vs total image height (default: 0.9)")
    args = parser.parse_args()

    file = args.input
    outfile = args.output
    pngfile = None
    factor = 0
    if args.color is not None:
        r = int(args.color[0:2], 16) / 255
        g = int(args.color[2:4], 16) / 255
        b = int(args.color[4:6], 16) / 255
        COLOR = (r, g, b)
    if args.bars is not None:
        BARS = int(args.bars)
    if args.step is not None:
        STEP = int(args.step)
    if args.height is not None:
        HEIGHT = int(args.height)
    if args.width is not None:
        WIDTH = int(args.width)
    if args.pngout is not None:
        pngfile = args.pngout
    if args.factor is not None:
        factor = float(args.factor)
    if args.max is not None:
        MAX = float(args.max)

    print_timer()
    print("Loading audio file...")
    # Open the audio file as mono to keep it simple
    y, sr = librosa.load(file, sr=None, mono=True)
    print_timer()
    print("Doing math...")
    # Split into chunks and compute a value for each segment
    segments = np.array_split(y, BARS)
    vals = []
    for s in segments:
        vals.append(np.sqrt(np.mean(s**2)))
    # Normalize these values
    factor = max(vals) if factor == 0 else factor
    vals = [ (x / factor) * MAX for x in vals ]

    if args.ffile is not None:
        with open(args.ffile, 'w') as f:
            json.dump({'factor': float(factor)}, f)

    # Normalized step size per bar
    step = (WIDTH/HEIGHT) / BARS
    # The scaling factor on BARS controls the whitespace gaps
    line_width = (WIDTH/HEIGHT) / (BARS * 1.25)

    print_timer()
    print("Drawing...")
    with cairo.SVGSurface(outfile, WIDTH, HEIGHT) as surface:
        context = cairo.Context(surface)
        context.scale(HEIGHT, HEIGHT)
        context.set_source_rgb(COLOR[0], COLOR[1], COLOR[2])
        if args.invert:
            context.set_source_rgba(COLOR[0], COLOR[1], COLOR[2], 1)
            context.rectangle(0, 0, HEIGHT, WIDTH)
            context.fill()
            context.set_operator(OPERATOR_CLEAR)
        context.set_line_width(line_width)
        context.set_line_cap(cairo.LINE_CAP_ROUND)
        count = 0
        while count < BARS:
            offset = (step / 2) + (count * step)
            if args.mirror:
                bottom = 1-(1-vals[count])/2
                top = (1-vals[count])/2
            else:
                bottom = 1
                top = 1-vals[count]
            context.move_to(offset, bottom)
            context.line_to(offset, top)
            context.stroke()
            count += STEP
        if pngfile is not None:
            surface.write_to_png(pngfile)
    print_timer()
    print("Finished")

if __name__ == '__main__':
    main()
