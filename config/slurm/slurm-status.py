#!/usr/bin/env python3
"""
SLURM status script for Snakemake.
Checks the status of a SLURM job.
"""

import sys
import subprocess
import time

jobid = sys.argv[1]

# Try to get job status with sacct
try:
    # Query sacct for job status
    result = subprocess.run(
        ["sacct", "-j", jobid, "--format=State", "--noheader", "--parsable2"],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    status = result.stdout.strip().split("\n")[0]
    
    # Map SLURM states to Snakemake expectations
    if status in ["COMPLETED"]:
        print("success")
    elif status in ["RUNNING", "PENDING", "CONFIGURING", "COMPLETING"]:
        print("running")
    elif status in ["FAILED", "CANCELLED", "TIMEOUT", "NODE_FAIL", "PREEMPTED", "OUT_OF_MEMORY"]:
        print("failed")
    else:
        # Unknown status, assume still running
        print("running")
        
except subprocess.TimeoutExpired:
    print("running")
except Exception as e:
    # If sacct fails, try squeue
    try:
        result = subprocess.run(
            ["squeue", "-j", jobid, "-h"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.stdout.strip():
            # Job found in queue, still running
            print("running")
        else:
            # Job not in queue, check if it completed
            # Assume success if not found (may have completed quickly)
            print("success")
    except:
        # If all fails, assume running
        print("running")
