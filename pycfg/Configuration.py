import logging
import textwrap

DEFAULTS = {
    'string' : '',
    'present' : False,
    'integer' : 0,
    'float' : 0.,
    }

class Configuration(object):
  def __init__(self, schema):
    self._schema = schema
    self._data = {}

    for key in self._schema.keys():
      key_schema = self._schema[key]
      if 'type' not in key_schema:
        self._schema[key]['type'] = 'string'
      if 'help' not in key_schema:
        self._schema[key]['help'] = ''
      if 'default' not in key_schema:
        key_schema['default'] = DEFAULTS[key_schema['type']]
      self._data[key] = key_schema['default']

  def read(self, filename):
    self.loads(open(filename).read())

  def loads(self, string):
    for line in string.split('\n'):
      if line:
        self.parseline(line)

  def parseline(self, line):
    if line.lstrip()[0] == '#':
      return
    if ':' not in line:
      line = line+':'
    key,value = map(lambda x:x.strip(), line.split(':', 1))
    key, value = self.parse_key_val(key, value)
    if value == '':
      self._data[key] = True
    else:
      self._data[key] = value

  def parse_key_val(self, key, value):
    if key not in self._schema:
      logging.warn("Key '{}' not in schema.".format(key))
      return key, value
    if self._schema[key]['type'] == 'present':
      if value:
        logging.warn("Key '{}' is type 'present' but has value".format(key))
      return key, True
    if self._schema[key]['type'] == 'integer':
      return key, int(value)
    if self._schema[key]['type'] == 'float':
      return key, float(value)
    return key, value

  def write_default_file(self, filename):
    f = open(filename, 'w')
    for key in self._schema:
      f.write('# {}\n'.format(key))
      f.write('#\n')
      if self._schema[key]['help']:
        f.write(textwrap.fill(
          self._schema[key]['help'],
          initial_indent='# ',
          subsequent_indent='# ',
          replace_whitespace=True)
          +'\n')
      if self._schema[key]['type'] == 'present':
        if self._schema[key]['default']:
          f.write('{}\n'.format(key))
        else:
          f.write('#{}\n'.format(key))
      else:
          f.write('{}: {}\n'.format(key, self._schema[key]['default']))
      f.write('\n')
      f.write('\n')
    f.close()

  def __getattr__(self, name):
    return self._data[name]

  def __repr__(self):
    return self._data.__repr__()

