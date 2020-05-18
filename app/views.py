from flask_appbuilder import BaseView, expose, has_access

from . import appbuilder
from flask_appbuilder import ModelView, SimpleFormView, MultipleView, BaseView
from flask_appbuilder.models.sqla.interface import SQLAInterface
import pandas as pd
import io
import os
import base64
from flask_appbuilder.models.sqla.filters import FilterEqualFunction, FilterStartsWith
from flask import request, render_template, redirect, make_response, flash, url_for
from werkzeug.utils import secure_filename


from forms import SearchForm,UploadForm

from app import app,db
from warnings import warn
import hashlib
from app.models import Exposure, Chemical, Estimated, Sample, Cell_line, Endpoint, Solvent, Experimenter, Medium
from insert_db import add_record
from fileIO import read_dr
from flask_appbuilder.widgets import ListWidget,RenderTemplateWidget

from flask_appbuilder.urltools import get_filter_args

from query_lib import get_database_readable


class ListDownloadWidget(ListWidget):
    template = 'widgets/list_download.html'
    
class ChemicalView(ModelView):
    datamodel = SQLAInterface(Chemical)

    label_columns = {'name':'Chemical',
                     "cas_number" : "CAS-Nr"
                     }
    list_columns = ["name","cas_number","user_corrected_experimental_log_kow","experimental_log_kow","estimated_log_kow"]
    
class SampleView(ModelView):
    datamodel = SQLAInterface(Sample)

    list_columns = ["cell_line.full_name","medium.full_name","fbs"]
    
class CellLineView(ModelView):
    datamodel = SQLAInterface(Cell_line)
    list_columns = ["full_name"]



class CustomShowWidget(RenderTemplateWidget):
    """
        ShowWidget implements a template as an widget
        it takes the following arguments
        pk = None
        label_columns = []
        include_columns = []
        value_columns = []
        actions = None
        fieldsets = []
        modelview_name = ''
    """

    template = "show.html"



from search import apply_filters
from query_lib import get_exposure_eager
from app import cache
class BrowseCustom(BaseView):
    
    default_view = 'search'
    
    @expose('/search/',methods=['GET', 'POST'])
    def search(self):
        form = SearchForm()
        q = get_exposure_eager(db)
        page = None

        clear = request.args.get('clear', False, type=bool)
        
        if clear:
            cache.set("search_query",None)
           

        if cache.get("search_query") is not None:
            ids = cache.get("search_query")
            q = q.filter(Exposure.id.in_(ids))
            
        if request.method == 'POST' and form.validate():
            page = request.args.get('page', 1, type=int)
           
            # flash('Validated')
            # flash(q.count())
            # for field in form:
            #     flash(field.name)
            #     flash(type(field.data))
            #     flash(field.data)
            q = apply_filters(q,form)
            cache.set("search_query",[x.id for x in q.with_entities(Exposure.id).all()])
            return redirect(url_for('BrowseCustom.search'))
        
        
        if page is not None:
            page = 1

        entries = q.paginate(
            page, 25, False)
        next_url = url_for('BrowseCustom.search', page=entries.next_num) \
                if entries.has_next else None
        prev_url = url_for('BrowseCustom.search', page=entries.prev_num) \
                if entries.has_prev else None
        clear_filters_url= url_for('BrowseCustom.search', page=entries.page, clear=True)
            # flash(q.count())
        return self.render_template("search.html",form = form,table =entries,
                                    prev_url = prev_url,next_url = next_url,clear_filters_url = clear_filters_url)
        # return "hello"



