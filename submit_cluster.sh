#!/bin/bash
#SBATCH --job-name=panforest_pipeline
#SBATCH --partition=normal
#SBATCH --time=168:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --output=logs/slurm/main_%j.out
#SBATCH --error=logs/slurm/main_%j.err

# ============================================
# PanForest Pipeline - SLURM Cluster Submission
# ============================================
#
# This is the MAIN submission script that launches Snakemake
# on a SLURM cluster. Snakemake will then submit individual
# jobs for each rule according to the configuration in:
#   config/cluster/slurm-config.yaml
#
# USAGE:
#   sbatch submit_cluster.sh
#
# OR for dry-run:
#   bash submit_cluster.sh --dry-run
#
# ============================================

set -e  # Exit on error
set -u  # Exit on undefined variable

# ============================================
# CONFIGURATION
# ============================================

# Number of jobs to submit simultaneously
MAX_JOBS=50

# Snakemake targets (leave empty for 'all')
TARGET=""

# Working directory (automatically set to script location)
WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$WORKDIR"

# Create logs directory
mkdir -p logs/slurm

# ============================================
# LOAD MODULES
# ============================================

# Load Anaconda3 module
module load anaconda3

# Activate snakemake environment
# If you don't have a snakemake environment yet, create it with:
#   conda create -n snakemake -c conda-forge -c bioconda snakemake
source activate snakemake

# ============================================
# CHECK SNAKEMAKE INSTALLATION
# ============================================

if ! command -v snakemake &> /dev/null; then
    echo "ERROR: Snakemake not found in PATH"
    echo "Please load the appropriate module or activate conda environment"
    exit 1
fi

echo "=================================================="
echo "PanForest Pipeline - Cluster Execution"
echo "=================================================="
echo "Snakemake version: $(snakemake --version)"
echo "Working directory: $WORKDIR"
echo "Max simultaneous jobs: $MAX_JOBS"
echo "=================================================="
echo ""

# ============================================
# PARSE COMMAND LINE ARGUMENTS
# ============================================

DRY_RUN=""
if [[ "$#" -gt 0 ]] && [[ "$1" == "--dry-run" ]]; then
    DRY_RUN="--dry-run"
    echo "Running in DRY-RUN mode (no jobs will be submitted)"
    echo ""
fi

# ============================================
# RUN SNAKEMAKE WITH CLUSTER EXECUTION
# ============================================

snakemake \
    --jobs $MAX_JOBS \
    --cluster-config config/cluster/slurm-config.yaml \
    --cluster "sbatch \
        --job-name={rule} \
        --partition={cluster.partition} \
        --time={cluster.time} \
        --mem={cluster.mem} \
        --cpus-per-task={cluster.cpus} \
        --output={cluster.output} \
        --error={cluster.error}" \
    --latency-wait 60 \
    --use-conda \
    --conda-prefix .snakemake/conda \
    --printshellcmds \
    --reason \
    --keep-going \
    $DRY_RUN \
    $TARGET

# ============================================
# COMPLETION MESSAGE
# ============================================

if [[ -z "$DRY_RUN" ]]; then
    echo ""
    echo "=================================================="
    echo "Pipeline submitted successfully!"
    echo "=================================================="
    echo ""
    echo "Monitor jobs with:"
    echo "  squeue -u \$USER"
    echo ""
    echo "Check logs in:"
    echo "  logs/slurm/"
    echo ""
    echo "Cancel all jobs:"
    echo "  scancel -u \$USER --name=panforest_pipeline"
    echo "=================================================="
fi
