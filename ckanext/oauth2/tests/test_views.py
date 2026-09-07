import pytest
from unittest.mock import patch, MagicMock
from ckanext.oauth2.views import login, callback, oauth2helper
import json
from flask import Flask

# Create a Flask app instance
from ckanext.oauth2.oauth2 import get_came_from
app = Flask(__name__)

# Mock the request object to provide necessary attributes
class MockRequest:
    def __init__(self, url):
        self.url = url
        self.args = {}
        self.params = {}  # Add this line to include a params attribute
        self.headers = {}  
        self.url_root = "http://example.com"

    def get(self, key, default=None):
        return self.args.get(key, default)

    def __getitem__(self, key):
        return self.args.get(key)

    def __setitem__(self, key, value):
        self.args[key] = value

    def __delitem__(self, key):
        del self.args[key]
    def GET(self, key, default=None):
        return self.args.get(key, default)

class MockOAuth2Helper:
    def get_came_from(self, state):
        return "http://example.com/some_path"  # Adjust as needed

class TestOAuthViews:
    def test_login(self):
        default_page = '/'  # Adjust based on your actual default_page value
        request = MockRequest('/some_referer')
        request.args = {'came_from': '/some_came_from_url'}  # Adjust based on your actual params

        with patch('ckanext.oauth2.views.toolkit.request', request):
            response = login()
            # Add your assertions for the response


class TestCallbackAccountGate:
    u''' The callback must only hand out a session to an active account.
        A pending account is one awaiting an administrator's approval; a
        deleted one has been deactivated or rejected.
    '''

    def _helper_for(self, state):
        user_obj = MagicMock()
        user_obj.state = state

        helper = MagicMock()
        helper.identify.return_value = ('test_user', user_obj)
        helper.can_log_in.side_effect = lambda user: user.state == 'active'
        helper.support_email = 'support@example.org'
        return helper

    def test_active_user_is_logged_in(self):
        helper = self._helper_for('active')

        with app.test_request_context('/oauth2/callback'), \
                patch('ckanext.oauth2.views.oauth2helper', helper):
            response = callback()

        helper.log_user_into_ckan.assert_called_once()
        helper.update_token.assert_called_once()
        assert response == helper.redirect_from_callback.return_value

    @pytest.mark.parametrize('state,pending', [('pending', True), ('deleted', False)])
    def test_inactive_user_gets_no_session(self, state, pending):
        helper = self._helper_for(state)

        with app.test_request_context('/oauth2/callback'), \
                patch('ckanext.oauth2.views.oauth2helper', helper), \
                patch('ckanext.oauth2.views.toolkit.render',
                      return_value='rendered') as render:
            response = callback()

        assert response.status_code == 403
        assert not helper.log_user_into_ckan.called
        # No token is stored either -- nothing about this sign-in is kept.
        assert not helper.update_token.called
        render.assert_called_once_with(
            'oauth2/account_not_active.html',
            {'pending': pending, 'support_email': 'support@example.org'})
