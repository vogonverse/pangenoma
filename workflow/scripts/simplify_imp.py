#!/usr/bin/env python3
"""Convert very low importances to 0."""

import sys
import pandas as pd

def get_args():
    """Get user arguments."""
    if len(sys.argv) != 4:
        print("USAGE: python3 simplify_imp.py threshold infile outfile")
        sys.exit()
    return sys.argv[1:]

def main():
    """Convert imp values < 0.01 to 0."""
    # pylint: disable=unbalanced-tuple-unpacking
    threshold, infile, outfile = get_args()
    threshold = float(threshold)
    imp =pd.read_csv(infile, index_col = 0, header = 0)
    imp = imp.apply(pd.to_numeric)
    imp[imp.le(threshold)] = 0
    imp.to_csv(outfile)

if __name__ == "__main__":
    # Check if running from Snakemake
    try:
        # Snakemake provides a global 'snakemake' object
        snakemake
        # Extract parameters from Snakemake
        threshold = snakemake.params.threshold
        infile = snakemake.input.importance
        outfile = snakemake.output.simplified

        # Run the analysis
        threshold = float(threshold)
        imp = pd.read_csv(infile, index_col=0, header=0)
        imp = imp.apply(pd.to_numeric)
        imp[imp.le(threshold)] = 0
        imp.to_csv(outfile)

    except NameError:
        # Not running from Snakemake, use command line arguments
        main()
