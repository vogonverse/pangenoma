# workflow/rules/panaroo.smk
"""
Pangenome inference with Panaroo.
Generates gene presence/absence matrix and all associated outputs.
"""

rule run_panaroo:
    """Execute Panaroo to infer the pangenome."""
    input:
        gff_list = "results/prokka/gff_files.txt",
        all_done = "results/prokka/.all_gffs_registered"
    output:
        # main outputs
        gene_pa_csv = "results/panaroo/gene_presence_absence.csv", # input for RF
        gene_pa_rtab = "results/panaroo/gene_presence_absence.Rtab",
        gene_data = "results/panaroo/gene_data.csv",
        summary = "results/panaroo/summary_statistics.txt",
        
        # graphs and structures
        final_graph = "results/panaroo/final_graph.gml",
        struct_pa = "results/panaroo/struct_presence_absence.Rtab",
        
        # reference sequence
        pan_genome_ref = "results/panaroo/pan_genome_reference.fa",
        combined_dna = "results/panaroo/combined_DNA_CDS.fasta",
        combined_protein = "results/panaroo/combined_protein_CDS.fasta",
        
        # alignment (if alignment: core)
        core_aln = "results/panaroo/core_gene_alignment.aln"
    params:
        # pass ALL config to params
        outdir = "results/panaroo",
        clean_mode = config["panaroo"]["clean_mode"],
        identity_threshold = config["panaroo"]["identity_threshold"],
        family_threshold = config["panaroo"].get("family_threshold", 0.7),
        len_dif_percent = config["panaroo"].get("len_dif_percent", 0.98),
        alignment = config["panaroo"].get("alignment", "core"),
        aligner = config["panaroo"].get("aligner", "mafft"),
        core_threshold = config["panaroo"].get("core_threshold", 0.95),
        merge_paralogs = config["panaroo"].get("merge_paralogs", False),
        remove_invalid_genes = config["panaroo"].get("remove_invalid_genes", True),
        threads = config["panaroo"]["threads"]
    threads:
        config["panaroo"]["threads"]
    resources:
        mem_mb = 256000,  # 256 GB for very large genome sets (6,252 genomes)
        runtime = 960     # 16 hours (inflated for first run)
    log:
        "logs/panaroo/run_panaroo.log"
    benchmark:
        "benchmarks/panaroo/run_panaroo.txt"
    conda:
        "../../envs/panaroo.yml"
    script:
        "../scripts/panaroo.py"