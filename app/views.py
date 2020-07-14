from flask_appbuilder import BaseView, expose, has_access

from . import appbuilder
from flask_appbuilder import ModelView, SimpleFormView, MultipleView
from flask_appbuilder.models.sqla.interface import SQLAInterface
import pandas as pd
import io
import os
from flask_appbuilder.models.sqla.filters import FilterStartsWith
from flask import request, redirect, make_response,url_for
from werkzeug.utils import secure_filename

from forms import SearchForm

from app import app, db

import hashlib
from app.models import Exposure, Chemical, Estimated,  Cell_line, \
    Endpoint, Solvent, Person, Medium, Nanomaterial, Institution, \
    Person_Institution

from flask_appbuilder.widgets import ListWidget, RenderTemplateWidget

from flask_appbuilder.urltools import get_filter_args

from query_lib import get_database_readable

from search import apply_filters, apply_ordering, sort_combinations
from query_lib import get_exposure_eager
from app import cache
from werkzeug.datastructures import MultiDict

from forms import makeUploadSingleForm
from fileIO import read_rawdata
from insert_db import add_record_rawdata, add_record_norawdata
from scipy.stats import t
from math import sqrt
from test import validate_ec_calculation



class ListDownloadWidget(ListWidget):
    template = 'widgets/list_download.html'


class ChemicalView(ModelView):
    datamodel = SQLAInterface(Chemical)

    label_columns = {'name': 'Chemical', "cas_number": "CAS-Nr"}
    list_columns = [
        "name", "cas_number", "user_corrected_experimental_log_kow",
        "experimental_log_kow", "estimated_log_kow"
    ]


class NanomaterialView(ModelView):
    datamodel = SQLAInterface(Nanomaterial)
    list_columns = ["core", "coating", "size", "treatment"]


class CellLineView(ModelView):
    datamodel = SQLAInterface(Cell_line)
    list_columns = ["short_name", "full_name"]


class MediumView(ModelView):
    datamodel = SQLAInterface(Medium)
    list_columns = ["short_name", "full_name"]


class EndpointView(ModelView):
    datamodel = SQLAInterface(Endpoint)
    list_columns = ["short_name", "full_name"]


class SolventView(ModelView):
    datamodel = SQLAInterface(Solvent)
    list_columns = ["short_name", "full_name"]


class PersonView(ModelView):
    datamodel = SQLAInterface(Person)
    list_columns = ["short_name", "full_name", "orcid", "linkedin"]


class InstitutionView(ModelView):
    datamodel = SQLAInterface(Institution)
    list_columns = ["full_name"]


class PersonInstitutionView(ModelView):
    datamodel = SQLAInterface(Person_Institution)


class MultiPersonView(MultipleView):
    views = [PersonView, InstitutionView, PersonInstitutionView]


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




