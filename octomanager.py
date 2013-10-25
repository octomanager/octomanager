#!/usr/bin/env python3
from github import Github

def octomanage():
    # poll github for open pull requests
    # set assignee for any unassigned pull requests
    github = Github("63c645c4c54933d1364e3f5367a55defe24b626f")
    repo = github.get_repo('octomanager/test-repo')
    pull_requests = repo.get_pulls()
    for pull_request in pull_requests:
        issue = repo.get_issue(pull_request.number)
        issue.edit(assignee=None)


if __name__ == '__main__':
    octomanage()
