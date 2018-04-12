import hashlib
import logging
import os
import tarfile
import cPickle as pickle
import numpy as np

if not os.path.exists("./_assets"):
    os.mkdir("./_assets")


def getInternalAssetID(assetID):
    return hashlib.sha256(repr(assetID)).hexdigest()[:16]


def getFilename(assetID):
    """Finds the path of an asset by its ID."""
    return os.path.join(".", "_assets", assetID)


def get_asset_metadata(assetID):
    if assetID + ".meta" not in os.listdir("_assets"):
        raise Exception("Asset not present")

    lines = map(lambda x: x.strip(), open("_assets/" + assetID + ".meta").readlines())
    return {"name": lines[0], "type": lines[1]}


def loadFromFile(filename, type_hint=None):
    if hasattr(type_hint, "_dent_asset_load"):
        if tarfile.is_tarfile(filename):
            datastore = tarfile.open(filename, "r")
            obj = type_hint._dent_asset_load(datastore)
            datastore.close()
            return obj
    try:
        obj = np.load(filename)
        logging.debug("Loaded object as numpy array")
        return obj

    except IOError as e:
        pass
    try:
        obj = pickle.load(open(filename, "rb"))
        logging.debug("Loaded object as python pickle")
        return obj

    finally:
        pass
    raise Exception("Unknown format.")


def saveToFile(obj, filename, assetName="<unknown>"):
    if hasattr(obj, "_dent_asset_save"):
        datastore = tarfile.open(filename, "w")
        obj._dent_asset_save(datastore)
        datastore.close()
        asset_type = type(obj).__name__
    elif type(obj) in [np.ndarray]:
        logging.debug("Saving object as numpy array")
        np.save(open(filename, "wb"), obj)
        asset_type = "numpy"
    else:
        logging.debug("Saving object as python pickle")
        pickle.dump(obj, open(filename, "wb"))
        asset_type = "pickle"
    with open(filename + ".meta", "w") as f:
        f.write("{}\n{}\n".format(assetName, asset_type))


def getAsset(assetName, function=None, args=(), forceReload=False, type_hint=None):
    logging.info("Loading asset '{}'".format(assetName))
    assetID = getInternalAssetID(assetName)
    if forceReload and function is None:
        raise Exception("Must specify generation function if reloading asset.")

    filename = getFilename(assetID)
    if os.path.exists(filename) and not forceReload:
        return loadFromFile(filename, type_hint)

    if not function:
        raise Exception("Asset not found")

    obj = function(*args)

    saveToFile(obj, filename, assetName)

    return obj


def saveAsset(assetName, value):
    assetID = getInternalAssetID(assetName)
    filename = getFilename(assetID)
    saveToFile(value, filename, assetName)


def getAllAssetIds():
    return [i for i in sorted(os.listdir("_assets")) if "meta" not in i]


def getAssetName(assetID):
    return get_asset_metadata(assetID)["name"]


def get_asset_type(assetID):
    return get_asset_metadata(assetID)["type"]
