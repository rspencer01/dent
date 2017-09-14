import pycfg
import args
import os
import sys

PMRC = os.getenv("HOME")+'/.dent.cfg'

config = pycfg.load(PMRC, 'configuration_schema.yml')

if not os.path.exists(PMRC) or args.args.remake_config_file:
  config.write_default_file(PMRC)

if args.args.remake_config_file:
  sys.exit(0)
