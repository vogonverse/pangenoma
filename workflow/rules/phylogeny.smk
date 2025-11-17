# Calculates Fritz & Purvis D statistic

rule identify_coincident_genes:
    """
    Identifies genes to be analyzed for D statistic.
    """
    input:
        importance = "results/random_forest/imp.csv"
    output:
        coincident = "results/phylogeny/coincident_nodes_in.csv"
    log:
        "logs/phylogeny/identify_genes.log"
    conda:
        "../../envs/py.yml"
    script:
        "../scripts/phylogeny_utils.py"

rule calculate_d_statistic:
    """
    Calculates Fritz & Purvis D statistic for all previously identified genes.
    D measures phylogenetic signal: D~1 (random), D~0 (Brownian), D<0 (conserved)
    """
    input:
        coincident = "results/phylogeny/coincident_nodes_in.csv",
        phylogeny = lambda wildcards: (
            config["input"]["phylogeny"]
            if config["input"]["phylogeny"] is not None
            else "results/phylogeny/core_genome.treefile"
        ),
        matrix = "data/interim/collapsed_matrix.csv"
    output:
        d_stats = "results/phylogeny/d_statistics.tsv"
    params:
        cores = config["phylogeny"]["cores"],
        output_prefix = "results/phylogeny/d"
    log:
        "logs/phylogeny/calculate_d.log"
    threads: config["phylogeny"]["cores"]
    conda:
        "../../envs/r.yml"
    script:
        "../scripts/calculate_d.R"

rule summarize_d_statistics:
    """
    Generates calculated D statistics summary.
    """
    input:
        d_stats = "results/phylogeny/d_statistics.tsv"
    output:
        summary = "results/phylogeny/d_summary.txt"
    log:
        "logs/phylogeny/summarize_d.log"
    conda:
        "../../envs/py.yml"
    script:
        "../scripts/phylogeny_utils.py"



rule build_phylogeny:
    """
    Build phylogenetic tree from core genome alignment using IQ-TREE.
    """
    input:
        alignment = "results/panaroo/core_gene_alignment.aln"
    output:
        tree = "results/phylogeny/core_genome.treefile",
        iqtree = "results/phylogeny/core_genome.iqtree",
        log_file = "results/phylogeny/core_genome.log"
    params:
        prefix = "results/phylogeny/core_genome",
        model = config["phylogeny_build"]["model"],
        bootstrap = config["phylogeny_build"]["bootstrap"]
    log:
        "logs/phylogeny/build_tree.log"
    threads: config["phylogeny_build"]["threads"]
    conda:
        "../../envs/phylogeny.yml"
    script:
        "../scripts/phylogeny_utils.py"

