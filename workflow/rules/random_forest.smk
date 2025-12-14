# ============================================
# RANDOM FOREST RULES - MULTI-NODE PARALLELIZATION
# ============================================
# Train Random Forest models in parallel batches across multiple nodes

rule split_genes_for_rf:
    """
    Split genes into batches for parallel Random Forest execution.
    """
    input:
        matrix = "data/interim/collapsed_matrix.csv"
    output:
        batches = expand("data/interim/rf_batches/batch_{batch}.txt",
                        batch=range(config["random_forest"]["n_batches"]))
    params:
        n_batches = config["random_forest"]["n_batches"],
        output_dir = "data/interim/rf_batches"
    log:
        "logs/random_forest/split_genes.log"
    conda:
        "../../envs/py.yml"
    script:
        "../scripts/split_genes_for_rf.py"


rule run_random_forest_batch:
    """
    Train Random Forest for a batch of genes.
    Each batch processes a subset of genes but uses the full matrix as features.
    """
    input:
        matrix = "data/interim/collapsed_matrix.csv",
        gene_list = "data/interim/rf_batches/batch_{batch}.txt"
    output:
        importance = "results/random_forest/batches/imp_{batch}.csv",
        performance = "results/random_forest/batches/perf_{batch}.csv"
    params:
        n_trees = config["random_forest"]["n_trees"],
        depth = config["random_forest"]["max_depth"],
        min_present = config["random_forest"]["min_present"],
        min_absent = config["random_forest"]["min_absent"],
        n_threads = config["random_forest"]["n_threads"],
        purity = config["random_forest"]["purity"],
        output_dir = "results/random_forest/batches"
    log:
        "logs/random_forest/batch_{batch}.log"
    benchmark:
        "benchmarks/random_forest/batch_{batch}.tsv"
    threads: 32  # Máxima paralelización efectiva
    resources:
        mem_mb = 64000,   # 64 GB per batch (less than single-node 320 GB)
        runtime = 480     # 8 hours per batch
    conda:
        "../../envs/py.yml"
    script:
        "../scripts/PanForest.py"


rule merge_rf_results:
    """
    Merge Random Forest batch results into complete matrices.
    """
    input:
        importance = expand("results/random_forest/batches/imp_{batch}.csv",
                           batch=range(config["random_forest"]["n_batches"])),
        performance = expand("results/random_forest/batches/perf_{batch}.csv",
                            batch=range(config["random_forest"]["n_batches"]))
    output:
        importance = "results/random_forest/imp.csv",
        performance = "results/random_forest/performance.csv"
    log:
        "logs/random_forest/merge_results.log"
    benchmark:
        "benchmarks/random_forest/merge_results.tsv"
    conda:
        "../../envs/py.yml"
    script:
        "../scripts/merge_rf_results.py"


rule simplify_importance_matrix:
    """
    Filter weak relationships from importance matrix.
    """
    input:
        importance = "results/random_forest/imp.csv"
    output:
        simplified = "results/networks/simplified_imp.csv"
    params:
        threshold = config["network"]["importance_threshold"]
    log:
        "logs/random_forest/simplify_imp.log"
    benchmark:
        "benchmarks/random_forest/simplify_importance_matrix.tsv"
    conda:
        "../../envs/py.yml"
    script:
        "../scripts/simplify_imp.py"