class BrowseCustom(BaseView):

    default_view = 'search'

    @expose('/search/', methods=['GET', 'POST'])
    def search(self):
        form = SearchForm()
        q = get_exposure_eager(db)
        page = None

        clear = request.args.get('clear', False, type=bool)

        #clear cached query and form data
        if clear:
            cache.set("search_query", None)
            cache.set("form_data", None)

        #apply filters defined in search form
        if request.method == 'POST' and form.validate():
            page = request.args.get('page', 1, type=int)

            q = apply_filters(q, form)

            cache.set("search_query",
                      [x.id for x in q.with_entities(Exposure.id).all()])
            form_dict = request.form.to_dict(flat=False)
            cache.set("form_data", form_dict)
           
            return redirect(url_for('BrowseCustom.search'))

        #get cached form data
        if cache.get("form_data") is not None:
            form = SearchForm(MultiDict(cache.get("form_data")))

        #get cached filtered query
        if cache.get("search_query") is not None:
            ids = cache.get("search_query")
            q = q.filter(Exposure.id.in_(ids))


        sort = None
        sort_dir = None

        #sort query
        if request.args.get('sort') and request.args.get('sort_dir'):
            sort = request.args.get('sort')
            sort_dir = request.args.get('sort_dir')
            q = apply_ordering(q, sort, sort_dir)

        #handle pagination
        if page is not None:
            page = 1

        
        entries = q.paginate(page, 25, False)

        #generate navigation links
        if sort is None:

            next_url = url_for('BrowseCustom.search', page=entries.next_num) \
                    if entries.has_next else None
            prev_url = url_for('BrowseCustom.search', page=entries.prev_num) \
                    if entries.has_prev else None
            first_url = url_for('BrowseCustom.search',page = 1) \
                    if entries.page != 1 else None
            last_url = url_for('BrowseCustom.search',page = entries.pages) \
                    if entries.page != entries.pages else None
        else:
            #propagate column ordering to next page
            next_url = url_for('BrowseCustom.search', page=entries.next_num,sort=sort,sort_dir=sort_dir) \
                if entries.has_next else None
            prev_url = url_for('BrowseCustom.search', page=entries.prev_num,sort=sort,sort_dir=sort_dir) \
                    if entries.has_prev else None
            first_url = url_for('BrowseCustom.search',page = 1,sort=sort,sort_dir=sort_dir) \
                    if entries.page != 1 else None
            last_url = url_for('BrowseCustom.search',page = entries.pages,sort=sort,sort_dir=sort_dir) \
                    if entries.page != entries.pages else None

        #generate urls for sort dropdown
        sort_urls = [
            url_for('BrowseCustom.search', sort=x[0], sort_dir=x[1])
            for x in sort_combinations
        ]
        sort_names = [" ".join(x) for x in sort_combinations]
        sort_info = list(zip(sort_urls, sort_names))
        
        clear_filters_url = url_for('BrowseCustom.search',
                                    page=entries.page,
                                    clear=True)
       
        return self.render_template("search.html",
                                    form=form,
                                    table=entries,
                                    prev_url=prev_url,
                                    next_url=next_url,
                                    clear_filters_url=clear_filters_url,
                                    last_url=last_url,
                                    first_url=first_url,
                                    sort_info=sort_info)
    #download csv and excel files
    @expose('/csv', methods=['GET'])
    def download_csv_custom(self):

        query = get_database_readable(db)
        if cache.get("search_query") is not None:
            ids = cache.get("search_query")
            query = query.filter(Exposure.id.in_(ids))
        df = pd.DataFrame(query)
        response = make_response(df.to_csv())
        cd = 'attachment; filename=celltox_database.csv'
        response.headers['Content-Disposition'] = cd
        response.mimetype = 'text/csv'
        return response

    @expose('/xls', methods=['GET'])
    def download_xls_custom(self):
        query = get_database_readable(db)
        if cache.get("search_query") is not None:
            ids = cache.get("search_query")
            query = query.filter(Exposure.id.in_(ids))
        output = io.BytesIO()
        writer = pd.ExcelWriter(output)
        df = pd.DataFrame(query)
        df.to_excel(writer, 'Tab1')
        writer.close()
        response = make_response(output.getvalue())
        response.headers[
            'Content-Disposition'] = 'attachment; filename=celltox_database.xlsx'
        response.headers["Content-type"] = "text/csv"
        return response


class Browse(ModelView):
    """ Admin view of exposure data """
    datamodel = SQLAInterface(Exposure, db.session)
    base_order = ('timepoint', 'asc')
    list_widget = ListDownloadWidget
    show_widget = CustomShowWidget

    add_exclude_columns = ['estimated']
    edit_exclude_columns = ['estimated', 'date_created']
    search_exclude_columns = ['chemical']


    search_columns = ["endpoint","chemical","timepoint", \
                      "experimenter","solvent","estimated", \
                          "replicates","insert","dosing","conc_determination","passive_dosing"]



    search_form_query_rel_fields = {
        "chemical": [["cas_number", FilterStartsWith, '1']]
    }


    label_columns = {
        'chemical.name': 'Chemical',
        "ell_line.full_name": "Cell line",
        "endpoint.full_name": "Endpoint",
        "timepoint": "Timepoint [h]",
        "ec50_format": "EC50 [mg/L]"
    }
    list_columns = ["chemical.name","cell_line.full_name", \
                    "endpoint.full_name","timepoint","ec50_format"]


    @expose('/csv', methods=['GET'])
    def download_csv(self):
        get_filter_args(self._filters)
        order_column, order_direction = self.base_order
        
        query = get_database_readable(db)
        if self._filters:
            query = self._filters.apply_all(query)
        df = pd.DataFrame(query)
        response = make_response(df.to_csv())
        cd = 'attachment; filename=celltox_database.csv'
        response.headers['Content-Disposition'] = cd
        response.mimetype = 'text/csv'
        return response

    @expose('/xls', methods=['GET'])
    def download_xls(self):
        get_filter_args(self._filters)
        order_column, order_direction = self.base_order
        
        query = get_database_readable(db)
        if self._filters:
            query = self._filters.apply_all(query)
        output = io.BytesIO()
        writer = pd.ExcelWriter(output)
        df = pd.DataFrame(query)
        df.to_excel(writer, 'Tab1')
        writer.close()
        response = make_response(output.getvalue())
        response.headers[
            'Content-Disposition'] = 'attachment; filename=output.xlsx'
        response.headers["Content-type"] = "text/csv"
        return response


