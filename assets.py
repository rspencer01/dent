import hashlib
import os
import cPickle as pickle
import numpy as np
import logging

if not os.path.exists('./_assets'):
  os.mkdir('./_assets')

def getInternalAssetID(assetID):
  return hashlib.sha256(repr(assetID)).hexdigest()[:16]

def getFilename(assetID):
  return './_assets/{}'.format(assetID)

def getType(assetID):
  if open(getFilename(assetID)).read(6) == '\x93NUMPY':
    return 'numpy'
  return 'pickle'

def loadFromFile(filename):
  try:
    obj = np.load(filename)
    logging.info("Loaded object as numpy array")
    return obj
  except IOError as e:
    pass
  try:
    obj = pickle.load(open(filename, 'rb'))
    logging.info("Loaded object as python pickle")
    return obj
  finally:
    pass
  raise Exception("Unknown format.")

def saveToFile(obj, filename, assetName='<unknown>'):
  if type(obj) in [np.ndarray]:
    logging.info("Saving object as numpy array")
    np.save(open(filename, 'wb'), obj)
  else:
    logging.info("Saving object as python pickle")
    pickle.dump(obj, open(filename, 'wb'))
  with open(filename+'.meta', 'w') as f:
    f.write("{}\n".format(assetName))

def getAsset(assetName, function=None, args=(), forceReload=False):
  logging.info("Loading asset '{}'".format(assetName))
  assetID = getInternalAssetID(assetName)
  if forceReload and function is None:
    raise Exception("Must specify generation function if reloading asset.")

  filename = getFilename(assetID)
  if os.path.exists(filename) and not forceReload:
    return loadFromFile(filename)

  obj = function(*args)

  saveToFile(obj, filename, assetName)

  return obj

def getAllAssetIds():
  return [i for i in sorted(os.listdir('_assets')) if 'meta' not in i]

def getAssetName(assetID):
  if assetID+'.meta' not in os.listdir('_assets'):
    return '-'
  return open('_assets/'+assetID+'.meta').readlines()[0].strip()

if __name__ == "__main__":
  print "{: <20.20} {: <16} {: >9} {}".format("Name", "ID", "Size (kb)", "Type")
  for asset in getAllAssetIds():
    print "{: <20.20} {: <16} {: >9,} {}".format(
        getAssetName(asset),
        asset, 
        os.path.getsize(getFilename(asset))/1024,
        getType(asset)
        )
