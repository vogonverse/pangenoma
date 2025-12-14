# ============================================
# PHYLOGENETIC STATISTICS RULES
# ============================================
# Calculates Fritz & Purvis D statistic to measure phylogenetic signal

rule identify_coincident_genes:
    """
    Identifies genes to be analyzed for D statistic.
    Filters genes based on F1 score and error thresholds.
    """
    input:
        importance = "results/random_forest/imp.csv"
    output:
        coincident = "results/statistics/coincident_nodes_in.csv"
    log:
        "logs/statistics/identify_genes.log"
    benchmark:
        "benchmarks/statistics/identify_coincident_genes.tsv"
    conda:
        "../../envs/py.yml"
    script:
        "../scripts/phylogeny_utils.py"

rule split_genes_for_d_stat:
    """
    Split coincident genes into batches for parallel D statistic calculation.
    """
    input:
        coincident = "results/statistics/coincident_nodes_in.csv"
    output:
        batches = expand("data/interim/d_stat_batches/batch_{batch}.csv",
                        batch=range(config["phylogeny"]["n_batches"]))
    params:
        n_batches = config["phylogeny"]["n_batches"],
        output_dir = "data/interim/d_stat_batches"
    log:
        "logs/statistics/split_genes_d_stat.log"
    conda:
        "../../envs/py.yml"
    script:
        "../scripts/split_genes_for_d_stat.py"


rule calculate_d_statistic_batch:
    """
    Calculate D statistic for a batch of genes.
    Each batch processes a subset of genes but uses the same phylogeny and matrix.
    D measures phylogenetic signal:
      - D ~  1: random/no phylogenetic signal
      - D ~  0: Brownian motion (neutral evolution)
      - D <  0: phylogenetically conserved (more than Brownian)
      - D > -1: phylogenetically overdispersed
    """
    input:
        gene_list = "data/interim/d_stat_batches/batch_{batch}.csv",
        phylogeny = lambda wildcards: (
            config["input"]["phylogeny"]
            if config["input"]["phylogeny"] is not None
            else "results/phylogeny/core_genome.treefile"
        ),
        matrix = "data/interim/collapsed_matrix.csv"
    output:
        d_stats = "results/statistics/batches/d_stat_{batch}.tsv"
    params:
        cores = config["phylogeny"]["cores"],
        output_prefix = "results/statistics/batches/d_{batch}"
    log:
        "logs/statistics/d_stat_batch_{batch}.log"
    benchmark:
        "benchmarks/statistics/d_stat_batch_{batch}.tsv"
    threads: 4  # R parallel processing
    resources:
        mem_mb = 16000,   # 16 GB per batch (less than single-node 128 GB)
        runtime = 120     # 2 hours per batch
    conda:
        "../../envs/r.yml"
    script:
        "../scripts/calculate_d_batch.R"


rule merge_d_statistics:
    """
    Merge D statistic batch results into complete table.
    """
    input:
        d_stats = expand("results/statistics/batches/d_stat_{batch}.tsv",
                        batch=range(config["phylogeny"]["n_batches"]))
    output:
        d_stats = "results/statistics/d_statistics.tsv"
    log:
        "logs/statistics/merge_d_statistics.log"
    benchmark:
        "benchmarks/statistics/merge_d_statistics.tsv"
    conda:
        "../../envs/py.yml"
    script:
        "../scripts/merge_d_statistics.py"

rule summarize_d_statistics:
    """
    Generates summary statistics from calculated D values.
    Creates a text report with distribution and interpretation.
    """
    input:
        d_stats = "results/statistics/d_statistics.tsv"
    output:
        summary = "results/statistics/d_summary.txt"
    log:
        "logs/statistics/summarize_d.log"
    benchmark:
        "benchmarks/statistics/summarize_d_statistics.tsv"
    conda:
        "../../envs/py.yml"
    script:
        "../scripts/phylogeny_utils.py"