class EstimatedView(ModelView):
    datamodel = SQLAInterface(Estimated)

    list_columns = ["ec50", "ec50_format"]
 

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in appbuilder.get_app.config['ALLOWED_EXTENSIONS']




class UploadView(SimpleFormView):

    with app.test_request_context():
        form = makeUploadSingleForm()
    form_title = 'Upload dose response file'
    message = "My form was submitted"

    def form_get(self, form):
        form.file.data = "This was prefilled"

    def form_post(self, form):
        dat = form.data
        rvalidation = {}
        if form.file.data is None:
            dat['ec50'] = form.ec50.data
            if form.error_type.data == 'std':
                replicates = form.replicates.data
                nconc = form.nconcentrations.data
                n = replicates * nconc
                s = form.error_value.data
                error = t.ppf(0.975, n - 1) * s / sqrt(n)
            else:
                error = form.error_value.data

            dat['ec50_ci_lower'] = dat['ec50'] - error
            dat['ec50_ci_upper'] = dat['ec50'] + error

            record = add_record_norawdata(dat, db.session)

        else:
            fname = os.path.join(appbuilder.get_app.config['UPLOAD_FOLDER'],
                                 form.file.data.filename)
            form.file.data.save(fname)

            fhash = hashlib.sha1(open(fname, 'rb').read()).hexdigest()

            hash_query = db.session.query(Exposure).filter(
                Exposure.rawfile_hash == fhash)

            if hash_query.count() > 0:
                return self.render_template(
                    'uploaded.html',
                    exposure=None,
                    status=False,
                    message=
                    "The raw file your are trying to upload has already been added to the database."
                )
       
            dat['rawfile_hash'] = fhash
            dat['raw_data'] = read_rawdata(fname)
            dat['filename'] = fname
            
            record = add_record_rawdata(dat, db.session, db.engine)
            odir = os.path.join("tmp",
                                os.path.splitext(os.path.basename(fname))[0])

            rvalidation = validate_ec_calculation(odir)

        if record is not None:
            status = True
        else:
            status = False

        return self.render_template('uploaded.html',
                                    exposure=record,
                                    status=status,
                                    message="Upload successfull.",
                                    rvalidation=rvalidation)


class PlotView(BaseView):

    default_view = 'method1'

    @expose('/method1/')
    @has_access
    def method1(self):
        """Landing page."""

        return self.render_template('plot.html', dash_url=url_for('/dashapp/'))



db.create_all()

appbuilder.add_view(BrowseCustom(), "Search")
appbuilder.add_view(Browse(), "Exposure", category="Admin")
appbuilder.add_view(UploadView, "Upload")
appbuilder.add_view(PlotView, "Plot")
appbuilder.add_view(ChemicalView(), "Chemicals", category="Admin")
appbuilder.add_view(NanomaterialView(), "Nanomaterial", category="Admin")

appbuilder.add_view(CellLineView(), "Cell line", category="Admin")
appbuilder.add_view(MediumView(), "Medium", category="Admin")
appbuilder.add_view(EndpointView(), "Endpoint", category="Admin")
appbuilder.add_view(SolventView(), "Solvent", category="Admin")
appbuilder.add_view(PersonView(), "Person", category="Admin")
appbuilder.add_view(InstitutionView(), "Institution", category="Admin")
