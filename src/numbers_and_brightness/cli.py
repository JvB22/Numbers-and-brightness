import argparse
import numbers_and_brightness
from pathlib import Path
from numbers_and_brightness.numbers_and_brightness import numbers_and_brightness_analysis, numbers_and_brightness_batch
from numbers_and_brightness.gui import nb_gui

from numbers_and_brightness.defaults import (
    DEFAULT_BACKGROUND,
    DEFAULT_SEGMENT,
    DEFAULT_DIAMETER,
    DEFAULT_FLOW_THRESHOLD,
    DEFAULT_CELLPROB_THRESHOLD,
    DEFAULT_ANALYSIS,
    DEFAULT_ERODE
)

def _str2bool(value):
    if value.lower() in ['true', '1', 't', 'y', 'yes']:
        return True
    elif value.lower() in ['false', '0', 'f', 'n', 'no']:
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected (true/false, yes/no)")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version', version=f'numbers_and_brightness {numbers_and_brightness.__version__}')
    parser.add_argument("--file", type=Path)
    parser.add_argument("--folder", type=Path)
    parser.add_argument("--background", type=float, default=DEFAULT_BACKGROUND)
    parser.add_argument("--segment", type=_str2bool, default=DEFAULT_SEGMENT)
    parser.add_argument("--diameter", type=int, default=DEFAULT_DIAMETER)
    parser.add_argument("--flow_threshold", type=float, default=DEFAULT_FLOW_THRESHOLD)
    parser.add_argument("--cellprob_threshold", type=float, default=DEFAULT_CELLPROB_THRESHOLD)
    parser.add_argument("--analysis", type=_str2bool, default=DEFAULT_ANALYSIS)
    parser.add_argument("--erode", type=int, default=DEFAULT_ERODE)

    args = parser.parse_args()

    if args.file:
        numbers_and_brightness_analysis(args.file.resolve(),
                                        background=args.background,
                                        segment=args.segment,
                                        diameter=args.diameter,
                                        flow_threshold=args.flow_threshold,
                                        cellprob_threshold=args.cellprob_threshold,
                                        analysis=args.analysis,
                                        erode=args.erode
                                        )
        print(f"Processed: {args.file}")
        
    elif args.folder:
        numbers_and_brightness_batch(args.folder.resolve(),
                                     background=args.background,
                                     segment=args.segment,
                                     diameter=args.diameter,
                                     flow_threshold=args.flow_threshold,
                                     cellprob_threshold=args.cellprob_threshold,
                                     analysis=args.analysis,
                                     erode=args.erode
                                     )
    else:
        nb_gui()