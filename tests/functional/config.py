#!/bin/env python

import os
import yaml

SF_BOOTSTRAP_DATA = "%s/sf-bootstrap-data" % os.getcwd()
SF_TESTS_DIR = "./tests"

# Remove http[s] proxy settings for functional tests
if "http_proxy" in os.environ:
    del os.environ["http_proxy"]
if "https_proxy" in os.environ:
    del os.environ["https_proxy"]

requests_ca = "%s/certs/localCA.pem" % SF_BOOTSTRAP_DATA
if "REQUESTS_CA_BUNDLE" not in os.environ and os.path.isfile(requests_ca):
    os.environ["REQUESTS_CA_BUNDLE"] = requests_ca

groupvars = yaml.safe_load(open("%s/all.yaml" % SF_BOOTSTRAP_DATA))

GATEWAY_HOST = groupvars['fqdn']

GATEWAY_URL = 'https://%s' % GATEWAY_HOST
MANAGESF_API = GATEWAY_URL + "/manage/"

GERRIT_USER = 'gerrit'
GERRIT_SERVICE_PRIV_KEY_PATH = '%s/ssh_keys/gerrit_service_rsa' \
                               % SF_BOOTSTRAP_DATA
SERVICE_PRIV_KEY_PATH = '%s/ssh_keys/service_rsa' \
                        % SF_BOOTSTRAP_DATA

ADMIN_PASSWORD = groupvars['authentication']['admin_password']
USER_1 = "admin"
USER_1_PASSWORD = ADMIN_PASSWORD

SF_SERVICE_USER = "SF_SERVICE_USER"
SF_SERVICE_USER_PASSWORD = groupvars.get('sf_service_user_password')

HOOK_USER = SF_SERVICE_USER
HOOK_USER_PASSWORD = SF_SERVICE_USER_PASSWORD

ADMIN_USER = USER_1
ADMIN_PRIV_KEY_PATH = '%s/ssh_keys/gerrit_admin_rsa' % SF_BOOTSTRAP_DATA
ADMIN_PUB_KEY_PATH = '%s/ssh_keys/gerrit_admin_rsa.pub' % SF_BOOTSTRAP_DATA

USER_2 = 'user2'
USER_2_PUB_KEY = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDV6R5m5a' + \
    'AFQGoaw82JyrD7TFP9+MqBVO7CKt/WzL5stcbXlsZqx7Sf4sS70S4ANOyAuyqQD' + \
    'Mrwu0xQwie6rxSTLQXR4Mj/9q29dsiYEOkZ5V0A2eU/ja1dqD56ajJeH24XJsKI' + \
    'Bd4B7o6F5HcK4wnj14w4yw8SmXXC01Z9t14y07fuXDt/5evGeQ43bOonAdXWx6R' + \
    'v6TG+sNP9T2oAoFjugFbAYPhxp2o9NCExessoiemQqf+a7It1r33P7uKgB5ShjB' + \
    'rFiH5TLsgxRb/Ni4oga13B+D3e/Sak5ca6zQp+J1JyBI1y4mDHtfxK3fhKdx6V3' + \
    'DgARhyrNNoiFc0s8Q75'
