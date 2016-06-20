# This patch fixes:
# File "pbr/packaging.py", line 640, in get_version
#    raise Exception("Versioning for this project requires either an sdist")
# Exception: Versioning for this project requires either an sdist tarball, or
#            access to an upstream git repository.
__version__ = '1.0.0'
