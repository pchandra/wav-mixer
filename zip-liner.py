#!/usr/bin/env python3

import os
import shutil
import uuid
import json
import zipfile
import subprocess
import argparse
import time

TMPDIR = '/tmp'
FFPROBE_BIN = '/usr/local/bin/ffprobe'

# Timer helper function
time_start = time.perf_counter()
time_last = 0
def print_timer():
    global time_start, time_last
    now = time.perf_counter()
    print("[%05.2f][%05.2f]" % (now-time_start, now-time_last), end=" ")
    time_last = now

def _get_media_info(wavfile):
    # Build the command line to run
    cmdline = []
    cmdline.append(FFPROBE_BIN)
    cmdline.extend([ "-v", "quiet",
                     "-of", "json",
                     "-show_format",
                     "-show_streams",
                     "-show_chapters",
                     "-show_programs",
                     "-find_stream_info"
                   ])
    cmdline.append(wavfile)
    # Execute the command
    process = subprocess.Popen(cmdline,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    stdout, _ = process.communicate()
    # Validate and write JSON output to tempfile
    return json.loads(stdout)

def _file_handler(filename):
    basename = os.path.basename(filename)
    if basename.startswith('.'):
        return
    ret = {}
    ext = os.path.splitext(basename)[1]
    if ext in [ ".wav", ".aiff", ".mp3", ".jpg", ".jpeg", ".png", ".gif"]:
        ret = _get_media_info(filename)
    return ret

def _check_dir(subdir, base, info={}, other={}):
    print_timer()
    print(f"Descending into: {subdir}")
    dirpath = os.path.abspath(subdir)
    for file in os.listdir(dirpath):
        fullpath = os.path.join(dirpath, file)
        if os.path.isdir(fullpath):
            dirinfo, dirother = _check_dir(fullpath, base)
            info.update(dirinfo)
            other.update(dirother)
        else:
            result = _file_handler(fullpath)
            key = fullpath.replace(base + '/', '')
            if result == {}:
                other[key] = True
            elif result is not None:
                info[key] = result
    return info, other

def main():
    global FFPROBE_BIN
    print_timer()
    print("Starting zip-liner...")

    # Parse the args
    DESC="""
    This is a really basic tool to inventory a ZIP file and collect
    metadata about each of the files it contains
    """
    parser = argparse.ArgumentParser(description=DESC)
    parser.add_argument("-i", "--input", required=True, help = "input zip file to be inventoried")
    parser.add_argument("-o", "--output", required=True, help = "write JSON formatted output to file")
    parser.add_argument("-f", "--ffprobe", required=False, help = "path to ffprobe binary to use")
    args = parser.parse_args()

    # Get the zip filename and a scratch directory
    file = args.input
    outfile = args.output
    if args.ffprobe is not None:
        FFPROBE_BIN = args.ffprobe
    scratch = TMPDIR + f'/{str(uuid.uuid4())}'
    os.makedirs(scratch)

    print_timer()
    print("Extracting zip file...")
    # Extract the zip archive
    with zipfile.ZipFile(file, "r") as z:
        z.extractall(scratch)

    print_timer()
    print("Checking files...")
    # Recursively inventory what we found
    extracted = os.path.abspath(scratch)
    zipinfo, others = _check_dir(extracted, extracted)

    print_timer()
    print("Summarizing metadata...")
    # Summarize some data for the whole zip
    summary = {}
    summary['size-compresssed'] = os.path.getsize(file)
    summary['size-uncompresssed'] = 0
    summary['file-types'] = {}

    for key in zipinfo.keys():
        basename = os.path.basename(key)
        ext = os.path.splitext(basename)[1]
        fmt = zipinfo[key].get('format')
        if fmt is not None:
            summary['size-uncompresssed'] += int(fmt.get('size', 0))
        summary['file-types'][ext] = summary['file-types'].get(ext, 0) + 1

    # Build the object we will save
    inventory = {}
    inventory['summary'] = summary
    inventory['files'] = zipinfo
    inventory['others'] = others

    print_timer()
    print("Writing output...")
    with open(outfile, 'w') as f:
        f.write(json.dumps(inventory, indent=2))
    shutil.rmtree(scratch)

    print_timer()
    print("Finished")

if __name__ == '__main__':
    main()
