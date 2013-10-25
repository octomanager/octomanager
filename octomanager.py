#!/usr/bin/env python3
# octositter - a GitHub pull request manager
# Copyright (C) 2013  Daniel Watkins
# Copyright (C) 2013  Gregory Loyse

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import random

from github import Github


LOGGER = logging.getLogger('octomanager')

APPROVAL_PHRASE = 'OCTOSITTER: +1'

REPO_USERS = {
    'octomanager/test-repo': ['arachnegl', 'OddBloke'],
}


def _get_authd_github():
    LOGGER.info("Retrieving auth'd Github instance...")
    github = Github("63c645c4c54933d1364e3f5367a55defe24b626f")
    rate = github.get_rate_limit().rate
    LOGGER.info('{} of {} API calls remaining until {}.'.format(rate.remaining, rate.limit, rate.reset))
    return github


class ConfigurationError(Exception):
    pass


ERROR = object()
FAILURE = object()
PENDING = object()
SUCCESS = object()

COMMIT_STATUSES = {
    ERROR: 'error',
    FAILURE: 'failure',
    PENDING: 'pending',
    SUCCESS: 'success',
}


class GithubStorage(object):

    @staticmethod
    def store_pull_request_approver(repo, pull_request_id, approver_login):
        github = _get_authd_github()
        repo = github.get_repo(repo)
        issue = repo.get_issue(pull_request_id)
        issue.create_comment(
            '@{} has been assigned as a reviewer.'.format(approver_login)
        )


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
            GithubStorage.store_pull_request_approver(
                self.repo.full_name, pr_number, assignee.login
            )

    def set_pull_request_status(self, pull_request, status):
        commit = pull_request.get_commits().reversed[0]
        status_string = COMMIT_STATUSES[status]
        commit.create_status(status_string)

    def check_for_pull_request_approval(self, pull_request):
        issue = self.repo.get_issue(pull_request.number)
        for comment in issue.get_comments():
            if (comment.user.login == issue.assignee.login
                    and APPROVAL_PHRASE in comment.body):
                self.set_pull_request_status(pull_request, SUCCESS)


def perform_batch_job(repo_name):
    repo_manager = GithubRepositoryManager(repo_name)
    pull_requests = repo_manager.get_pulls()
    for pull_request in pull_requests:
        repo_manager.set_pull_request_status(pull_request, PENDING)
        repo_manager.perform_pull_request_assignment(pull_request)
        repo_manager.check_for_pull_request_approval(pull_request)


if __name__ == '__main__':
    logging.basicConfig(level='INFO',
                        format='%(asctime)s [%(levelname)s] %(message)s')
    perform_batch_job('octomanager/test-repo')