USER_2_PRIV_KEY = """
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA1ekeZuWgBUBqGsPNicqw+0xT/fjKgVTuwirf1sy+bLXG15bG
ase0n+LEu9EuADTsgLsqkAzK8LtMUMInuq8Uky0F0eDI//atvXbImBDpGeVdANnl
P42tXag+emoyXh9uFybCiAXeAe6OheR3CuMJ49eMOMsPEpl1wtNWfbdeMtO37lw7
f+XrxnkON2zqJwHV1sekb+kxvrDT/U9qAKBY7oBWwGD4cadqPTQhMXrLKInpkKn/
muyLda99z+7ioAeUoYwaxYh+Uy7IMUW/zYuKIGtdwfg93v0mpOXGus0KfidScgSN
cuJgx7X8St34Snceldw4AEYcqzTaIhXNLPEO+QIDAQABAoIBAHN8VhOLaScsrZwh
lfgMXBxwCvCUvw+wAO8HIq3e//fE88M0/Y5snxGq5jfYKROnfv/JDKOUpIPvOrZm
+/gHyf3jUr8KsrmuPgKJ/KZMiuyWLe3ltaToIm7sBD8m0maKZW9OV7wEHuXAG2Yi
ADr6dD50Apou1sZd33v9iTZ6Jvsc4X2sk7+uifJnVGWRmqmftaujf9zIpIBW8Tta
LzwZxMKdoW/7eh2YsOCOqxK6Ttd7kMEahyMLtqAEXUGYwwSGOdWSwkcmHW04etj7
bgAnIBDn6Jubh8ZFBGLz7SNzE+v1K0pGNePKit46j37dstF8bb+ahYc7RRgGv05/
aR5WC3kCgYEA+aAayq9jmV/eh6rvnabiJ+qE9TnUBuOYknVYz5r9kfB7f0jZjdUd
QpF7SCtLCpwCpWeLLc/X+FC4g6mrGnnOKvu0ZjEA37vP8/Nl9Wfvl0h6f4XGrdVz
eNKqBBAsiSm2MZSlEalHOi+cdPesNKKQyoNnpaJnRlDcPkFuWPfZBR8CgYEA21+I
d3vLv6H/D8+L3nxfh2gil5fXtz4qLHllRTEdWhGqzhQJZ8vhulJXGe3oxtwSDWnS
4+2WMM3NC+e8rfZu6HSYQLM0ZQvfynaj9j725RxUTKKWOY/rveJDv18pOnH39Ovk
ASJowl1s6RBU1+f7K/Hdk7Mj39YV7tuOJcdEkOcCgYEA8eqIrG8HLkerqH0vVPC7
cgWkrudJJRgC78ULub6yCXIurS9Tr1Ge1rmY6VsTkYeaROQxDMfFvN+1wdt3d+Qd
uqhOr07EUw93vCrhX9BHcKyMEvP5lNQs4SYAIInwL0meSTSOOKx929TyYqT4XdZC
ThDFLM9UGOAaYbcVkuE3j+8CgYEAlIwaQp5nl7pAlxo5Ykzh+zT+x5wgjIrhz//c
HYBmmckA2k8jF1At6Bc9t+csCwyWhNK15XXKj/2r7XXchAgtjeb1+knfHtVtkxHH
cUWttfL6+nHWO+BDB++hZIMxzcvC1eyuFj6QpZzR1PgkG5eQs28yVYOmtTmo3Hd7
yAUpXt0CgYAN5uVUOun3MYg5IYnj5SdhvkdzPdsgzhEkXPrsNr5u3dKnIXDEuh33
gShLmXU7q0KSUXXb7yxYZiK58jV3u/2N5Pi6j03TxK+kZCiJQkDFeGSQaD4OFNrH
iy5Lb0Yy9I1UjSyJ+ftDkizdrUb1h6B8gP0+6t5ee9qMiY96e2KZDw==
-----END RSA PRIVATE KEY-----
"""

USER_3 = 'user3'
USER_3_PUB_KEY = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDj0xClo8qxB+' + \
    '0Omdab78T/zF+owWtbE6BxZBw0h3mm+wy2h/M1b/P2xb0nW6djFXPzd6OcRl5Ws' + \
    'zZfbH1J11IZ8v5ax0caR/y8YbWSGgHllEPcv8wYl0hnmyutPBjxoQ+Fyp7/uPGB' + \
    '/h2s1RXLtdwBDREnYTeWEc+yGmMuvhX6E6RdlvLoXnTXTgNJB6HWUejeILtRsF1' + \
    '9yCTva8eLImT99BD9gcV77eQsxA7ppOSeveY9Mo6ZAs4f1uC+Ig3pr37FToCxUN' + \
    '2kg+wOJD3U1+jCM5g5LTrFIu3xrtk0hSoyt55ZwKSyGOEZ5e7xE3jkwrdsl/t5L' + \
    'Tust4tdG0dZi0Sv'
