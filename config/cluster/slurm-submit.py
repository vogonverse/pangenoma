#!/usr/bin/env python3
"""
SLURM job submission script for Snakemake
==========================================
This script is called by Snakemake to submit jobs to SLURM.
It parses the job properties and submits using sbatch.

Usage (called automatically by Snakemake):
    python slurm-submit.py <jobscript>
"""

import sys
import os
from pathlib import Path
from snakemake.utils import read_job_properties

# Read job properties from the jobscript
jobscript = sys.argv[1]
job_properties = read_job_properties(jobscript)

# Extract job information
rule = job_properties.get("rule", "unknown")
wildcards = job_properties.get("wildcards", {})
threads = job_properties.get("threads", 1)
resources = job_properties.get("resources", {})

# Build job name
job_name = rule
if wildcards:
    wildcard_str = "_".join(f"{k}={v}" for k, v in wildcards.items())
    job_name = f"{rule}_{wildcard_str}"

# Extract SLURM parameters from resources
partition = resources.get("partition", "normal")
time = resources.get("time", "01:00:00")
mem = resources.get("mem", "4G")
cpus = resources.get("cpus", threads)
output = resources.get("output", f"logs/slurm/{rule}_%j.out")
error = resources.get("error", f"logs/slurm/{rule}_%j.err")

# Create log directory if it doesn't exist
log_dir = Path(output).parent
log_dir.mkdir(parents=True, exist_ok=True)

# Build sbatch command
sbatch_cmd = f"""sbatch \
--job-name={job_name} \
--partition={partition} \
--time={time} \
--mem={mem} \
--cpus-per-task={cpus} \
--output={output} \
--error={error} \
{jobscript}"""

# Submit job
os.system(sbatch_cmd)
