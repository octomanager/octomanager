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


@patch('octomanager.random')
@patch('octomanager.REPO_USERS', new_callable=dict)
@patch('octomanager.Github')
def test_assigns_users_randomly_to_an_unassigned_pull_request(
                                                github, repo_users, random):
    repo_name = 'some_org/random_assignment'
    repo_users[repo_name] = ['user #1', 'user #2']
    _add_repository_with_name(github, repo_name)
    issue = _add_single_unassigned_pull_request_and_return_issue(github)
    perform_batch_job(repo_name)
    eq_([call(repo_users[repo_name])], random.choice.call_args_list)
    eq_([call(random.choice.return_value)],
        github.return_value.get_user.call_args_list)
    eq_([call(assignee=github.return_value.get_user.return_value)],
        issue.edit.call_args_list)


@patch('octomanager.REPO_USERS', new_callable=dict)
@patch('octomanager.Github')
def test_specified_repo_is_acted_against(github, repo_users):
    repo_name = 'some_org/some_repo'
    repo_users[repo_name] = ['a user']
    perform_batch_job(repo_name)
    eq_([call(repo_name)], github.return_value.get_repo.call_args_list)


@patch('octomanager.random')
@patch('octomanager.REPO_USERS', new_callable=dict)
@patch('octomanager.Github')
def test_specific_repo_users_are_selected_from(github, repo_users, random):
    repo_name = 'some_org/repo_user_test'
    repo_users[repo_name] = ['user #1', 'user #2']
    _add_repository_with_name(github, repo_name)
    _add_single_unassigned_pull_request_and_return_issue(github)
    perform_batch_job(repo_name)
    eq_([call(repo_users[repo_name])], random.choice.call_args_list)


@patch('octomanager.REPO_USERS', {})
@patch('octomanager.Github')
def test_unconfigured_repository_raises_configurationerror(github):
    _add_single_unassigned_pull_request_and_return_issue(github)
    with assert_raises(ConfigurationError):
        perform_batch_job('org/repo_name')


@patch('octomanager.REPO_USERS', new_callable=dict)
@patch('octomanager.Github')
def test_empty_list_of_users_raises_configurationerror(github, repo_users):
    repo_name = 'org/empty_list'
    repo_users[repo_name] = []
    with assert_raises(ConfigurationError):
        perform_batch_job(repo_name)


@patch('octomanager.REPO_USERS', new_callable=dict)
@patch('octomanager.Github')
def test_pull_requests_are_marked_as_pending_if_not_already(github,
                                                            repo_users):
    repo_name = 'org/mark_pending'
    repo_users[repo_name] = ['user #1', 'user #2']
    most_recent_commit = Mock()
    _add_repository_with_name(github, repo_name)
    pull_request = Mock(assignee=None)
    _add_single_unassigned_pull_request_and_return_issue(github, pull_request)
    pull_request.get_commits.return_value.reversed = [
        most_recent_commit, Mock()
    ]
    perform_batch_job(repo_name)
    eq_([call('pending')], most_recent_commit.create_status.call_args_list)


@patch('octomanager.REPO_USERS', new_callable=dict)
@patch('octomanager.Github')
def test_assigns_users_to_two_unassigned_pull_requests(github, repo_users):
    repo_name = 'org/two_unassigned'
    _add_repository_with_name(github, repo_name)
    repo_users[repo_name] = ['single user']
    github.return_value.get_repo.return_value.get_pulls.return_value = [
        _pull_request_mock(), _pull_request_mock()
    ]
    issues = [Mock(assignee=None), Mock(assignee=None)]
    github.return_value.get_repo.return_value.get_issue.side_effect = issues
    perform_batch_job(repo_name)
    for issue in issues:
        eq_([call(assignee=ANY)], issue.edit.call_args_list)


@patch('octomanager.REPO_USERS', new_callable=dict)
@patch('octomanager.Github')
def test_assigns_users_only_to_unassigned_pull_requests(github, repo_users):
    repo_name = 'org/one_assigned_one_not'
    _add_repository_with_name(github, repo_name)
    repo_users[repo_name] = ['single user']
    github.return_value.get_repo.return_value.get_pulls.return_value = [
        _pull_request_mock(assignee=Mock()),
        _pull_request_mock()
    ]
    perform_batch_job(repo_name)
    eq_(1, github.return_value.get_repo.return_value.get_issue.return_value
                                                            .edit.call_count)
