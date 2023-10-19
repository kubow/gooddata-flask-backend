from common import LoadGoodDataSdk #, visualize_workspace_hierarchy
from flask import Flask,request, jsonify, Response
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app, resources={r"/ws/*": {"origins": ["https://127.0.0.1:8080", "https://data-dragons.netlify.app"], "methods": ["GET", "POST", "DELETE"]}})

def get_headers():
    # Access the Authorization header
    authorization_header = request.headers.get('Authorization')

    # Check if an Authorization header with a Bearer token exists
    if authorization_header and authorization_header.startswith('Bearer '):
        # Extract the Bearer token
        bearer_token = authorization_header.split(' ')[1]

        # Print the Bearer token and address for demonstration (you can use the values as needed)
        content = {
        'Bearer': bearer_token,
        'User-Agent': request.headers.get('User-Agent'),
        'Content-Type': request.headers.get('Content-Type')
        }

    else:
        # No valid Bearer token found
        content = {
        'Bearer': 'empty',
        'User-Agent': request.headers.get('User-Agent'),
        'Content-Type': request.headers.get('Content-Type')
        }
    return content

def get_gooddata(endpoint: str="https://jav.demo.cloud.gooddata.com/",
    token: str="SmFrdWIuVmFqZGE6c3RyZWFtbGl0X2hhY2thdG9uOmZjbW0xY3c3ZThSU09zU3hCcTFVR0UyWlRlSVc3VnV5"
    ):
    return LoadGoodDataSdk(endpoint, token)

def export_ws(wks_id: str, export_type: str):
    gooddata = get_gooddata()
    if export_type == "yaml":
        content = gooddata.get_yaml(wks_id)
    elif export_type == "json":
        content = gooddata.get_json_from_yaml(gooddata.get_yaml(wks_id))
    return jsonify(content)

def manage_ws(wks_id: str, wks_name: str):
    gooddata = get_gooddata()
    gooddata.manage_wks(wks_id, wks_name, None) # Change name, or delete. id and parent_id cannot be changed
    return {"message": f"Succesfully renamed {wks_id}: new name {wks_name}"} 

def create_ws(wks_id: str, wks_name: str, parent_id: str=""):
    gooddata = get_gooddata()
    gooddata.create_wks(wks_id, wks_name, parent_id)
    return {"message": f"Workspace {wks_id} created... "} 

def delete_ws(wks_id: str):
    gooddata = get_gooddata()
    gooddata.delete_wks(wks_id)
    return {"message": f"Workspace {wks_id} deleted... "} 

def view_ws(wks_id: str=""):
    # here we will generate the whole structure
    gooddata = get_gooddata()
    if len(wks_id)> 0:
        hierarchy = gooddata.visualize_workspace_hierarchy(wks_id)
    else:
        hierarchy = gooddata.visualize_workspace_hierarchy()
    return jsonify(json.loads(hierarchy))

@app.route('/')
def home():
    return {"message": "This is the default page for GoodData pink pages."} 

@app.route('/ws', methods=['GET', 'POST', 'DELETE'])
def workspace():
    # You can define logic to retrieve content based on the address input here.
    # For this example, let's assume a simple dictionary mapping addresses to content.
    verify = get_headers()

    if "Bearer" in verify.keys():
        id = request.args.get('id', '')
        action = request.args.get('action', '')
        name = request.args.get('name', '')
        parent = request.args.get('parent', '')
        if action == 'view':
            if len(id) > 0:
                return view_ws(id)
            else:
                return view_ws()
        elif action == 'create':
            if len(id) > 0:
                if len(name) > 0:
                    return create_ws(id, name, parent)
                else:
                    return create_ws(id, id, parent)
            else:
                return {"message": "no id provided for creating new name"}
        elif action == 'manage':
            if len(id) > 0:
                if len(name)> 0:
                    return manage_ws(id, name)
                else:
                    return manage_ws(id, id)
            else:
                return {"message": "no id provided for management"}
        elif action == 'delete':
            if len(id) > 0:
                return delete_ws(id)
            else:
                return {"message": "no id provided for deletion"}
        elif action == 'export':
            if len(id) > 0:
                if len(name)> 0 and name=="yaml":
                    return export_ws(id, name)
                else:
                    return export_ws(id, "json")
            else:
                return {"message": "no id provided for export"}
        else:
            return {"message": "Not recognized action..."}
    else:
        return {"message": "Cannot find valid authorization ..."}


@app.route('/provision', methods=['GET', 'POST', 'DELETE'])
def provision():
    # You can define logic to retrieve content based on the address input here.
    # For this example, let's assume a simple dictionary mapping addresses to content.
    verify = get_headers()

    if "Bearer" in verify.keys():
        source_id = request.args.get('source', 'ws-snowflake-demo')
        target_id = request.args.get('target', 'new')
        gooddata = get_gooddata()
        gooddata.put_wks(source_id, gooddata.get_wks(target_id))
    return "Workspace provisioned"


if __name__ == '__main__':
    app.run(debug=True)