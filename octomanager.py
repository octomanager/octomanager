#!/usr/bin/env python3
import random

from github import Github


REPO_USERS = {
    'octomanager/test-repo': ['arachnegl', 'OddBloke'],
}


def _get_authd_github():
    return Github("63c645c4c54933d1364e3f5367a55defe24b626f")


class GithubRepositoryManager(object):

    def __init__(self, repo_name):
        self.github = _get_authd_github()
        self.repo = self.github.get_repo(repo_name)
        self.repo_name = repo_name

    def _get_assignee(self):
        return self.github.get_user(random.choice(REPO_USERS[self.repo_name]))

    def get_pulls(self):
        return self.repo.get_pulls()

    def perform_pull_request_assignment(self, pull_request):
        if pull_request.assignee is None:
            issue = self.repo.get_issue(pull_request.number)
            issue.edit(assignee=self._get_assignee())


class PullRequestAssignmentDriver(object):

    def __init__(self, repo_name):
        self.repo_name = repo_name

    def perform_assignments(self):
        repo_manager = GithubRepositoryManager(self.repo_name)
        pull_requests = repo_manager.get_pulls()
        for pull_request in pull_requests:
            repo_manager.perform_pull_request_assignment(pull_request)


def octomanage(repo_name):
    PullRequestAssignmentDriver(repo_name).perform_assignments()


if __name__ == '__main__':
    octomanage('octomanager/test-repo')
