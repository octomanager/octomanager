#!/usr/bin/env python3
import random

from github import Github


USERS = ['arachnegl', 'OddBloke']


def _get_authd_github():
    return Github("63c645c4c54933d1364e3f5367a55defe24b626f")


class OctoManage(object):

    def __init__(self):
        self.github = _get_authd_github()
        self._perform_pull_request_assignment('octomanager/test-repo')

    def _get_assignee(self):
        return self.github.get_user(random.choice(USERS))

    def _perform_pull_request_assignment(self, repo_name):
        repo = self.github.get_repo(repo_name)
        pull_requests = repo.get_pulls()
        for pull_request in pull_requests:
            if pull_request.assignee is None:
                issue = repo.get_issue(pull_request.number)
                issue.edit(assignee=self._get_assignee())


def octomanage():
    OctoManage()


if __name__ == '__main__':
    octomanage()
