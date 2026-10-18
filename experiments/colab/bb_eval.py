"""Run `lerobot-eval` with the bounded-brain trace logger switched on.

Usage (same flags as lerobot-eval):
    BB_TRACE_DIR=/path/to/traces BB_RUN_TAG=pi05_spatial BB_POLICY=lerobot/pi05_libero_finetuned \
        python bb_eval.py --policy.path=lerobot/pi05_libero_finetuned --env.type=libero ...

BB_MAX_VIDEOS (default 1) caps how many episodes per task lerobot-eval renders to mp4.
lerobot 0.6.1 renders up to 10 per task, which re-renders a frame every step; the
traces already allow exact offline replay, so a single video per task is enough.
"""

import os
import sys

import bb_trace  # noqa: F401  (patches LiberoEnv before any env is created)
import lerobot.scripts.lerobot_eval as _le

_MAX_VIDEOS = int(os.environ.get("BB_MAX_VIDEOS", "1"))
_orig_eval_policy = _le.eval_policy


def _eval_policy(*args, **kwargs):
    if "max_episodes_rendered" in kwargs:
        kwargs["max_episodes_rendered"] = min(int(kwargs["max_episodes_rendered"]), _MAX_VIDEOS)
    return _orig_eval_policy(*args, **kwargs)


_le.eval_policy = _eval_policy

if __name__ == "__main__":
    sys.argv[0] = "lerobot-eval"
    _le.main()
