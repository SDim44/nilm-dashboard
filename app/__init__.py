import logging
import os
from sqlalchemy import create_engine

from flask import Flask, request, redirect, url_for, flash
from flask_appbuilder import AppBuilder, SQLA
from flask_login import current_user
from flask_appbuilder._compat import as_unicode
from flask_appbuilder import AppBuilder
from flask_appbuilder.security.sqla.manager import SecurityManager

from app.newindex import MyIndexView


"""
    Overwriting for Registration
"""
from flask_appbuilder.security.registerviews import RegisterUserDBView

class MyRegisterUserDBView(RegisterUserDBView):
    def add(self, registration_form):
        self.add_form_unique_validations(registration_form)

        user = self.appbuilder.sm.add_user(
            username=registration_form.username.data,
            email=registration_form.email.data,
            first_name=registration_form.first_name.data,
            last_name=registration_form.last_name.data,
            role=self.appbuilder.sm.find_role(
                self.appbuilder.sm.auth_role_registration
            ),
            password=registration_form.password.data,
        )

        if user:
            # These two lines auto-confirm the user
            user.active = True
            self.appbuilder.get_session.commit()

            self.update_redirect()
            return redirect(self.appbuilder.get_url_for_login)

        else:
            flash(as_unicode(self.error_message), "danger")
            return redirect(self.appbuilder.get_url_for_index)


# In your app initialization file
class MySecurityManager(SecurityManager):
    registeruserdbview = MyRegisterUserDBView


"""
 Logging configuration
"""

logging.basicConfig(format="%(asctime)s:%(levelname)s:%(name)s:%(message)s")
logging.getLogger().setLevel(logging.DEBUG)

app = Flask(__name__)
app.config.from_object("config")
db = SQLA(app)
appbuilder = AppBuilder(app, db.session,  security_manager_class=MySecurityManager, base_template='base.html', indexview=MyIndexView)



basedir = os.path.abspath(os.path.dirname(__file__))
app.config['DATADB'] = create_engine('sqlite:///data.db')

"""
from sqlalchemy.engine import Engine
from sqlalchemy import event

#Only include this for SQLLite constraints
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    # Will force sqllite contraint foreign keys
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
"""

from . import views
from .utils import *

@app.route('/appliance/<appliance_name>', methods=['GET', 'POST'])
def upload_file(appliance_name):
    app.config['UPLOAD_FOLDER'] = os.path.join(basedir,"static","uploads",str(current_user.id))

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'],exist_ok=True)

    if request.method == 'POST':
        file = request.files['file']
        
        if file and allowed_file(file.filename):
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = secure_filename(timestamp + "_upload" + ".csv") 
            filename2 = secure_filename(timestamp + "_prediction" + ".csv") 
            
            file_path = os.path.join(app.config['UPLOAD_FOLDER'],filename)
            prediction_path = os.path.join(app.config['UPLOAD_FOLDER'],filename2)
            file.save(file_path)
            predict_seq2seq(file_path, prediction_path,app.config['DATADB'],current_user.id)
            return redirect(url_for('upload_file', appliance_name=appliance_name, filename=filename))

