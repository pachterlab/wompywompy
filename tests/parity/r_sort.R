#!/usr/bin/env Rscript
# Sorting parity harness -- R side.
#
# Reads a JSON file of parity cases, sorts each with the *reference* R
# implementation (wompwomp::sort_to_uncross), and writes a JSON file of
# {case_id, order} where `order` is the block order of every axis.
#
# `default_sorting = "fixed"` makes R start from the order the blocks appear in
# the data, which is where wompywompy starts; `column_method = "none"` keeps the
# axis order out of it, so only the stratum orders are compared.
#
# Usage:
#   Rscript r_sort.R <cases.json> <out.json> [path-to-wompwomp-repo]

suppressWarnings(suppressMessages({
  library(jsonlite)
}))

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) stop("usage: Rscript r_sort.R <cases.json> <out.json> [wompwomp-repo]")
cases_path <- args[[1]]
out_path <- args[[2]]
if (length(args) >= 3) {
  repo <- normalizePath(args[[3]], mustWork = TRUE)
} else {
  this_file <- sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE))
  repo <- normalizePath(file.path(dirname(this_file), "..", "..", "..", "wompwomp"), mustWork = TRUE)
}

suppressWarnings(suppressMessages(pkgload::load_all(repo, quiet = TRUE)))

cases <- jsonlite::fromJSON(cases_path, simplifyDataFrame = FALSE)

out <- lapply(cases, function(case) {
  cols <- unlist(case$cols)
  df <- do.call(rbind, lapply(case$rows, function(row) {
    as.data.frame(row, stringsAsFactors = FALSE)
  }))
  for (col in cols) df[[col]] <- as.character(df[[col]])
  fixed <- if (length(case$fixed) == 0) NULL else unlist(case$fixed)

  sorted <- sort_to_uncross(
    df, cols = cols, wt = "value",
    method = case$method, column_method = "none", fixed_column = fixed,
    options = list(default_sorting = "fixed")
  )
  list(case_id = case$case_id,
       order = lapply(setNames(cols, cols), function(col) levels(sorted[[col]])))
})

writeLines(jsonlite::toJSON(out, auto_unbox = TRUE), out_path)
