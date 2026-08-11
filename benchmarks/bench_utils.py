"""Subprocess-isolated timing/resource harness.

Each benchmark config runs in its own child process so that:
  - a hung config (e.g. exact-TSP sorting on too many categories) can be
    killed on a timeout instead of blocking the rest of the sweep.
  - a crashing config doesn't take down the sweep process.
  - peak RSS (resource.getrusage) reflects that one run, not accumulated
    state left over from earlier configs in the same interpreter.

Peak RSS includes the fixed cost of importing numpy/pandas/matplotlib/igraph
in the child, so treat absolute numbers as having a shared baseline offset --
differences *between* configs are what's meaningful.
"""

import multiprocessing as mp
import resource
import time
import traceback


def _worker(target_fn, params, result_queue):
    start = time.perf_counter()
    try:
        extra = target_fn(params) or {}
        status, error = "ok", None
    except Exception:
        extra = {}
        status, error = "error", traceback.format_exc()
    wall_time_s = time.perf_counter() - start
    usage = resource.getrusage(resource.RUSAGE_SELF)
    result = {
        "status": status,
        "error": error,
        "wall_time_s": wall_time_s,
        "user_cpu_s": usage.ru_utime,
        "sys_cpu_s": usage.ru_stime,
        "peak_rss_mb": usage.ru_maxrss / 1024,  # ru_maxrss is KB on Linux
    }
    result.update(extra)
    result_queue.put(result)


def run_isolated(target_fn, params, timeout_s=600):
    """Run target_fn(params) in a subprocess with a wall-clock timeout.

    target_fn must be a top-level (picklable) function taking a single dict
    argument. It may return a dict of extra fields to merge into the result
    (e.g. n_unique_alluvia); anything it raises is captured as status="error".
    """
    ctx = mp.get_context("spawn")
    result_queue = ctx.Queue()
    proc = ctx.Process(target=_worker, args=(target_fn, params, result_queue))
    start = time.perf_counter()
    proc.start()
    proc.join(timeout_s)

    if proc.is_alive():
        proc.terminate()
        proc.join(5)
        if proc.is_alive():
            proc.kill()
            proc.join()
        return {
            "status": "timeout",
            "error": f"exceeded {timeout_s}s",
            "wall_time_s": time.perf_counter() - start,
            "user_cpu_s": None,
            "sys_cpu_s": None,
            "peak_rss_mb": None,
        }

    if not result_queue.empty():
        return result_queue.get()

    return {
        "status": "crashed",
        "error": f"process exited with code {proc.exitcode}, no result produced",
        "wall_time_s": time.perf_counter() - start,
        "user_cpu_s": None,
        "sys_cpu_s": None,
        "peak_rss_mb": None,
    }
