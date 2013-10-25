#!/usr/bin/env python3
import random

from github import Github


USERS = ['arachnegl', 'OddBloke']


def _get_authd_github():
    return Github("63c645c4c54933d1364e3f5367a55defe24b626f")


class GithubRepositoryManager(object):

    def __init__(self, repo_name):
        self.github = _get_authd_github()
        self.repo = self.github.get_repo(repo_name)
        self._assign_all_unassigned_pull_requests()

    def _get_assignee(self):
        return self.github.get_user(random.choice(USERS))

    def _assign_all_unassigned_pull_requests(self):
        pull_requests = self.repo.get_pulls()
        for pull_request in pull_requests:
            self._perform_pull_request_assignment(pull_request)

    def _perform_pull_request_assignment(self, pull_request):
        if pull_request.assignee is None:
            issue = self.repo.get_issue(pull_request.number)
            issue.edit(assignee=self._get_assignee())


def octomanage(repo_name):
    GithubRepositoryManager(repo_name)


if __name__ == '__main__':
    octomanage('octomanager/test-repo')
