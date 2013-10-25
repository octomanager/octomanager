from mock import call, Mock, patch
from nose.tools import eq_

from octomanager import octomanage


@patch('octomanager.random')
@patch('octomanager.USERS', new_callable=list)
@patch('octomanager.Github')
def test_assigns_users_randomly_to_an_unassigned_pull_request(
                                                        github, users, random):
    users += ['user #1', 'user #2']
    github.return_value.get_repo.return_value.get_pulls.return_value = [
        Mock(assignee=None)
    ]
    issue = Mock(assignee=None)
    github.return_value.get_repo.return_value.get_issue.return_value = issue
    octomanage()
    eq_([call(users)], random.choice.call_args_list)
    eq_([call(random.choice.return_value)],
        github.return_value.get_user.call_args_list)
    eq_([call(assignee=github.return_value.get_user.return_value)],
        issue.edit.call_args_list)
