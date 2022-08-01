# 22/06/14 TK; Don't think we need the following to activate conda v-env.
#          Have added a directive to Apache config instead...
#activate_this = '/home/student/miniconda3/envs/comp47360py39_jt/bin/?????activate?????'
#with open(activate_this) as f:
#	exec(f.read(:), dict(__file__=activate_this))

import sys
import logging

logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/html/comp47360-group3-raduno/jtApi/")

from jt_flask_module import jt_flask_app as application

# If a factory function is used in a __init__.py file, then the function should be imported:
# from yourapplication import create_app
# application = create_app()