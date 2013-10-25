from mock import call, Mock, patch
from nose.tools import eq_

from octomanager import octomanage


@patch('octomanager.random')
@patch('octomanager.REPO_USERS', new_callable=dict)
@patch('octomanager.Github')
def test_assigns_users_randomly_to_an_unassigned_pull_request(
                                                github, repo_users, random):
    repo_name = 'some_org/random_assignment'
    repo_users[repo_name] = ['user #1', 'user #2']
    github.return_value.get_repo.return_value.get_pulls.return_value = [
        Mock(assignee=None)
    ]
    issue = Mock(assignee=None)
    github.return_value.get_repo.return_value.get_issue.return_value = issue
    octomanage(repo_name)
    eq_([call(repo_users[repo_name])], random.choice.call_args_list)
    eq_([call(random.choice.return_value)],
        github.return_value.get_user.call_args_list)
    eq_([call(assignee=github.return_value.get_user.return_value)],
        issue.edit.call_args_list)


@patch('octomanager.Github')
def test_specified_repo_is_acted_against(github):
    repo_name = 'some_org/some_repo'
    octomanage(repo_name)
    eq_([call(repo_name)], github.return_value.get_repo.call_args_list)


@patch('octomanager.random')
@patch('octomanager.REPO_USERS', new_callable=dict)
@patch('octomanager.Github')
def test_specific_repo_users_are_selected_from(github, repo_users, random):
    repo_name = 'some_org/repo_user_test'
    repo_users[repo_name] = ['user #1', 'user #2']
    github.return_value.get_repo.return_value.get_pulls.return_value = [
        Mock(assignee=None)
    ]
    issue = Mock(assignee=None)
    github.return_value.get_repo.return_value.get_issue.return_value = issue
    octomanage(repo_name)
    eq_([call(repo_users[repo_name])], random.choice.call_args_list)
