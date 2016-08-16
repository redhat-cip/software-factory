#!/bin/env python

import os
import yaml


def loadConfig(config_path):
    """Load layout configuration whenever it is a single file or a directory.
       If it's a directory, this will walk through each .yaml file and performs
       a simple yaml merge"""
    config_path = os.path.expanduser(config_path)
    if not os.path.exists(config_path):
        raise Exception("Unable to read layout config path at %s" %
                        config_path)

    # Discover all files in config_path
    paths = []
    if os.path.isdir(config_path):
        for root, dirs, files in os.walk(config_path, topdown=True):
            paths.extend([os.path.join(root, path) for path in files])
    else:
        paths.append(config_path)

    # Keeps only .yaml files
    paths = filter(lambda x: x.endswith('.yaml') or x.endswith('.yml'), paths)
    # make sure layout.yaml is the first one
    if '%s/_layout.yaml' % config_path in paths:
        paths.remove('%s/_layout.yaml' % config_path)
        paths.insert(0, '%s/_layout.yaml' % config_path)

    final_data = {}
    for path in paths:
        data = yaml.load(open(path))
        if not data:
            continue
        # Merge document
        for key in data:
            if key in final_data:
                try:
                    final_data[key] += data[key]
                except:
                    raise RuntimeError("Could not merge '%s' from %s" %
                                       (key, path))
            else:
                final_data[key] = data[key]
    return final_data


def main(argv):
    if len(argv) != 2 and not os.path.isdir(argv[1]):
        print "usage: %s dir" % argv[0]
    data = loadConfig(argv[1])
    print yaml.dump(data, indent=4)

if __name__ == "__main__":
    import sys
    main(sys.argv)
