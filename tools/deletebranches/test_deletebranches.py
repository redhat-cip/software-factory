import json
import unittest
from mock import call, patch, MagicMock

import deletebranches


class TestDeleteBranches(unittest.TestCase):

    def test_main_missing_args(self):
        self.assertRaises(SystemExit, deletebranches.main)

    @patch('requests.delete')
    @patch('requests.get')
    def test_delete(self, mock_get, mock_delete):
        argv = ["--user", "joe",
                "--password", "pass",
                "--org", "SF",
                "--token", "something",
                "--branch", "test",
                "--filter", "name",
                "--host", "host"]
        content = "junk" + json.dumps({'pname': 'bad'})

        mock_get.return_value = MagicMock(content=content)
        deletebranches.main(argv)
        calls = [
            call(u'http://joe:pass@host/api/a/projects/pname/branches/test',
                 headers={'Authorization': 'token something'}),
            call().ok.__nonzero__(),
            call(u'https://api.github.com/repos/SF/pname/git/refs/heads/test',
                 headers={'Authorization': 'token something'}),
            call().ok.__nonzero__()
            ]
        mock_delete.assert_has_calls(calls)

    @patch('requests.delete')
    @patch('requests.patch')
    @patch('requests.put')
    @patch('requests.get')
    def test_delete_master(self, mock_get, mock_put, mock_patch, mock_delete):
        argv = ["--user", "joe",
                "--password", "pass",
                "--org", "SF",
                "--token", "something",
                "--branch", "master",
                "--filter", "name",
                "--host", "host",
                "--default", "other"]
        content = "junk" + json.dumps({'pname': 'bad'})

        mock_get.return_value = MagicMock(content=content)
        deletebranches.main(argv)

        calls = [
            call(
                u'http://joe:pass@host/api/a/projects/pname/branches/master',
                headers={'Authorization': 'token something'}),
            call().ok.__nonzero__(),
            call(
                u'https://api.github.com/repos/SF/pname/git/refs/heads/master',
                headers={'Authorization': 'token something'}),
            call().ok.__nonzero__()
            ]
        mock_delete.assert_has_calls(calls)

        calls = [
            call(u'https://api.github.com/repos/SF/pname',
                 data='{"default_branch": "other", "name": "pname"}',
                 headers={
                     'Content-Type': 'application/json',
                     'Authorization': 'token something'}),
            call().ok.__nonzero__()
        ]
        mock_patch.assert_has_calls(calls)

        calls = [
            call(u'http://joe:pass@host/api/a/projects/pname/HEAD',
                 data='{"ref": "refs/heads/other"}',
                 headers={
                     'Content-Type': 'application/json',
                     'Authorization': 'token something'}),
            call().ok.__nonzero__()
        ]
        mock_put.assert_has_calls(calls)


if __name__ == '__main__':
    unittest.main()
