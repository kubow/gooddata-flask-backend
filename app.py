from common import LoadGoodDataSdk, read_env_file
from flask import Flask, jsonify, make_response, request, Response, url_for
from flask_cors import CORS
from flask_weasyprint import HTML, render_pdf
from healthcheck import HealthCheck  # basic client info
from jinja2 import Environment, FileSystemLoader

# from schedule import every, run_pending
# from time import sleep
# from threading import Thread

# from boto3 import client
# from boto3.s3.transfer import S3Transfer
# import pptx
# import pptx.util
# import glob
# import imageio
# import fitz  # PyMuPDF, imported as fitz for backward compatibility reasons
from pandas import DataFrame

# custom example functions
# from helper import alert_needed, compare_values, send_email, sync_db

# AI stuff
from ai.deepAR.clean_up import CleanUp as DeepARCleanUp
from ai.deepAR.dataset_import import DatasetImport as DeepArDatasetImport
from ai.deepAR.deep_ar_input import DeepARInput
from ai.deepAR.predictor import Predictor as DeepARPredictor
from ai.RCF.dataset_import import DatasetImport as RCFDatasetImport
from ai.RCF.predictor import Predictor as RCFPredictor
from ai.RCF.clean_up import CleanUp as RCFCleanUp
from ai.sagemaker import boto_session, sagemaker_session

app = Flask(__name__)
# allow external environment communication via CORS
ALLOWED = ["https://127.0.0.1:8080", "https://127.0.0.1:3001", "https://localhost:3001",
           "https://data-dragons.netlify.app"]
CORS(app, resources={r"/ws/*": {"origins": ALLOWED, "methods": ["GET", "POST", "DELETE"]}})
# for sake of simplicity: please insert your connection details
connection_details = read_env_file(file_name_append="demo")
if connection_details["GOODDATA_HOST"]:
    gd = LoadGoodDataSdk(connection_details["GOODDATA_HOST"], connection_details["GOODDATA_API_TOKEN"])
    VERIFIED = True
else:
    VERIFIED = False
    raise ValueError("cannot run without environment details, specify in the .env.test file ...")


def authorized() -> bool:
    # Access the Authorization header
    authorization_header = request.headers.get('Authorization')

    # Check if an Authorization header with a Bearer token exists
    if authorization_header and authorization_header.startswith('Bearer '):
        # Print the Bearer token and address for demonstration (you can use the values as needed)
        print(f'''"Bearer": "{authorization_header.split(' ')[1]}",\n
            "User-Agent": "{request.headers.get('User-Agent')}",\n
            "Content-Type": "{request.headers.get('Content-Type')}"''')
        return True
    else:
        # No valid Bearer token found
        print(
            f'''"Bearer": "no frontend token stored",\n"User-Agent": "{request.headers.get('User-Agent')}",\n"Content-Type": "{request.headers.get('Content-Type')}"''')
        return True


def static_content(data_frame: DataFrame, content_type: str = "html") -> object:
    settings = {
        "html": "template.html",
        "css": "static/style.css",
        "html_final": "report.html",
        "first_visual": "static/visual.png",
        "first_table": data_frame.to_html(),
        "pdf": "report.pdf",
    }
    # prepare template
    env: Environment = Environment(loader=FileSystemLoader("static"))
    template = env.get_template(settings[content_type])
    return template.render(settings)


@app.route('/')
def home():
    return {
        "admin_access": gd.admin,
        "default": {
            "workspace": connection_details["GOODDATA_DEFAULT_WORKSPACE"],
            "dashboard": connection_details["GOODDATA_DEFAULT_DASHBOARD"],
            "visualization": connection_details["GOODDATA_DEFAULT_INSIGHT"]
        },
        "endpoint": connection_details["GOODDATA_HOST"],
        "help": {
            "/export": '?ws="workspace_id"&db="dashboard_id"&vis="visual_id"',
            "/ws": '?action="{[view/create/manage/delete/export]}"&id="feature_id"&name="if_to_be_changed"',
            "/provision": '?source="workspace_id"&target="workspace_id"',
            "ai-/create-deepAR": "?workspace_id=&insight_id=&prediction_length=90&context_length=90",
            "ai-/predict-deepAR": "?timeserie=0&stop_endpoint=True",
            "ai-/clean-up-deepAR": "used for clearing up space for DeepAR models",
            "ai-/create-RCF": "?workspace_id=&insight_id=",
            "ai-/predict-RCF": "-",
            "ai-/clean-up-RCF": "used for clearing up space for RCF models",
        },
        "organization": gd.organization().attributes.name,
        "workspaces": [f"{w.id}: {w.name}" for w in gd.workspaces]
    }


