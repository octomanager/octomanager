from mock import ANY, call, MagicMock, Mock, patch
from nose.tools import assert_raises, eq_

from octomanager import ConfigurationError, perform_batch_job


def _pull_request_mock(assignee=None):
    pull_request_mock = Mock(assignee=assignee)
    pull_request_mock.get_commits.return_value.reversed = [
        Mock(), Mock()
    ]
    return pull_request_mock


def _add_single_unassigned_pull_request_and_return_issue(
                                        github_mock, pull_request_mock=None):
    if pull_request_mock is None:
        pull_request_mock = _pull_request_mock()
    github_mock.return_value.get_repo.return_value.get_pulls.return_value = [
        pull_request_mock
    ]
    issue = Mock(assignee=None)
    github_mock.return_value.get_repo.return_value.get_issue.return_value = (
        issue
    )
    return issue


def _add_repository_with_name(github_mock, repo_name):
    github_mock.return_value.get_repo.return_value = Mock(full_name=repo_name)


def _enhance_github_mock(github_mock, repo_name, pull_request_assignees):
    repo_mock = github_mock.return_value.get_repo.return_value
    repo_mock.full_name = repo_name
    issue_mocks = []
    pull_request_mocks = []
    for n, pull_request_assignee in enumerate(pull_request_assignees):
        pr_mock = _pull_request_mock(pull_request_assignee)
        pr_mock.number = n
        pull_request_mocks.append(pr_mock)
        issue_mock = MagicMock(assignee=pull_request_assignee)
        issue_mocks.append(issue_mock)
    repo_mock.get_pulls.return_value = pull_request_mocks
    repo_mock.get_issue.side_effect = lambda n: issue_mocks[n]
    return github_mock, pull_request_mocks, issue_mocks



@patch('octomanager.REPO_USERS', new_callable=dict)
@patch('octomanager.Github')
class TestPullRequestAssignment(object):

    @patch('octomanager.random')
    def test_assigns_users_randomly_to_an_unassigned_pull_request(
                                            self, random, github, repo_users):
        repo_name = 'some_org/random_assignment'
        repo_users[repo_name] = ['user #1', 'user #2']
        github, _, issues = _enhance_github_mock(github, repo_name, [None])
        perform_batch_job(repo_name)
        eq_([call(repo_users[repo_name])], random.choice.call_args_list)
        get_user = github.return_value.get_user
        eq_([call(random.choice.return_value)], get_user.call_args_list)
        eq_([call(assignee=get_user.return_value)],
            issues[0].edit.call_args_list)

    def test_specified_repo_is_acted_against(self, github, repo_users):
        repo_name = 'some_org/some_repo'
        repo_users[repo_name] = ['a user']
        perform_batch_job(repo_name)
        eq_([call(repo_name)], github.return_value.get_repo.call_args_list)


    @patch('octomanager.random')
    def test_specific_repo_users_are_selected_from(
                                            self, random, github, repo_users):
        repo_name = 'some_org/repo_user_test'
        repo_users[repo_name] = ['user #1', 'user #2']
        _enhance_github_mock(github, repo_name, [None])
        perform_batch_job(repo_name)
        eq_([call(repo_users[repo_name])], random.choice.call_args_list)


    def test_empty_list_of_users_raises_configurationerror(self,
                                                           github,
                                                           repo_users):
        repo_name = 'org/empty_list'
        repo_users[repo_name] = []
        with assert_raises(ConfigurationError):
            perform_batch_job(repo_name)

    def test_pull_requests_are_marked_as_pending_if_not_already(self,
                                                                github,
                                                                repo_users):
        repo_name = 'org/mark_pending'
        repo_users[repo_name] = ['user #1', 'user #2']
        _, pull_requests, _ = _enhance_github_mock(github, repo_name, [None])
        perform_batch_job(repo_name)
        most_recent_commit = (
            pull_requests[0].get_commits.return_value.reversed[0]
        )
        eq_([call('pending')], most_recent_commit.create_status.call_args_list)

    def test_assigns_users_to_two_unassigned_pull_requests(self,
                                                           github,
                                                           repo_users):
        repo_name = 'org/two_unassigned'
        github, _, issues = _enhance_github_mock(github,
                                                 repo_name,
                                                 [None, None])
        repo_users[repo_name] = ['single user']
        perform_batch_job(repo_name)
        for issue in issues:
            eq_([call(assignee=ANY)], issue.edit.call_args_list)

    def test_assigns_users_only_to_unassigned_pull_requests(self,
                                                            github,
                                                            repo_users):
        repo_name = 'org/one_assigned_one_not'
        github, _, issues = _enhance_github_mock(github,
                                                 repo_name,
                                                 [Mock(), None])
        repo_users[repo_name] = ['single user']
        perform_batch_job(repo_name)
        issue_call_count = sum([issue.edit.call_count for issue in issues])
        eq_(1, issue_call_count)

    def test_approval_comment_sets_success_status(self, github,
                                                        repo_users):
        repo_name = 'some_org/some_repo'
        repo_users[repo_name] = ['a user']
        github, pull_requests, issues = _enhance_github_mock(github,
                                                             repo_name,
                                                             [Mock(), None])
        login = 'my nice login'
        issues[0].get_comments.return_value = [
            Mock(),
            Mock(body='OCTOSITTER: +1', user=Mock(login=login)),
            Mock(),
        ]
        issues[0].assignee = Mock(login=login)
        perform_batch_job(repo_name)
        most_recent_commit = (
            pull_requests[0].get_commits.return_value.reversed[0]
        )

        eq_(call('success'),
            most_recent_commit.create_status.call_args_list[-1])

    @patch('octomanager.GithubStorage')
    def test_approval_assignment_is_stored(self, storage, github, repo_users):
        repo_name = 'org/store_approvals'
        user_name = 'a user'
        repo_users[repo_name] = [user_name]
        github, pull_requests, _ = _enhance_github_mock(
            github, repo_name, [None]
        )
        github.return_value.get_user.return_value = Mock(login=user_name)
        perform_batch_job(repo_name)
        eq_([call(repo_name, pull_requests[0].number, user_name)],
            storage.store_pull_request_approver.call_args_list)


@patch('octomanager.REPO_USERS', {})
@patch('octomanager.Github')
def test_unconfigured_repository_raises_configurationerror(github):
    _add_single_unassigned_pull_request_and_return_issue(github)
    with assert_raises(ConfigurationError):
        perform_batch_job('org/repo_name')
