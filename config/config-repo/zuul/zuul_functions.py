#!/usr/bin/python


def set_node_reuse(item, job, params):
    print "zuul_functions: set_node_reuse(", item, job, "): "
    params['OFFLINE_NODE_WHEN_COMPLETE'] = '0'


def set_node_options(item, job, params):
    if job.name in ('config-check', 'config-update', 'sf-mirror-update'):
        # Prevent putting master node offline
        params['OFFLINE_NODE_WHEN_COMPLETE'] = '0'
        return
    print "zuul_functions: set_node_options(", item, job, "): "
    params['OFFLINE_NODE_WHEN_COMPLETE'] = '1'
