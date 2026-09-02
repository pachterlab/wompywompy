#!/usr/bin/env Rscript
# Parity harness -- R side.
#
# Reads a JSON file of parity cases, computes the W_POMP crossing objective for
# each with the *reference* R implementation (wompwomp::compute_crossing_objective),
# and writes a JSON file of {case_id, r_objective, r_bruteforce}.
#
# The R package cannot be install/library()'d in every environment (it pulls in a
# newer igraph than some R installs ship, only for the W_LOMP colouring path), so
# this sources just the files the objective path needs:
#   src/fenwick.cpp, R/utils.R, R/objective_calculation.R
# None of those touch igraph at load time.
#
# Usage:
#   Rscript r_objective.R <cases.json> <out.json> [path-to-wompwomp-repo]

suppressWarnings(suppressMessages({
  library(jsonlite)
  library(Rcpp)
}))

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) stop("usage: Rscript r_objective.R <cases.json> <out.json> [wompwomp-repo]")
cases_path <- args[[1]]
out_path <- args[[2]]
if (length(args) >= 3) {
  repo <- normalizePath(args[[3]], mustWork = TRUE)
} else {
  this_file <- sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE))
  repo <- normalizePath(file.path(dirname(this_file), "..", "..", "..", "wompwomp"), mustWork = TRUE)
}

sourceCpp(file.path(repo, "src", "fenwick.cpp"))
source(file.path(repo, "R", "utils.R"))
source(file.path(repo, "R", "objective_calculation.R"))

# Independent O(n^2) crossing objective for the *given* layout, used to
# self-check the Fenwick result. `pos_a`, `pos_b` are the within-layer y
# positions (rank order) of each alluvium in the two layers of a pair.
brute_pair <- function(pos_l, pos_r, w) {
  n <- length(w)
  total <- 0
  if (n < 2) return(0)
  for (i in 1:(n - 1)) {
    for (j in (i + 1):n) {
      dl <- sign(pos_l[i] - pos_l[j])
      dr <- sign(pos_r[i] - pos_r[j])
      if (dl != 0 && dr != 0 && dl != dr) total <- total + w[i] * w[j]
    }
  }
  total
}

cases <- fromJSON(cases_path, simplifyVector = FALSE)
results <- vector("list", length(cases))

for (ci in seq_along(cases)) {
  case <- cases[[ci]]
  cols <- unlist(case$cols)
  m <- length(cols)
  rows <- case$rows

  df <- as.data.frame(do.call(rbind, lapply(rows, function(r) {
    setNames(data.frame(as.list(unlist(r)), stringsAsFactors = FALSE), c(cols, "value"))
  })), stringsAsFactors = FALSE)
  df$value <- as.numeric(df$value)
  for (i in seq_along(cols)) {
    lv <- unlist(case$levels[[cols[i]]])
    df[[cols[i]]] <- factor(as.character(df[[cols[i]]]), levels = as.character(lv))
  }

  res <- compute_crossing_objective(df, cols = cols, wt = "value", weighted_metric = TRUE)
  fen <- res$output_objective

  # brute force on the same lode_df layout the package built
  lode <- res$lode_df
  bf <- 0
  for (h in seq_len(m - 1)) {
    yl <- rank(lode[[paste0("y", h)]], ties.method = "min")
    yr <- rank(lode[[paste0("y", h + 1)]], ties.method = "min")
    bf <- bf + brute_pair(yl, yr, lode$value)
  }

  results[[ci]] <- list(case_id = case$case_id, r_objective = fen, r_bruteforce = bf)
}

write(toJSON(results, auto_unbox = TRUE, digits = 10), out_path)
