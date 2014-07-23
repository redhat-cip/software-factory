import json
import requests


class Redmine:
    def __init__(self, redmine_host, api_key):
        self.redmine_url = "http://%s/users.json" % redmine_host
        self.api_key = api_key

    def create_redmine_user(self, username, email, lastname):
        user = {"login":  username,
                "firstname": username,
                "lastname": lastname,
                "mail": email,
                }
        data = json.dumps({"user": user})
        headers = {"X-Redmine-API-Key": self.api_key,
                   "Content-type": "application/json"}
        resp = requests.post(self.redmine_url, data=data, headers=headers)

        return resp.status_code


class UserDetailsCreator:
    def __init__(self, redmine_host, api_key):
        self.r = Redmine(redmine_host, api_key)

    def create_user(self, username, email, lastname):
        # Here we don't care of the error
        return self.r.create_redmine_user(username, email, lastname)
