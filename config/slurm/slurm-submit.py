#!/usr/bin/env python3
"""
SLURM submission script for Snakemake.
Translates Snakemake resources to SLURM directives.
"""

import sys
import os
from snakemake.utils import read_job_properties

# Read job properties from Snakemake
jobscript = sys.argv[1]
job_properties = read_job_properties(jobscript)

# Extract job information
rule = job_properties.get("rule", "unknown")
wildcards = job_properties.get("wildcards", {})
threads = job_properties.get("threads", 1)
resources = job_properties.get("resources", {})

# Get resources with defaults
mem_mb = resources.get("mem_mb", 4000)
runtime = resources.get("runtime", 60)  # minutes

# Create job name
if wildcards:
    wildcard_str = "_".join(f"{k}={v}" for k, v in wildcards.items())
    job_name = f"{rule}_{wildcard_str}"
else:
    job_name = rule

# Truncate job name if too long (SLURM limit is typically 64 chars)
job_name = job_name[:64]

# Create SLURM submission command
slurm_cmd = [
    "sbatch",
    "--parsable",  # Return job ID only
    f"--job-name={job_name}",
    f"--cpus-per-task={threads}",
    f"--mem={mem_mb}M",
    f"--time={runtime}",
    f"--output=logs/slurm/{rule}_%j.out",
    f"--error=logs/slurm/{rule}_%j.err",
]

# Add the jobscript
slurm_cmd.append(jobscript)

# Create logs directory
os.makedirs("logs/slurm", exist_ok=True)

# Print command for debugging
print(" ".join(slurm_cmd), file=sys.stderr)

# Execute sbatch
os.execvp("sbatch", slurm_cmd)
