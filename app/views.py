from flask import render_template
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView, ModelRestApi
from .utils import get_appliance_name, get_energy_data,get_dashboard_data,get_leaderboard_data,get_history_data

from . import appbuilder, db

"""
    Create your Model based REST API::

    class MyModelApi(ModelRestApi):
        datamodel = SQLAInterface(MyModel)

    appbuilder.add_api(MyModelApi)


    Create your Views::


    class MyModelView(ModelView):
        datamodel = SQLAInterface(MyModel)


    Next, register your Views::


    appbuilder.add_view(
        MyModelView,
        "My View",
        icon="fa-folder-open-o",
        category="My Category",
        category_icon='fa-envelope'
    )
"""

"""
    Application wide 404 error handler
"""

from flask_appbuilder import AppBuilder, BaseView, expose, has_access
from flask_login import current_user
from app import appbuilder
from app import app

class Home(BaseView):
    route_base = '/'
    @expose('/dashboard')
    def dashboard(self):
        self.update_redirect()
        hist_lables, hist_data, mean, bills, pie_values, pie_labels = get_dashboard_data(current_user.id)
        return self.render_template('dashboard.html',
            avg_conumption = mean, 
            bills_anno = bills,
            hist_lables = hist_lables,
            hist_data = hist_data,
            pie_values = pie_values, 
            pie_labels = pie_labels)

    @expose('/history/<string:period>')
    def history(self, period):
        hist_lables, hist_data = get_history_data(current_user.id,period)
        self.update_redirect()
        return self.render_template('history.html',
                        hist_lables = hist_lables,
                        hist_data = hist_data)
    
    @expose('/leaderboard')
    def leaderboard(self):
        leaderboard_data = get_leaderboard_data()
        app.logger.info(leaderboard_data)
        return self.render_template('leaderboard.html', leaderboard_data=leaderboard_data, current_user_id=current_user.id)

    @expose('/forecasting')
    def forecasting(self):
        self.update_redirect()
        return self.render_template('forecast.html')
    
    @expose('/tips')
    def tips(self):
        self.update_redirect()
        return self.render_template('tips.html')

    @expose('/appliance/<string:appliance_name>/<string:model_name>')
    def appliance(self, appliance_name, model_name):
        """
        This function allows provides an appliance name that need to be disaggregated and the 
        """
        hist_lables, hist_data, mean, bills = get_energy_data(appliance_name,current_user.id,model_name)

        return self.render_template('appliance.html', 
            appliance_name=appliance_name,
            appliance_title=get_appliance_name(appliance_name),
            model_name = model_name,
            avg_conumption = mean, 
            bills_anno = bills,
            hist_lables = hist_lables,
            hist_data = hist_data)    

appbuilder.add_view_no_menu(Home())




@appbuilder.app.errorhandler(404)
def page_not_found(e):
    return (
        render_template(
            "404.html", base_template=appbuilder.base_template, appbuilder=appbuilder
        ),
        404,
    )


db.create_all()
