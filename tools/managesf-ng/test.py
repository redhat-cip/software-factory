import requests as http
from requests.auth import HTTPBasicAuth
import json

name = 'a3'
url = "http://tests-gerrit/r/a/groups/%s" % name
group_info = {
    "description": "desc",
    "name": "%s" % name,
    "visible_to_all": True
}
resp = http.put(url, data=json.dumps(group_info),
                headers={'Content-type': 'application/json'},
                auth=HTTPBasicAuth('fabien.boucher',
                                   'userpass'))
print resp
