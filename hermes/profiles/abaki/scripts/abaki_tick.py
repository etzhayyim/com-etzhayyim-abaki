#!/usr/bin/env python3
"""Host-bound cron entrypoint; execution paths are configured by the owner."""
import json
from pathlib import Path
import runpy
import sys

config_file=Path(__file__).resolve().parents[1]/'execution.json'
config=json.loads(config_file.read_text())
pipeline=Path(config['pipeline'])
if not pipeline.is_absolute() or not pipeline.is_file():
    raise RuntimeError('Bind the immutable owner pipeline before activating this job')
sys.argv=[str(pipeline),'--config',str(config_file)]
runpy.run_path(str(pipeline),run_name='__main__')
