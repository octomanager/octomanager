from mock import patch
from nose.tools import assert_in, eq_

from octomanager import GithubStorage


@patch('octomanager.Github')
class TestGitHubAssignmentStorage(object):

    def test_storing_an_assignment_adds_a_comment_to_pr(self, github):
        repo = 'some/repo'
        pull_request_id = 17
        approver_login = 'abacus'
        GithubStorage.store_pull_request_approver(
            repo, pull_request_id, approver_login
        )
        repo = github.return_value.get_repo.return_value
        create_comment = repo.get_issue.return_value.create_comment
        eq_(1, create_comment.call_count)
        args, _ = create_comment.call_args
        comment_body = args[0]
        assert_in('@{}'.format(approver_login), comment_body)