USER_3_PRIV_KEY = """
-----BEGIN RSA PRIVATE KEY-----
MIIEpQIBAAKCAQEA49MQpaPKsQftDpnWm+/E/8xfqMFrWxOgcWQcNId5pvsMtofz
NW/z9sW9J1unYxVz83ejnEZeVrM2X2x9SddSGfL+WsdHGkf8vGG1khoB5ZRD3L/M
GJdIZ5srrTwY8aEPhcqe/7jxgf4drNUVy7XcAQ0RJ2E3lhHPshpjLr4V+hOkXZby
6F50104DSQeh1lHo3iC7UbBdfcgk72vHiyJk/fQQ/YHFe+3kLMQO6aTknr3mPTKO
mQLOH9bgviIN6a9+xU6AsVDdpIPsDiQ91NfowjOYOS06xSLt8a7ZNIUqMreeWcCk
shjhGeXu8RN45MK3bJf7eS07rLeLXRtHWYtErwIDAQABAoIBAQDWZiv1ZaX7YfUi
V34Ss9sVy1R+sL+CL38/FrJAcPn4PawiHuCvelMB+ebfoi5tXaQIDKApEkP3naHe
vW9OzVbTWs0pyv3L6tEay20fOGBumFAg71J4Fe6qqem5lqP2yNad1yg4ieilp+pv
Wvyu/88yIgTxpVi1Xr+x4YlTVMnD02+DvIHoMhxt825tYfwWXlpmsFpW7JhgI7RU
t0kQM4bOuCIgmeJ7WkR+AJ+KwSHvlfx4i02PEXMClZBtYTd1gRETbhSFjn1boeg7
EMX/2bwHkktRKsnzHwG2Gri4c10hMClbtKQn1y8pCV3sS0vFtEUzsTSRCsbZ51p2
jQvbJ/fJAoGBAPlmWeRxQyDc01dfxUQDHNF8lLV5IxabTmQaFq7VVNJXS94Xk0Xo
xdk6aY4C0t2Zv/MdZPvWL9F2Dfj1AuLfZuphrzWOiih5q305z+NXoBAf+xCbYwEy
HecH3bF/itv2p5a6HimMrLLvkTvnTmDxFqwbxuHrBrZDbadbGsvZN0y7AoGBAOna
i0NVycy9xCKCIZLEUzGeNjezLJyuv4SNxj1cEIu7CaOmvn1tifGmkWMdL0a13JTN
ueoqtco8MXfKC3G5orhO2u2YWwhKY+3aHZ3iB41h+koDN90HVVECNqv1bk4qeXlk
pMbpp2hv+Hs+oRoOaUiE7aO763jxkhimBsxZe0KdAoGAXn12xWRcKJFByTLRzGjZ
fE0VEoRo1OHWm3p+6ZKN5nuIlQadl7kPbLQC1fkf5zGfVf7nCbsmttdhh9dcVpSJ
q3eDKGlu0tL2NCW5K8tBK5rSRoJ4yjUwux1x0xQdiiUzbZnqX5eavtihT+7c9UGi
c2a6vVGMY3W8j9Gmn2EW4I0CgYEA1LNzwZ4Q+4mLEPwdv1mUdef6VnVA2Y5UIiO1
sO/BGObZYKF0V68/La2cRXMxIfaeGDZ6qFOKn9RaBiOefyUirNMEa+EMw6Ct/ZRL
JeSFjAIW3iTJNd/KqPEDeyqz1qLpdBGnkkjJfMODVc3kSEfdWRmW8DsndQz8HjE8
s7eb1j0CgYEAlwN3HCutHPVzdAO4q8vwev+isw7+SJ8dF/hRMZVrHLWI+gairLs+
XrhFc+BJQEzvEQjBdeFMttHzx2NnWjKiIaMqpxF1mSVxUCErn5S8Q/uNqVWiPPzj
asObPhlIwm8RAI2c5sqeGjSERG3kfR3Zif+bukkVkz2N5yON3VJKEmA=
-----END RSA PRIVATE KEY-----
"""

USER_4 = 'user4'
USER_4_PUB_KEY = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC0uBmIooeTKA' + \
    'UKdeqQtR/LUt7qbSd+0jFZPtyDLCvfVZHz9UdmjGfPS0YAXO3vDAx6kjg/acWc8' + \
    '/c2V/xeFKj5xSyl2LUGy4nPiF9KMXGBqu6pKP6kM47dzol/Qy8hkB3JY6wzvpQg' + \
    'hw0fPMeEUFrJtYI0kqR91vAUAHUK8SIWwOL/AaAvvA1frvI7FFgWqb+HgM8P5Dd' + \
    'rT7whMZgA1Y9TMqonwvT+7kYLqtHx2p8cvV+MUiYfKC9JgCbmyvGcMGyn17BIB+' + \
    'JeW+Pkxa2+pjrRSEMXQoLWlKKRIlbaS6PUwgCs6lZSoQp4ULDL8UGtRNibp2khM' + \
    'GB0zfOiR8e543jP'
