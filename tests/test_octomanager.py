from mock import call, Mock, patch
from nose.tools import eq_

from octomanager import octomanage


@patch('octomanager.Github')
def test_octomanage_assigns_greg_to_an_unassigned_pull_request(github):
    github.return_value.get_repo.return_value.get_pulls.return_value = [
        Mock(assignee=None)
    ]
    issue = Mock(assignee=None)
    github.return_value.get_repo.return_value.get_issue.return_value = issue
    octomanage()
    eq_([call('arachnegl')], github.return_value.get_user.call_args_list)
    eq_([call(assignee=github.return_value.get_user.return_value)],
        issue.edit.call_args_list)
