# ============================================
# REGLAS DE PREPROCESAMIENTO
# ============================================
# Limpia y colapsa la matriz de presencia/ausencia de genes

rule process_matrix:
 """
Preprocesa la matriz de presencia/ausencia de genes.
    
En modo FULL: usa matriz de Panaroo
En modo EXAMPLE: usa archivo de ejemplo
 """
    input:
        matrix = lambda wildcards: (
            "results/panaroo/gene_presence_absence.csv"  # !!!!!!!
            if config.get("mode") == "full" 
            else config["input"]["gene_presence_absence"]
        )
    output:
        collapsed = "data/interim/collapsed_matrix.csv",
        constant = "data/interim/constant_genes.txt",
        core = "data/interim/core_genes.txt",
        singletons = "data/interim/singletons.txt",
        non_unique_genes = "data/interim/non_unique_genes.csv",
        non_unique_genomes = "data/interim/non_unique_genomes.csv"
    params:
        roary = "--roary" if config["preprocessing"]["roary_format"] else ""
    log:
        "logs/preprocessing/process_matrix.log"
    conda:
        "../../envs/py.yml"
    shell: #! pasar ejecucion a directiva script 
        """
        python workflow/scripts/process_matrix.py \
            -i {input.matrix} \
            {params.roary} \
            -o {output.collapsed} \
            > {log} 2>&1
        
        # Mover archivos auxiliares a data/interim
        mv constant_genes.txt {output.constant} 2>/dev/null || true
        mv core_genes.txt {output.core} 2>/dev/null || true
        mv singletons.txt {output.singletons} 2>/dev/null || true
        mv non-unique_genes.csv {output.non_unique_genes} 2>/dev/null || true
        mv non-unique_genomes.csv {output.non_unique_genomes} 2>/dev/null || true
        
        echo "✓ Preprocesamiento completado" >> {log}
        """
