library(caper)
library(phytools)
library(future)
library(flock)
library(stringr)

# ============================================
# Clean up any stale lock file
# ============================================
if (file.exists("./.lock")) {
  cat("Warning: Removing stale .lock file\n")
  file.remove("./.lock")
}

# ============================================
# Configuración desde Snakemake
# ============================================
# Cuando se usa la directiva script:, Snakemake inyecta automáticamente
# el objeto 'snakemake' con input, output, params, log, threads, etc.

# Obtener parámetros desde Snakemake
opt <- list(
  phylogeny = snakemake@input[["phylogeny"]],
  gene_pa = snakemake@input[["matrix"]],
  cores = snakemake@threads[[1]],
  output = snakemake@params[["output_prefix"]]
)

# Read gene list from batch file (CSV format)
genes_df <- read.csv(snakemake@input[["gene_list"]], check.names=TRUE)
# Extract the gene_id column as a vector
genes <- genes_df$gene_id

#Read in tree
tree <- read.tree(opt$phylogeny)
# Apply same transformation as CSV headers: convert dots to underscores, then make.names()
tree$tip.label <- gsub("[.]", "_", tree$tip.label)
tree$tip.label <- make.names(tree$tip.label) #ensure tree tip names will match annot rownames
#Ensure no zero branch lengths
if (!is.na(match(0, tree$edge.length))) {
  print("Phylogeny contains pairs of tips on zero branch lengths, cannot currently simulate")
  quit()
}
#Root phylogeny for input into comparative.data
treeRt <- midpoint.root(tree)
treeRt <- makeLabel(treeRt)

#Gene_pa read in
#genepa <- read.csv(opt$gene_pa, header=T, row.names=1)
#load in line by line; if rowname of line %in% names(genes), put into annot
con = file(opt$gene_pa, "r") #GOOD
header=readLines(con, n=1) #read in line-GOOD
header=gsub("[.]", "_", header)
header.sp = strsplit(header,",") #split line into list-GOOD

header.sp[[1]] <- make.names(header.sp[[1]]) #puts "X" into the first 3 columns - not sure this is necessary
annot <- matrix(ncol=length(header.sp[[1]])) #creates an empty list of length = nrow matrix
colnames(annot) <- header.sp[[1]] #annotates them
flag <- 1
print("Read in gene_pa file..")
while(TRUE) {
  line=readLines(con, n=1) #read in line
  if (length(line)==0) {
    break #file done
  }
  line.sp = strsplit(line,",") #split line into list
  if (line.sp[[1]][1] %in% genes) {
    print(line.sp[[1]][1]) #its a gene of interest, keep around
    if (flag == 1) {
      annot[1,] <- as.character(line.sp[[1]])
      flag <- 0
    } else {
      annot <- rbind(annot, as.character(line.sp[[1]]))#, stringsAsFactors=FALSE)
    }
  }
}
close(con)
annot <- as.data.frame(annot)
rownames(annot) <- annot[,1]
annot[,1:3] <- NULL
#Make annot table
#genepa[,1:14] <- NULL
#rownames(genepa) <- gsub(" ", "", rownames(genepa))
#annot <- genepa[(rownames(genepa) %in% names(genes)),]
#genepa <- NULL
annot <- t(annot)
annot <- as.data.frame(annot)
annot$Id <- rownames(annot)
#Double check that each column has 2 states
remove <- vector()
for(a in 1:length(colnames(annot))) {
  if (length(table(annot[a])) == 1) {
    print("Encountered the following gene that only exists in one state in the data.")
    print(colnames(annot)[a])
    print("I'm removing it, but you should be cautious as to what this means...")
    remove <- append(remove, a)
  }
}
#Remove any columns with only one state
if (length(remove)>0) {
  for(a in 1:length(remove)) {
    annot[remove[a]] <- NULL
  }
}


####IAMHERE!!!!!!!!####

# DEBUG: Print diagnostic information
print("=== DIAGNOSTIC INFO ===")
print(paste("Number of tree tips:", length(treeRt$tip.label)))
print(paste("Number of annot rows:", nrow(annot)))
print("First 5 tree tip labels:")
print(head(treeRt$tip.label, 5))
print("First 5 annot rownames:")
print(head(rownames(annot), 5))
print("First 5 annot$Id:")
print(head(annot$Id, 5))
print(paste("Names in common:", sum(annot$Id %in% treeRt$tip.label)))
print("======================")

#Make comparative data object
dataset <- comparative.data(phy = treeRt,
                            data = annot,
                            names.col = Id,
                            vcv = TRUE, na.omit = FALSE, warn.dropped = TRUE)
#Estimate D (Fritz & Purvis 2010) for all columns in annot
#Detect available cores and decrease the number of parallel runs to that if its < opt$cores
availcores <- availableCores()
cores <- 1
if (availcores < opt$cores) {
  cores <- as.integer(availcores)
} else {
  cores <- opt$cores
}
print("Cores is set to:")
print(cores)
# Usar el archivo de salida definido en Snakemake
outstr <- snakemake@output[["d_stats"]]
write(paste("ID","Result",sep="\t"),file=outstr,append=FALSE)
parallelCluster <- parallel::makeCluster(cores, type="FORK")
mkWorker <- function(dataset) {
  library(flock)
  #Make sure each value is passed
  #force(dataset)
  #Define function
  calcD <- function(dataset, binvarry) {
    if(binvarry != "Id") {
      # Escape the variable name with backticks to handle special characters like ~
      escaped_var <- paste("`", binvarry, "`", sep="")
      result <- eval(parse(text=paste("caper::phylo.d(data=dataset, binvar=",escaped_var,", permut=1000)", sep="")))
      line <- paste(binvarry,result$DEstimate, sep="\t")
      locked_towrite <- flock::lock("./.lock")
      write(line,file=outstr,append=TRUE)
      flock::unlock(locked_towrite)
      rm(result)
    }
  }
  #Define & return worker function
  worker <- function(binvarry) {
    calcD(dataset, binvarry)
  }
  return(worker)
}
#results <- parallel::parLapply(parallelCluster, colnames(annot), mkWorker(dataset))
parallel::parLapply(parallelCluster, colnames(annot), mkWorker(dataset))
# Shutdown cluster neatly
if(!is.null(parallelCluster)) {
  parallel::stopCluster(parallelCluster)
  parallelCluster <- c()
}