# Add a flask route to expose information
app.add_url_rule("/healthcheck", "healthcheck", view_func=lambda: HealthCheck().run())


@app.route('/export', methods=['GET', 'POST', 'DELETE'])
def export():
    export_format = request.args.get('format', 'PDF')
    if not export_format:  # and action not in (['view', 'create', 'manage', 'export', 'delete']):
        raise Exception("Please provide valid output content_type (PDF, PPT, XLS)")
    static = bool(request.args.get('static', True))

    dash_id = request.args.get('db', connection_details["GOODDATA_DEFAULT_DASHBOARD"])
    vis_id = request.args.get('vis', connection_details["GOODDATA_DEFAULT_INSIGHT"])
    ws_id = request.args.get('ws', connection_details["GOODDATA_DEFAULT_WORKSPACE"])

    if 'pdf' in export_format.lower():
        gd.details(wks_id=ws_id)
        if not static:  # exporting dashboard instead / hardcoded - first one
            return gd.export(wks_id=ws_id, export_format="pdf")
        else:  # inspired by: https://www.geeksforgeeks.org/how-to-create-pdf-files-in-flask/
            # exports given visual to a PDF file (dashboard not used)
            content_page = static_content(gd.data(ws_id=ws_id, vis_id=vis_id))

            print(f"... returning the generated PDF file from workspace: {ws_id}\n using visualization: {vis_id}")
            try:
                return render_pdf(HTML(string=content_page))
            except Exception:
                return {'message': "some bad during export happened."}
    elif 'ppt' in export_format.lower():
        return {'message': "Powerpoint not yet implemented."}
    else:
        return {'message': "unknown method of export: " + export_format}


@app.route('/ws', methods=['GET', 'POST', 'DELETE'])
def workspace():
    # You can define logic to retrieve content based on the address input here.
    # For this example, let's assume a simple dictionary mapping addresses to content.
    action = request.args.get('action', 'view')
    if not action:  # and action not in (['view', 'create', 'manage', 'export', 'delete']):
        raise Exception("Please provide valid workspace action")

    if authorized():
        ws_id = request.args.get('id', connection_details["GOODDATA_DEFAULT_WORKSPACE"])
        name = request.args.get('name', ws_id)
        parent = request.args.get('parent', '')
        if action == 'view':
            return jsonify(gd.tree(ws_id).to_dict())
        elif action == 'create':
            if len(ws_id) > 0:
                return gd.create(ent_id=ws_id, name=name, parent=parent)
            else:
                return {"message": "no id provided for creating new name"}
        elif action == 'manage':
            return {"message": "Functionality not yet implemented... "}
        elif action == 'delete':
            return {"message": "Functionality not yet implemented... "}
        elif action == 'export':
            pass  # for now
            # if len(ws_id) > 0:
            #     if len(name) > 0 and name == "yaml":
            #         content = gd.get_yaml(ws_id)
            #     elif name == "json":
            #         content = gd.get_json_from_yaml(gd.get_yaml(wks_id)
            # else:
            #     return {"message": "no id provided for export"}
        else:
            return {"message": "Not recognized action..."}
    else:
        return {"message": "no valid token submitted"}


@app.route('/provision', methods=['GET', 'POST', 'DELETE'])
def provision():
    # You can define logic to retrieve content based on the address input here.
    # For this example, let's assume a simple dictionary mapping addresses to content.
    if authorized():
        source_id = request.args.get('source', connection_details["GOODDATA_DEFAULT_WORKSPACE"])
        target_id = request.args.get('target', 'new')
        gd.create(ent_id=target_id, of_type="ws")
        # TODO: fill content
        return {"message": f"Workspace {target_id} provisioned from {source_id}"}
    else:
        return {"message": "no valid token submitted"}


