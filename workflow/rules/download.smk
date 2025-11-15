# workflow/rules/download.smk
"""
Download and organize genomes from NCBI.

This module handles:

"""

rule query_ncbi_metadata:
    """Get metadata from NCBI without downloading genomes"""
    output:
        metadata = "data/raw/genomes/ncbi_metadata.jsonl"
    params:
        taxid = config["download"]["taxid"],
        assembly_levels = config["download"]["assembly_levels"]
    conda:
        "../../envs/download.yml"
    log:
        "logs/download/query_metadata.log"
    script:
        "../scripts/get_metadata.py"


rule deduplicate_assemblies:
    """Deduplicate GCA vs GCF (prefer GCA)"""
    input:
        metadata = "data/raw/genomes/ncbi_metadata.jsonl"
    output:
        accessions = "data/raw/genomes/accessions_filtered.txt",
        stats = "data/raw/genomes/deduplication_stats.txt"
    conda:
        "../../envs/download.yml"
    log:
        "logs/download/deduplicate.log"
    script:
        "../scripts/filter_metadata.py"


rule download_genomes:
    """Download only deduplicated genomes"""
    input:
        accessions = "data/raw/genomes/accessions_filtered.txt"
    output:
        flag = "data/raw/genomes/.download_complete",
        metadata = "data/raw/genomes/metadata.tsv"
    params:
        outdir = config["download"]["outdir"]
    conda:
        "../../envs/download.yml"
    log:
        "logs/download/download_genomes.log"
    script:
        "../scripts/download_genomes.py"


