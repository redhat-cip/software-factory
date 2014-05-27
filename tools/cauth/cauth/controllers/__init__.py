from M2Crypto import RSA
from pecan import conf

rsa_priv = RSA.load_key(conf.app['priv_key_path'])
