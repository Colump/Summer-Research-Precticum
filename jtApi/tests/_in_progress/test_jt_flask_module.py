# project/test_basic.py

# 22/08/01 TK; This module was started before I started using selenium
# I may still use this to test some functions not covered by selenium... not
# sure. So - don't want to delete for now - leaving in situ. ...

import os
import sys
import unittest

from jt_flask_module import jt_flask_app, db

test_jt_gtfs_module_dir = os.path.dirname(__file__)
test_jt_gtfs_parent_dir = os.path.dirname(test_jt_gtfs_module_dir)
sys.path.insert(0, test_jt_gtfs_parent_dir)
from jt_utils import load_credentials

class BasicTests(unittest.TestCase):
    """
    """
     # executed prior to each test
    def setUp(self):
        """
        """
        jt_flask_app.config['TESTING'] = True
        jt_flask_app.config['WTF_CSRF_ENABLED'] = False
        jt_flask_app.config['DEBUG'] = False
        jt_flask_app.config['SQLALCHEMY_DATABASE_URI'] = \
            'sqlite:///' + os.path.join(jt_flask_app.config['BASEDIR'], 'jt_test.db')
        self.app = jt_flask_app.test_client()
        # db.drop_all()
        # db.create_all()

        self.assertEqual(jt_flask_app.debug, False)

    # executed after each test
    def tearDown(self):
        """
        """
        pass

# Convenience methods:
def register(self, email, password, confirm):
    return self.jt_flask_app.post('/register.do',
            data=dict(email=email, password=password, confirm=confirm),
            follow_redirects=True
        )

def login(self, email, password):
    return self.jt_flask_app.post('/login.do',
            data=dict(email=email, password=password),
            follow_redirects=True
        )

################################################################################
#  TESTS
################################################################################

def test_main_page(self):
    response = self.jt_flask_app.get('/', follow_redirects=True)
    self.assertEqual(response.status_code, 200)

def test_valid_user_registration(self):
    response = self.register('flintdk99', 'FlaskIsAwesome', 'FlaskIsAwesome')
    self.assertEqual(response.status_code, 200)
    self.assertIn(b'Thanks for registering!', response.data)

def test_invalid_user_registration_different_passwords(self):
    response = self.register('patkennedy79@gmail.com', 'FlaskIsAwesome', 'FlaskIsNotAwesome')
    self.assertIn(b'Field must be equal to password.', response.data)

def test_if_username_is_avaialable(self):
    response = self.register('patkennedy79@gmail.com', 'FlaskIsAwesome', 'FlaskIsNotAwesome')
    self.assertIn(b'Field must be equal to password.', response.data)



if __name__ == "__main__":
    unittest.main()