class Browse(ModelView):
    datamodel = SQLAInterface(Exposure,db.session)
    base_order = ('timepoint','asc')
    list_widget = ListDownloadWidget
    show_widget = CustomShowWidget
    
    
    add_exclude_columns = ['estimated']
    edit_exclude_columns = ['estimated']
    search_exclude_columns = ['chemical']
    

    
    #querydb =  get_database_readable(db)
    
    
    #cache.set("foo",querydb.count())

    search_columns = ["sample","endpoint","chemical","timepoint", \
                      "experimenter","solvent","estimated", \
                          "replicates","insert","dosing","conc_determination","passive_dosing"]
        
    #add_form_query_rel_fields = {"chemical": [["cas_number", FilterStartsWith, 'F'],
                                  #                 ["name", FilterStartsWith, 'F']]
                                  # }
        
    search_form_query_rel_fields = {"chemical": [["cas_number", FilterStartsWith, '1']]
                                    }

                                    
    #add_form_query_rel_fields = {'chemical': [['cas_number', FilterStartsWith, 'W']]}
        
    #search_form_extra_fields = {"chemical": [["experimental_log_kow", FilterGreater, 2]]}
    #search_form_query_rel_fields = {"chemical": [["experimental_log_kow", FilterGreater, 20],]}
    #add_form_query_rel_fields = {"chemical": [["experimental_log_kow", FilterGreater, 2]]}
    #search_form_query_rel_fields = {'experimenter': [["full_name", FilterStartsWith, 'F']]}
    
    
    label_columns = {'chemical.name':'Chemical',
                     "sample.cell_line.full_name":"Cell line",
                     "endpoint.full_name":"Endpoint",
                     "timepoint": "Timepoint [h]",
                     "ec50_format":"EC50 [mg/L]"
                     }
    list_columns = ["chemical.name","sample.cell_line.full_name", \
                    "endpoint.full_name","timepoint","ec50_format"]
        
    #related_views = [ChemicalView]
    #list_columns = ["exposure.chemical.name","exposure.sample.cell_line.full_name","exposure.endpoint.full_name","exposure.timepoint","ec50"]
    #related_views = [ChemicalView]
    
    @expose('/csv', methods=['GET'])
    def download_csv(self):
        get_filter_args(self._filters)
        order_column, order_direction = self.base_order
        #query = self.datamodel.query(self._filters, order_column, order_direction)
        query = get_database_readable(db)
        if self._filters:
            query = self._filters.apply_all(query)
        df = pd.DataFrame(query)
        response = make_response(df.to_csv())
        cd = 'attachment; filename=celltox_database.csv'
        response.headers['Content-Disposition'] = cd
        response.mimetype='text/csv'
        return response
    
    @expose('/xls', methods=['GET'])
    def download_xls(self):
        get_filter_args(self._filters)
        order_column, order_direction = self.base_order
        #query = self.datamodel.query(self._filters, order_column, order_direction)
        
        query = get_database_readable(db)
        if self._filters:
            query = self._filters.apply_all(query)
        output = io.BytesIO()
        writer = pd.ExcelWriter(output)
        df = pd.DataFrame(query)
        df.to_excel(writer, 'Tab1')
        writer.close() 
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = 'attachment; filename=output.xlsx'
        response.headers["Content-type"] = "text/csv"
        return response

class MultiView(MultipleView):
    views = [Browse,ChemicalView]

class EstimatedView(ModelView):
    datamodel = SQLAInterface(Estimated)
    


    list_columns = ["ec50","ec50_format"]
    #list_columns = ["exposure.chemical.name","exposure.sample.cell_line.full_name","exposure.endpoint.full_name","exposure.timepoint","ec50"]
    #related_views = [ChemicalView]
   



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in appbuilder.get_app.config['ALLOWED_EXTENSIONS']


class UploadView(SimpleFormView):
   
    form = UploadForm
    form_title = 'Upload dose response file'
    message = "My form was submitted"
    
    def form_get(self, form):
        form.file.data = "This was prefilled"
    
    def form_post(self,form):
        fname = os.path.join(appbuilder.get_app.config['UPLOAD_FOLDER'], form.file.data.filename)
        form.file.data.save(fname)
        fhash = hashlib.sha1(open(fname, 'rb').read()).hexdigest()
        dat = read_dr(fname)
        status = add_record(dat,db.session,db.engine)
        return self.render_template('uploaded.html',  fname = fname , filehash = fhash , status = status)
    

class PlotView(BaseView):

    default_view = 'method1'

    @expose('/method1/')
    @has_access
    def method1(self):
        # do something with param1
        # and return to previous page or index
        """Landing page."""
        #return redirect(url_for('/dashapp/'))
        
        return self.render_template('plot.html',
                           dash_url = url_for('/dashapp/') )




#appbuilder.add_view(ShowView(), "Show",category = "shows")

# appbuilder.add_view(
#     MyView(), "Method2", href='/myview/method2/jonh', category='My View'
# )
# Use add link instead there is no need to create MyView twice.

db.create_all()


appbuilder.add_view(BrowseCustom(),"Search")
appbuilder.add_view(Browse(), "Browse",category = "Tables")
appbuilder.add_view(UploadView, "Upload")
appbuilder.add_view(PlotView, "Plot")
appbuilder.add_view(ChemicalView(), "Chemical",category = "Tables")
appbuilder.add_view(SampleView(), "Sample",category = "Tables")
appbuilder.add_view(EstimatedView(), "Estimated",category = "Tables")
