
#!/usr/bin/env python3
"""
Deduplicate GCA vs GCF assemblies.
If both GCA and GCF exist for same genome, keep GCA. If only GCF exists, then keep GCF
"""
import json
from pathlib import Path
from collections import defaultdict

def parse_metadata(metadata_file):
    """Parse NCBI metadata JSON lines"""
    genomes = []
    with open(metadata_file) as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                genomes.append(data)
    return genomes

def deduplicate_assemblies(genomes):
    """
    Deduplicate GCA vs GCF based on assembly name.
    """
    # group by assembly name
    assembly_groups = defaultdict(list)
    
    for genome in genomes:
        accession = genome['accession']
        assembly_name = genome['assembly_info']['assembly_name']
        assembly_groups[assembly_name].append({
            'accession': accession,
            'type': 'GCA' if accession.startswith('GCA_') else 'GCF',
            'genome': genome
        })
    
    # select one per group
    selected = []
    stats = {'total_groups': 0, 'gca_preferred': 0, 'gcf_only': 0}
    
    for assembly_name, assemblies in assembly_groups.items():
        stats['total_groups'] += 1
        
        # check if GCA exists
        gca_assemblies = [a for a in assemblies if a['type'] == 'GCA']
        gcf_assemblies = [a for a in assemblies if a['type'] == 'GCF']
        
        if gca_assemblies:
            # prefer GCA
            selected.append(gca_assemblies[0]['accession'])
            stats['gca_preferred'] += 1
        elif gcf_assemblies:
            # only GCF available
            selected.append(gcf_assemblies[0]['accession'])
            stats['gcf_only'] += 1
    
    return selected, stats

def main():
    metadata_file = snakemake.input.metadata
    accessions_file = snakemake.output.accessions
    stats_file = snakemake.output.stats
    
    print("Parsing metadata...")
    genomes = parse_metadata(metadata_file)
    print(f"  Total genomes in metadata: {len(genomes)}")
    
    print("Deduplicating GCA/GCF assemblies...")
    selected_accessions, stats = deduplicate_assemblies(genomes)
    
    # write accessions list
    with open(accessions_file, 'w') as f:
        f.write('\n'.join(selected_accessions) + '\n')
    
    # write stats
    with open(stats_file, 'w') as f:
        f.write(f"Deduplication Statistics\n")
        f.write(f"========================\n")
        f.write(f"Total assembly groups: {stats['total_groups']}\n")
        f.write(f"GCA preferred (had both): {stats['gca_preferred']}\n")
        f.write(f"GCF only (no GCA): {stats['gcf_only']}\n")
        f.write(f"\nFinal unique genomes: {len(selected_accessions)}\n")
    
    print(f" Selected {len(selected_accessions)} unique genomes")
    print(f"  - {stats['gca_preferred']} GCA (preferred)")
    print(f"  - {stats['gcf_only']} GCF (only option)")

if __name__ == "__main__":
    main()

