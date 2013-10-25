#!/usr/bin/env python3
import logging
import random

from github import Github


LOGGER = logging.getLogger('octomanager')

REPO_USERS = {
    'octomanager/test-repo': ['arachnegl', 'OddBloke'],
}


def _get_authd_github():
    LOGGER.info("Retrieving auth'd Github instance...")
    return Github("63c645c4c54933d1364e3f5367a55defe24b626f")


class ConfigurationError(Exception):
    pass


class GithubRepositoryManager(object):

    def __init__(self, repo_name):
        try:
            self.potential_assignees = REPO_USERS[repo_name]
        except KeyError:
            raise ConfigurationError(
                'No potential users configured for {}'.format(repo_name)
            )
        if len(self.potential_assignees) == 0:
            raise ConfigurationError(
                'No potential users configured for {}'.format(repo_name)
            )
        self.github = _get_authd_github()
        self.repo = self.github.get_repo(repo_name)

    def _log(self, msg):
        LOGGER.info('[{}] {}'.format(self.repo.full_name, msg))

    def _get_assignee(self):
        return self.github.get_user(
            random.choice(REPO_USERS[self.repo.full_name])
        )

    def get_pulls(self):
        return self.repo.get_pulls()

    def perform_pull_request_assignment(self, pull_request):
        pr_number = pull_request.number
        self._log('Performing assignment for PR #{}.'.format(pr_number))
        if pull_request.assignee is None:
            issue = self.repo.get_issue(pr_number)
            assignee = self._get_assignee()
            self._log(
                'Assigning {} to PR #{}.'.format(assignee.login, pr_number)
            )
            issue.edit(assignee=assignee)


class PullRequestAssignmentDriver(object):

    def __init__(self, repo_name):
        self.repo_name = repo_name

    def perform_assignments(self):
        LOGGER.info('Performing pull request assignments...')
        repo_manager = GithubRepositoryManager(self.repo_name)
        pull_requests = repo_manager.get_pulls()
        for pull_request in pull_requests:
            repo_manager.perform_pull_request_assignment(pull_request)


def octomanage(repo_name):
    PullRequestAssignmentDriver(repo_name).perform_assignments()


if __name__ == '__main__':
    logging.basicConfig(level='INFO',
                        format='%(asctime)s [%(levelname)s] %(message)s')
    octomanage('octomanager/test-repo')