# @app.route("/create-powerpoint")
# def createPowerPoint():
#     dashboard_id = request.args.get('dashboard_id')
#
#     if try_to_export(dashboard_id, type="dashboard", ws=app.config["GD_WORKSPACE"]):
#         print(f'Succesfully exported "dashboard" id: {dashboard_id} in the workspace: {app.config["GD_WORKSPACE"]}')
#
#     for filename in glob.glob("*.pdf"):
#         pdffile = filename
#         doc = fitz.open(pdffile)
#         for page_index in range(doc.page_count):
#             try:
#                 page = doc.load_page(page_index)
#                 zoom = 2
#                 mat = fitz.Matrix(zoom, zoom)
#                 pix = page.get_pixmap(matrix=mat, dpi=1200)
#                 output = 'page_' + filename.replace(".pdf", "") + "-" + str(page_index) + ".png"
#                 pix.save(output)
#             except Exception as e:
#                 print(str(filename) + ' > ' + str(e))
#         doc.close()
#
#     OUTPUT_TAG = "dashboard_export"
#
#     # new
#     prs = pptx.Presentation()
#     # open
#     # prs_exists = pptx.Presentation("some_presentation.pptx")
#
#     # default slide width
#     #prs.slide_width = 9144000
#     # slide height @ 4:3
#     # prs.slide_height = 6858000
#     # slide height @ 16:9
#     prs.slide_height = 5143500
#
#     # title slide
#     # slide = prs.slides.add_slide(prs.slide_layouts[0])
#     # blank slide
#     #slide = prs.slides.add_slide(prs.slide_layouts[6])
#
#     # set title
#     # title = slide.shapes.title
#     # title.text = OUTPUT_TAG
#
#     pic_left = int(prs.slide_width * 0.15)
#     pic_top = int(prs.slide_height * 0.001)
#     pic_width = int(prs.slide_width * 0.7)
#
#     for g in glob.glob(os.getcwd() + "/page*.png"):
#         slide = prs.slides.add_slide(prs.slide_layouts[6])
#
#         tb = slide.shapes.add_textbox(0, 0, prs.slide_width, pic_top / 2)
#         p = tb.text_frame.add_paragraph()
#         p.font.size = pptx.util.Pt(14)
#
#         imageio.imread(g)
#         pic_height = int(pic_width * 0.9)
#         slide.shapes.add_picture(g, pic_left, pic_top, pic_width, pic_height)
#
#     prs.save("%s.pptx" % OUTPUT_TAG)
#
#     bucket_name = "gooddata-demo"
#     bucket_prefix = "dashboard-plugins/pptx-export/dashboard_export.pptx"
#
#     s3_client = client('s3', aws_access_key_id=app.config["AWS_SERVER_PUBLIC_KEY"],
#                        aws_secret_access_key=app.config["AWS_SERVER_SECRET_KEY"])
#     transfer = S3Transfer(s3_client)
#     transfer.upload_file('dashboard_export.pptx', bucket_name, bucket_prefix,
#                          extra_args={'ServerSideEncryption': "AES256"})
#


# Deep AR

# http://localhost:5000/create-deepAR?workspace_id=&insight_id=&prediction_length=90&context_length=90
@app.route("/create-deepAR")
def create_deepAR_model():
    insight_id = request.args.get('insight_id')
    workspace_id = request.args.get('workspace_id', connection_details["GOODDATA_DEFAULT_WORKSPACE"])
    prediction_length = int(request.args.get("prediction_length"))
    context_length = int(request.args.get("context_length"))

    gd._sdk.export.export_tabular_by_insight_id(
        insight_id=insight_id,
        workspace_id=workspace_id,
        file_format="CSV",
        file_name="insight_data"
    )

    DeepArDatasetImport().import_dataset(boto_session=boto_session, sagemaker_session=sagemaker_session,
                                         deepAR_input=DeepARInput(
                                             prediction_length=prediction_length,
                                             context_length=context_length
                                         ))

    return {"message": "Deep AR created..."}


# http://localhost:5000/predict-deepAR?timeserie=0&stop_endpoint=True
@app.route("/predict-deepAR")
def predict_deepAR():
    timeserie = int(request.args.get('timeserie'))
    stop_endpoint = str(request.args.get('stop_endpoint')).lower() in ("yes", "true", "t", "1")
    response = make_response(DeepARPredictor().predict(timeserie, stop_endpoint))

    response.headers.add('Access-Control-Allow-Origin', '*')

    return {"message": f"Deep AR started...\n {response}"}


@app.route("/clean-up-deepAR")
def clean_up_deepAR():
    DeepARCleanUp().clean_up()
    return {"message": "Deep AR cleaned..."}


# http://localhost:5000/create-RCF?workspace_id=&insight_id=
@app.route("/create-RCF")
def create_RCF_model():
    insight_id = request.args.get('insight_id')
    workspace_id = request.args.get('workspace_id')

    gd._sdk.export.export_tabular_by_insight_id(
        insight_id=insight_id,
        workspace_id=workspace_id,
        file_format="CSV",
        file_name="insight_data"
    )

    RCFDatasetImport().import_dataset(boto_session=boto_session, sagemaker_session=sagemaker_session)

    return {"message": "RCF model created..."}


@app.route("/predict-RCF")
def predict_RCF():
    response = make_response(RCFPredictor().predict())
    response.headers.add('Access-Control-Allow-Origin', '*')

    return {"message": f"RCF model predicted...\n {response}"}


@app.route("/clean-up-RCF")
def clean_up_RCF():
    RCFCleanUp().clean_up()

    return {"message": "RCF model cleaned..."}


if __name__ == "__main__":
    app.run(debug=True)
