#!/usr/bin/env python3
"""Process the matrix so that it's ready for analysis."""

import argparse
import re
import sys
import math
import pandas as pd
import rf_module as rf


def get_args():
    """Get arguments from Snakemake or command line."""
    # Check if running from Snakemake
    try:
        infile = snakemake.input.matrix
        outfile = snakemake.output.collapsed
        roary = snakemake.params.roary_format
        # Get output paths for auxiliary files
        output_paths = {
            'constant': snakemake.output.constant,
            'core': snakemake.output.core,
            'singletons': snakemake.output.singletons,
            'non_unique_genes': snakemake.output.non_unique_genes,
            'non_unique_genomes': snakemake.output.non_unique_genomes
        }
        return [infile, outfile, roary, output_paths]
    except NameError:
        # Running from command line
        parser = argparse.ArgumentParser()
        parser.add_argument("-i", "--infile", dest = "infile",
                            type = str, help = "input file")
        parser.add_argument("-r", "--roary", dest = "roary",
                            help = "toggle for roary input",
                            action = "store_true")
        parser.add_argument("-o", "--output", dest = "outfile",
                            type = str, help = "Output matrix file")
        args = parser.parse_args()
        if None in [args.infile, args.outfile]:
            parser.print_help(sys.stderr)
            sys.exit(0)
        return [args.infile, args.outfile, args.roary, None]

def write_gene_lists(matrix, output_paths=None):
    """
    Write the files - singletons.txt, core_genes.txt, constant_genes.txt.
    """
    constant = list(matrix[matrix.sum(axis = 1) == matrix.shape[1]].index)
    threshold = math.ceil(0.05 * matrix.shape[1])
    core = list(matrix[matrix.sum(axis = 1) >= threshold].index)
    singletons = list(matrix[matrix.sum(axis = 1) == 1].index)

    # Use output_paths if provided (from Snakemake), otherwise use current directory
    constant_file = output_paths['constant'] if output_paths else "constant_genes.txt"
    core_file = output_paths['core'] if output_paths else "core_genes.txt"
    singletons_file = output_paths['singletons'] if output_paths else "singletons.txt"

    with open(constant_file, "w", encoding = "utf-8") as out:
        out.write("\n".join(constant))
    with open(core_file, "w", encoding = "utf-8") as out:
        out.write("\n".join(core))
    with open(singletons_file, "w", encoding = "utf-8") as out:
        out.write("\n".join(singletons))

    matrix = matrix.drop(index = constant)
    matrix = matrix.drop(index = singletons)
    return matrix

def collapse_genes(matrix, output_paths=None):
    """Collapse genes with the same presence absence pattern."""
    colapsed_rows = pd.DataFrame(columns = matrix.columns)
    identical_sets = {}
    count = 0
    pattern = 0
    indices  = []
    non_unique = matrix[matrix.duplicated(keep = False)]
    non_unique = non_unique.sort_values(by = list(non_unique.columns))
    for i in range(len((matrix[matrix.duplicated(keep = False)].index))):
        if list(non_unique.iloc[i]) == pattern:
            identical_sets["family_group_" + str(count)].append(non_unique.iloc[i].name)
        else:
            colapsed_rows.loc[count] = list(non_unique.iloc[i])
            pattern = list(non_unique.iloc[i])
            count += 1
            indices.append("family_group_" + str(count) + ",,family_group")
            identical_sets["family_group_" + str(count)] = [non_unique.iloc[i].name]

    colapsed_rows.index = indices

    # Use output_paths if provided (from Snakemake), otherwise use current directory
    non_unique_genes_file = output_paths['non_unique_genes'] if output_paths else "non-unique_genes.csv"

    with open(non_unique_genes_file, "w", encoding = "utf-8") as out:
        for key, value in identical_sets.items():
            out.write(key + "\t" + ",".join(value) + "\n")
    matrix = matrix.drop_duplicates(keep = False)
    matrix = pd.concat([matrix, colapsed_rows])
    return matrix

def collapse_genomes(matrix, output_paths=None):
    """Collapse genomes with identical presence absence patterns."""
    matrix = matrix.transpose()
    colapsed_genomes = pd.DataFrame(columns = matrix.columns)
    identical_sets = {}
    count = 0
    pattern = 0
    indices  = []
    non_unique = matrix[matrix.duplicated(keep = False)]
    non_unique = non_unique.sort_values(by = list(non_unique.columns))

    for i in range(len((matrix[matrix.duplicated(keep = False)].index))):
        if list(non_unique.iloc[i]) == pattern:
            identical_sets["genome_group_" + str(count)].append(non_unique.iloc[i].name)
        else:
            pattern = list(non_unique.iloc[i])
            colapsed_genomes.loc[count] = list(non_unique.iloc[i])
            count += 1
            indices.append("genome_group_" + str(count))
            identical_sets["genome_group_" + str(count)] = [non_unique.iloc[i].name]

    colapsed_genomes.index = indices

    # Use output_paths if provided (from Snakemake), otherwise use current directory
    non_unique_genomes_file = output_paths['non_unique_genomes'] if output_paths else "non-unique_genomes.csv"

    with open(non_unique_genomes_file, "w", encoding = "utf-8") as out:
        for key, value in identical_sets.items():
            out.write(key + "\t" + ",".join(value) + "\n")
    matrix = matrix.drop_duplicates(keep = False)
    matrix = pd.concat([matrix, colapsed_genomes])
    matrix = matrix.transpose()
    return matrix

def convert_roary(roary_matrix):
    """
    Convert Roary matrix into panaroo by removing several columns.
    There are 14 roary header cols and 3 panaroo
    there are also commas in the values of the PA matrix of roary
    """
    index = roary_matrix.index
    names = index.names
    new_index = []
    for ind in index:
        if "," in ind[2]:
            new_index = new_index + [(ind[0], ind[1], ind[2].replace(",",";"))]
        else:
            new_index.append(ind)
    roary_matrix.index = pd.MultiIndex.from_tuples(new_index, names = names)
    roary_matrix = roary_matrix.replace(',',';', regex=True)
    cols = range(11)
    roary_matrix.drop(roary_matrix.columns[cols], axis=1, inplace=True)
    return roary_matrix


def main():
    """
    Preprocessing Pipeline.

    Remove constant genes - writing their names to a file.
    Remove genes with identical patterns of presence/absence and write to
    a file.
    Remove genomes with identical gene presence/absence patterns and write
    them to a file.
    Write the new matrix to a file.
    """
    infile, outfile, roary, output_paths = get_args()
    matrix = pd.read_csv(infile, header = 0, index_col = [0,1,2], dtype = str)
    if roary:
        matrix = convert_roary(matrix)
    #remove genes with < 2 present/absent
    matrix = rf.preprocess_df(matrix, 0, 0, 0)
    print("Writing singletons, core and constant genes")
    matrix = write_gene_lists(matrix, output_paths)

    print("Collapsing identical genes and genomes")
    matrix = collapse_genes(matrix, output_paths)
    matrix = collapse_genomes(matrix, output_paths)

    #now write matrix to a file
    print("Writing collapsed matrix")
    matrix.to_csv(outfile, sep = ",", doublequote=False)
    lines = rf.get_file_data(outfile)
    with open(outfile, "w", encoding = "utf8") as out:
        out.write(",," + lines[0] + "\n")
        for line in lines[1:]:
            out.write(re.sub("\"", "", line) + "\n")
#        out.write("\n".join([line.strip('"') for line.maketrans("\"", "") in lines[1:]]))

if __name__ == "__main__":
    main()