USER_4_PRIV_KEY = """
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAtLgZiKKHkygFCnXqkLUfy1Le6m0nftIxWT7cgywr31WR8/VH
Zoxnz0tGAFzt7wwMepI4P2nFnPP3Nlf8XhSo+cUspdi1BsuJz4hfSjFxgaruqSj+
pDOO3c6Jf0MvIZAdyWOsM76UIIcNHzzHhFBaybWCNJKkfdbwFAB1CvEiFsDi/wGg
L7wNX67yOxRYFqm/h4DPD+Q3a0+8ITGYANWPUzKqJ8L0/u5GC6rR8dqfHL1fjFIm
HygvSYAm5srxnDBsp9ewSAfiXlvj5MWtvqY60UhDF0KC1pSikSJW2kuj1MIArOpW
UqEKeFCwy/FBrUTYm6dpITBgdM3zokfHueN4zwIDAQABAoIBAATvmlLvDYDpcOnO
Oq/lIo8tHkWM4a1HFG35l5BFnpUlAy2En4SfhR5WUf0kjKMg0x5t6/dfbjRRPYlQ
ceYn7k2UIxoMhzU+Te9LLD8chpsiDg60ve/CML7CK2M8dIcYJpgfjs6DAAy7Y5Jc
2J42i6RCvuGst61wN3J0aL35xBKW+lEPoJdJ6MqcY9joowmuDFikIVd2+1nAMw/P
65jpXznTCcZrBh9ct6wkBPiFcRFKiP7VVbWJeYjXNdD/Ky3twB/U5u2ykLNzGDQY
SeI8EyQ9f0vYCJ4XrtMkC+fZmsugDHJ9JWg0MIrR8O/qxhU9gjqOBS19y1zffr5d
mFq8DaECgYEA6oOyDEzlbTRSwqZEN5d3V0ogPMBEfPt0YImPOgVEgWZfl3ArS8LY
IqQ0Rv53HunbU6vVpQcJrSMUyQOeZTsIydLJRnVQNKQWvi56Jen6v7EqNeVmJZ3S
eYY8Ivw5Fp9wDd0Ubh02Pct/0D9EbosWDG8uzD2sqnAMVF+rZ1x7M8kCgYEAxUaw
TojzyiRTihF0UV0A6244h3/q1qZEgH0tv/kjxRn645lx08xpzFPFVD2yynZxmB+n
C7IfNpeVCJ6rzt5N9PvPYJWUJ0osmRl6cXH+hRdx7PebFR+LZZBaLrvRh5kGbN8N
stA4EJtMenSwiw0TINSfjToLKzJmJW4KHD3io9cCgYEAzD3YMjhCVAKO1XGi1du3
lzE6tE4rF8KTz4PeVoTB7gSv2h9ZxcizHjBuSypRqn23g76S+gAQIFb+QjdBmx53
//XxT8jaCo6iNA4cWarWtF5iyb+5X6d86FPNShbqzVYcbCaQJXqRg+4YqdCAE9pU
YI3wbvaDy4h8ZHtRt1pm/mkCgYA2VUvFtY5/hBXGFxyUNCtGrGrBVwfU6qI/STrK
ftHNPWSOPvrMvKX+8quMkhmmDY0nusAFRp+2J3WSlDD5ntyVtqzdCxVs5M73s763
dBAHk/d6ro919+QqquFLscr5r7nHTn+1Wge2+y7LI0xkX8t+5VC0UuI0mYLsmCwM
rza2rQKBgQDRVxH7vKgDB97WuZ8KZeJWTWOv3ssHjIL93RoKGzngNc0KrE0BFD+e
e8Hn4MD7cWUwUa2k/bDgp0El8Hfiiwicd2d/Q3tzAEy76n7HwEJ0X0ZjrgYMnak8
GImOmKYg2lO4r6X5SO3RzrNxQnEBKk4q4r7j70meLkxqDj5WdbvirA==
-----END RSA PRIVATE KEY-----
"""

USER_5 = "user5"
USER_5_PUB_KEY = USER_4_PUB_KEY
USER_5_PRIV_KEY = USER_4_PRIV_KEY

USER_6 = "user6"
USER_6_PUB_KEY = USER_4_PUB_KEY
USER_6_PRIV_KEY = USER_4_PRIV_KEY

# USER_5 AND USER_6 are added to this dictionary in
# test_10_userdata.py file. So if new users to be added
# to this dictionary please start with USER_7

USERS = {
    USER_1: {"password": ADMIN_PASSWORD,
             "email": "admin@sftests.com",
             "pubkey": file(ADMIN_PUB_KEY_PATH).read(),
             "privkey": file(ADMIN_PRIV_KEY_PATH).read(),
             "auth_cookie": "",
             },
    USER_2: {"password": ADMIN_PASSWORD,
             "email": "user2@sftests.com",
             "pubkey": USER_2_PUB_KEY,
             "privkey": USER_2_PRIV_KEY,
             "auth_cookie": "",
             },
    USER_3: {"password": ADMIN_PASSWORD,
             "email": "user3@sftests.com",
             "pubkey": USER_3_PUB_KEY,
             "privkey": USER_3_PRIV_KEY,
             "auth_cookie": "",
             },
    USER_4: {"password": ADMIN_PASSWORD,
             "email": "user4@sftests.com",
             "pubkey": USER_4_PUB_KEY,
             "privkey": USER_4_PRIV_KEY,
             "auth_cookie": "",
             },
    USER_5: {"password": ADMIN_PASSWORD,
             "email": "user5@sftests.com",
             "pubkey": USER_5_PUB_KEY,
             "privkey": USER_5_PRIV_KEY,
             "auth_cookie": "",
             "lastname": "Demo user5",
             },
    USER_6: {"password": ADMIN_PASSWORD,
             "email": "user6@sftests.com",
             "pubkey": USER_6_PUB_KEY,
             "privkey": USER_6_PRIV_KEY,
             "auth_cookie": "",
             "lastname": "Demo user6",
             }
}


# List of potential issue tracker plugins supported by managesf
ISSUE_TRACKERS = []
