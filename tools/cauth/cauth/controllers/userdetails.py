import json
import requests
import MySQLdb


class Redmine:
    def __init__(self, conf):
        self.redmine_url = "http://%s/users.json" % conf.redmine['apihost']
        self.api_key = conf.redmine['apikey']

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


class Gerrit:
    def __init__(self, conf):
        self.gerrit_url = "http://%s/api/a/accounts" % conf.gerrit['url']
        self.admin_user = conf.gerrit['admin_user']
        self.admin_password = conf.gerrit['admin_password']

        self.db_host = conf.gerrit['db_host']
        self.db_name = conf.gerrit['db_name']
        self.db_user = conf.gerrit['db_user']
        self.db_password = conf.gerrit['db_password']

    def install_sshkeys(self, username, keys):
        url = "%s/%s/sshkeys" % (self.gerrit_url, username)
        for entry in keys:
            requests.post(url, data=entry.get('key'),
                          auth=(self.admin_user, self.admin_password))

    def add_in_acc_external(self, account_id, username):
        db = MySQLdb.connect(passwd=self.db_password, db=self.db_name,
                             host=self.db_host, user=self.db_user)
        c = db.cursor()
        sql = ("INSERT INTO account_external_ids VALUES"
               "(%d, NULL, NULL, 'gerrit:%s');" %
               (account_id, username))
        try:
            c.execute(sql)  # Will be only successful if entry does not exist
            db.commit()
            return True
        except:
            return False

    def create_gerrit_user(self, username, email, lastname, keys):
        user = {"name": lastname, "email": email}
        data = json.dumps(user)

        headers = {"Content-type": "application/json"}
        url = "%s/%s" % (self.gerrit_url, username)
        requests.put(url, data=data, headers=headers,
                     auth=(self.admin_user, self.admin_password))

        resp = requests.get(url, headers=headers,
                            auth=(self.admin_user, self.admin_password))
        data = resp.content[4:]  # there is some garbage at the beginning
        try:
            account_id = json.loads(data).get('_account_id')
        except:
            account_id = None

        fetch_ssh_keys = False
        if account_id:
            fetch_ssh_keys = self.add_in_acc_external(account_id, username)

        if keys and fetch_ssh_keys:
            self.install_sshkeys(username, keys)


class UserDetailsCreator:
    def __init__(self, conf):
        self.r = Redmine(conf)
        self.g = Gerrit(conf)

    def create_user(self, username, email, lastname, keys):
        self.r.create_redmine_user(username, email, lastname)
        self.g.create_gerrit_user(username, email, lastname, keys)
        # Here we don't care of the error
        return True
