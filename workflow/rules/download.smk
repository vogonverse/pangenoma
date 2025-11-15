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












# ============================================
# RULE: download_genomes
# ============================================



# ============================================
# RULE: index_gff_files
# ============================================
rule index_gff_files:
    """
    Create a list of all downloaded GFF files for Panaroo.
    
    Panaroo requires a file listing all input GFFs.
    This rule scans the genomes directory and creates that list.
    """
    input:
        flag = "data/raw/genomes/.download_complete"
    output:
        gff_list = "data/raw/genomes/gff_files.txt"
    params:
        genomes_dir = config["download"]["outdir"]
    log:
        "logs/download/index_gff_files.log"
    shell:
        """
        # Find all GFF files recursively and sort
        find {params.genomes_dir}/genomes -name "*.gff" -type f | sort > {output.gff_list}
        
        # Count and report
        n_files=$(wc -l < {output.gff_list})
        echo "Found $n_files GFF files" | tee -a {log}
        
        # Validate: must have at least 1 file
        if [ "$n_files" -eq 0 ]; then
            echo "ERROR: No GFF files found in {params.genomes_dir}" >&2
            exit 1
        fi
        """


# ============================================
# RULE: validate_downloads 
# ============================================
rule validate_downloads:
    """
    Validate that downloaded files are not corrupted.
    
    Checks:
    - GFF files are not empty
    - GFF files have valid format (start with ##gff-version)
    - Metadata matches actual files
    """
    input:
        metadata = "data/raw/genomes/metadata.tsv",
        gff_list = "data/raw/genomes/gff_files.txt"
    output:
        report = "data/raw/genomes/validation_report.txt"
    log:
        "logs/download/validate_downloads.log"
    shell:
        """
        echo "Validation Report" > {output.report}
        echo "=================" >> {output.report}
        echo "" >> {output.report}
        
        # Check metadata
        n_metadata=$(tail -n +2 {input.metadata} | wc -l)
        echo "Genomes in metadata: $n_metadata" >> {output.report}
        
        # Check actual files
        n_files=$(wc -l < {input.gff_list})
        echo "GFF files found: $n_files" >> {output.report}
        
        # Validate each GFF
        echo "" >> {output.report}
        echo "Checking GFF formats..." >> {output.report}
        
        invalid=0
        while IFS= read -r gff; do
            # Check if empty
            if [ ! -s "$gff" ]; then
                echo "ERROR: Empty file - $gff" >> {output.report}
                invalid=$((invalid + 1))
                continue
            fi
            
            # Check GFF header
            if ! head -n 1 "$gff" | grep -q "##gff-version"; then
                echo "WARNING: Missing GFF header - $gff" >> {output.report}
            fi
        done < {input.gff_list}
        
        echo "" >> {output.report}
        if [ "$invalid" -eq 0 ]; then
            echo "✓ All files validated successfully" >> {output.report}
        else
            echo "✗ Found $invalid invalid files" >> {output.report}
            exit 1
        fi
        
        cat {output.report} | tee {log}
        """