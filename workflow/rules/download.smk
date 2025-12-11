# workflow/rules/download.smk
"""
Download and organize genomes from NCBI.
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
    benchmark:
        "benchmarks/download/query_ncbi_metadata.tsv"
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
    benchmark:
        "benchmarks/download/deduplicate_assemblies.tsv"
    script:
        "../scripts/filter_metadata.py"


rule download_genomes:
    """Download only deduplicated genomes"""
    input:
        accessions = "data/raw/genomes/accessions_filtered.txt"
    output:
        flag = "data/raw/genomes/.download_complete",
    params:
        outdir = config["download"]["outdir"]
    conda:
        "../../envs/download.yml"
    log:
        "logs/download/download_genomes.log"
    benchmark:
        "benchmarks/download/download_genomes.tsv"
    script:
        "../scripts/download_genomes.py"


