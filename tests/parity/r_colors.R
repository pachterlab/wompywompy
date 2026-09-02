#!/usr/bin/env Rscript
# Colour parity harness -- R side. Reads the cases JSON written by
# run_color_parity.py, and for each case + method emits R's colour partition
# {col: {value: community}} plus the advanced block-overlap graph edge list.
suppressWarnings(suppressMessages({
  library(jsonlite)
  library(wompwomp)
}))

args <- commandArgs(trailingOnly = TRUE)
cases <- fromJSON(args[[1]], simplifyVector = FALSE)
out <- vector("list", length(cases))

for (ci in seq_along(cases)) {
  case <- cases[[ci]]
  cols <- unlist(case$cols)
  rows <- do.call(rbind, lapply(case$rows, function(r) {
    as.data.frame(as.list(unlist(r)), stringsAsFactors = FALSE)
  }))
  rows$value <- as.numeric(rows$value)
  for (cn in cols) {
    rows[[cn]] <- factor(as.character(rows[[cn]]),
                         levels = as.character(unlist(case$levels[[cn]])))
  }
  g <- prep_for_lodes(rows, cols = cols, wt = "value",
                      do_gather_set_data = FALSE, do_add_int_columns = TRUE)

  res <- list()
  for (m in c("left", "right", cols[[1]], "advanced")) {
    set.seed(1)
    cm <- tryCatch(
      get_lode_clusters(g, cols = cols, wt = "value", method = m, resolution = 1,
                        options = get_lode_clusters_options(preprocess_data = FALSE)),
      error = function(e) NULL
    )
    key <- if (m == "advanced") "advanced" else if (m == cols[[1]]) "named" else m
    res[[key]] <- cm
  }
  out[[ci]] <- list(case_id = case$case_id, partitions = res)
}

write(toJSON(out, auto_unbox = TRUE, null = "null"), args[[2]])
