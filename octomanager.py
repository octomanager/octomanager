#!/usr/bin/env python3
from github import Github


def _get_authd_github():
    return Github("63c645c4c54933d1364e3f5367a55defe24b626f")


def octomanage():
    # poll github for open pull requests
    # set assignee for any unassigned pull requests
    github = _get_authd_github()
    repo = github.get_repo('octomanager/test-repo')
    pull_requests = repo.get_pulls()
    for pull_request in pull_requests:
        if pull_request.assignee is None:
            issue = repo.get_issue(pull_request.number)
            issue.edit(assignee=github.get_user('arachnegl'))


if __name__ == '__main__':
    octomanage()
