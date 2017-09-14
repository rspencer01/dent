import yaml
import os
from Configuration import Configuration

def load(filename, schema_filename):
  try:
    schema = yaml.load(open(schema_filename).read())
  except IOError as e:
    schema = {}
  cfg = Configuration(schema)
  if os.path.exists(filename):
    cfg.read(filename)
  return cfg

if __name__ == '__main__':
  c = load('main.cfg', 'example_schema.yaml')
  c.write_default_file('default.cfg')
  print c
