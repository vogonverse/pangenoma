"""
Deduplicate assembly accessions based on accession base ID.

Deduplication strategy:
1. Group by accession number (e.g., GCA_000123456.1 and GCF_000123456.2 -> same group)
2. Prefer GCA_ over GCF_ when both exist for the same genome
3. When multiple versions exist (e.g., .1, .2, .3), keep the latest version
4. Apply max_genomes limit AFTER deduplication (if configured)
5. Output: one accession per unique genome

Configuration:
- Set max_genomes in config.yaml to limit number of genomes
- Unset/comment max_genomes to download all deduplicated genomes
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
    Deduplicate GCA vs GCF based on accession base (without version).
    If both GCA and GCF exist for same genome ID, prefer GCA.
    If multiple versions exist, prefer the latest version.
    """
    # group by accession base
    assembly_groups = defaultdict(list)

    for genome in genomes:
        accession = genome['accession']

        # Extract base accession without version
        parts = accession.split('_')
        if len(parts) >= 2:
            accession_number = parts[1].split('.')[0]  # Remove version
            assembly_groups[accession_number].append({
                'accession': accession,
                'type': 'GCA' if accession.startswith('GCA_') else 'GCF',
                'version': int(parts[1].split('.')[1]) if '.' in parts[1] else 1,
                'genome': genome
            })

    # select one per group
    selected = []
    stats = {'total_groups': 0, 'gca_preferred': 0, 'gcf_only': 0, 'version_dedup': 0}

    for accession_number, assemblies in assembly_groups.items():
        stats['total_groups'] += 1

        # Separate GCA and GCF
        gca_assemblies = [a for a in assemblies if a['type'] == 'GCA']
        gcf_assemblies = [a for a in assemblies if a['type'] == 'GCF']

        # Prefer GCA over GCF
        if gca_assemblies:
            # Sort by version (descending) to get latest
            gca_assemblies.sort(key=lambda x: x['version'], reverse=True)
            selected.append(gca_assemblies[0]['accession'])
            stats['gca_preferred'] += 1
            if len(gca_assemblies) > 1:
                stats['version_dedup'] += len(gca_assemblies) - 1
        elif gcf_assemblies:
            # Sort by version (descending) to get latest
            gcf_assemblies.sort(key=lambda x: x['version'], reverse=True)
            selected.append(gcf_assemblies[0]['accession'])
            stats['gcf_only'] += 1
            if len(gcf_assemblies) > 1:
                stats['version_dedup'] += len(gcf_assemblies) - 1

    return selected, stats

def main():
    metadata_file = snakemake.input.metadata
    accessions_file = snakemake.output.accessions
    stats_file = snakemake.output.stats

    # Get max_genomes from config (if specified)
    max_genomes = snakemake.config["download"].get("max_genomes")

    print("Parsing metadata...")
    genomes = parse_metadata(metadata_file)
    print(f"  Total genomes in metadata: {len(genomes)}")

    print("Deduplicating GCA/GCF assemblies...")
    selected_accessions, stats = deduplicate_assemblies(genomes)

    # Apply limit AFTER deduplication (if specified)
    total_deduplicated = len(selected_accessions)
    if max_genomes and len(selected_accessions) > max_genomes:
        print(f"  Limiting to first {max_genomes} genomes (from {len(selected_accessions)} deduplicated)")
        selected_accessions = selected_accessions[:max_genomes]
        stats['limited'] = True
        stats['total_before_limit'] = total_deduplicated
    else:
        stats['limited'] = False

    # write accessions list
    with open(accessions_file, 'w') as f:
        f.write('\n'.join(selected_accessions) + '\n')

    # write stats
    with open(stats_file, 'w') as f:
        f.write(f"Deduplication Statistics\n")
        f.write(f"========================\n")
        f.write(f"Total assembly groups (by accession base): {stats['total_groups']}\n")
        f.write(f"GCA preferred (had both GCA/GCF): {stats['gca_preferred']}\n")
        f.write(f"GCF only (no GCA alternative): {stats['gcf_only']}\n")
        f.write(f"Duplicate versions removed: {stats['version_dedup']}\n")
        f.write(f"\nTotal after deduplication: {total_deduplicated}\n")
        if stats['limited']:
            f.write(f"Limited to: {len(selected_accessions)} genomes\n")
        f.write(f"\nFinal unique genomes: {len(selected_accessions)}\n")

    print(f" Selected {len(selected_accessions)} unique genomes")
    print(f"  - {stats['gca_preferred']} GCA (preferred)")
    print(f"  - {stats['gcf_only']} GCF (only option)")
    print(f"  - {stats['version_dedup']} duplicate versions removed")
    if stats['limited']:
        print(f"  - Limited from {total_deduplicated} to {len(selected_accessions)} genomes")

if __name__ == "__main__":
    main()

