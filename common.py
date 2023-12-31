from dotenv import dotenv_values
from os import getenv
import json
from dotenv import load_dotenv
from gooddata_sdk import GoodDataSdk, CatalogWorkspace
from pathlib import Path
from treelib import Tree
import requests
import yaml


class LoadGoodDataSdk:
    def __init__(self, endpoint: str, token: str):
        self._sdk = GoodDataSdk.create(endpoint, token)
        self.users = (
            self._sdk.catalog_user.list_users()
        )  # alternative get_declarative_users()
        self.groups = self._sdk.catalog_user.list_user_groups()
        self.datasources = self._sdk.catalog_data_source.list_data_sources()
        self.workspaces = self._sdk.catalog_workspace.list_workspaces()
        self.declarative_workspaces = self._sdk.catalog_workspace.get_declarative_workspaces()

    def create_wks(self, ws_id, name, parent_id):
        if parent_id is None:
            parent_id = ""  # Convert None to an empty string

        workspace = CatalogWorkspace(workspace_id=ws_id, name=name, parent_id=parent_id)
        self._sdk.catalog_workspace.create_or_update(workspace)

    def manage_wks(self, ws_id, name, parent_id):
        workspace = CatalogWorkspace(workspace_id=ws_id, name=name, parent_id=parent_id)
        self._sdk.catalog_workspace.create_or_update(workspace)

    def delete_wks(self, ws_id):
        self._sdk.catalog_workspace.delete_workspace(workspace_id=ws_id)

    def get_wks(self, ws_id):
        return self._sdk.catalog_workspace.get_declarative_workspace(workspace_id=ws_id)

    def put_wks(self, ws_id, layout):
        return self._sdk.catalog_workspace.put_declarative_workspace(workspace_id=ws_id, workspace=layout)

    def get_yaml(self, ws_id):
        return yaml.dump(self._sdk.catalog_workspace.get_declarative_workspace(workspace_id=ws_id), default_style='|')

    def get_json_from_yaml(self, yaml_file):
        return json.dumps(yaml_file, indent=2)

    def visualize_workspace_hierarchy(self, id: str=None):
        data = {}

        tree = Tree()
        tree.create_node("GoodData", "root")
        for workspace in self._sdk.catalog_workspace.list_workspaces():
            if id and workspace.id != id and workspace.parent_id != id:
                continue
            # print(workspace)
            parent_id = workspace.parent_id if workspace.parent_id else "root"
            # print(workspace.id, workspace.name, workspace.parent_id)
            data[workspace.id] = {
                'name': workspace.name,
                'parent_id': workspace.parent_id
            }
            workspace_structure = create_workspace_structure(data, parent_id=None)
            json_data = json.dumps(workspace_structure, indent=4)
        
        return json_data

    def organization(self):
        print(f"\nCurrent organization info:")  # ORGANIZATION INFO
        pretty(self._sdk.catalog_organization.get_organization().to_dict())
        return self._sdk.catalog_organization.get_organization()

    def first(self, of_type="user", by="id"):
        if of_type == "user":
            return first_item(self.users, by)
        elif of_type == "group":
            return first_item(self.groups, by)
        elif of_type == "datasource":
            return first_item(self.datasources, by)
        elif of_type == "workspace":
            return first_item(self.workspaces, by)

    def get_id(self, name, of_type):
        if of_type == "user":
            return [u.id for u in self.users if name == u.name][0]
        elif of_type == "group":
            return [g.id for g in self.groups if name == g.name][0]
        elif of_type == "datasource":
            return [d.id for d in self.datasources if name == d.name][0]
        elif of_type == "workspace":
            return [w.id for w in self.workspaces if name == w.name][0]
        elif of_type == "insight":
            return [w.id for w in self.workspaces if name == w.name][0]
        elif of_type == "dashboard":
            return [w.id for w in self.workspaces if name == w.name][0]

    def specific(self, value, of_type="user", by="id"):
        if by != "id":
            value = self.get_id(value, of_type)
        if of_type == "user":
            return self._sdk.catalog_user.get_user(value)
        elif of_type == "group":
            return self._sdk.catalog_user.get_user_group(value)
        elif of_type == "datasource":
            return self._sdk.catalog_data_source.get_data_source(value)
        elif of_type == "workspace":
            return self._sdk.catalog_workspace.get_workspace(value)
        elif of_type == "dashboard":
            return self._sdk.catalog_workspace_content.get_workspace(value)  # NA
        elif of_type == "insight":
            return self._sdk.insights.get_insight(value)

def create_workspace_structure(data, parent_id=None):
    workspace_list = []

    for key, value in data.items():
        if value["parent_id"] == parent_id:
            workspace = {
                "id": key,
                "name": value["name"],
                "parent_id": parent_id,
                "children": create_workspace_structure(data, key)
            }
            workspace_list.append(workspace)

    return workspace_list

def get_variables():
    try:
        load_dotenv()
        if getenv("GOODDATA_HOST") and getenv("GOODDATA_TOKEN"):
            temp = {
                "GOODDATA_HOST": getenv("GOODDATA_HOST"),
                "GOODDATA_TOKEN": getenv("GOODDATA_TOKEN"),
            }
        else:
            file = (Path(__file__).parent / ".env").resolve()
            if file.is_file():
                print(".env file read...")
                temp = dotenv_values(file)
    except Exception as ex:
        print(f"what happened: {ex}")
    finally:
        print(
            "Your workspace evnironment variables:\n",
            f"GOODDATA_HOST: {temp['GOODDATA_HOST']}\n",
            f"GOODDATA_TOKEN: {len(temp['GOODDATA_TOKEN'])} characters",
        )
        return temp


def pretty(d, indent=1, char="-"):
    for key, value in d.items():
        if isinstance(value, dict):
            pretty(value, indent + 2)
        else:
            print(f"{char * (indent)} {str(key)} : {str(value)}")


def first_item(dataset, attr=""):
    if len(dataset) < 1:
        return None
    else:
        return next(iter(dataset)).__getattribute__(attr)


def init_gd(default_env: str = "test"):
    # Load environment variables from .env.* file stored in root directory
    temp = dotenv_values(Path(__file__).resolve().parents[1] / f".env.{default_env}")

    # Access the environment variables
    host = temp["GOODDATA_HOST"]
    token = temp["GOODDATA_TOKEN"]

    sdk = GoodDataSdk.create(host, token)

    return host, token, sdk


def wipe_workspaces_and_permissions(
        wdf_id: str, workspace_ids: list[str], host: str, token: str, sdk: classmethod
) -> None:
    f"""
    This method is used when you want to wipe/delete workspaces via id and related workspace permissions
        :param sdk:
        :param host:
        :param token:
        :param wdf_id: id of the datafilter, reachable via /api/v1/entities/workspaces/parent_workspace_id/workspaceDataFilters/
        :param workspace_ids: id of the datafilter, reachable via /api/v1/entities/workspaces/parent_workspace_id/workspaceDataFilters/
        :return:
    """

    if not isinstance(wdf_id, str):
        raise ValueError("wdf_id must be a string.")

    if not isinstance(workspace_ids, list):
        raise ValueError("workspace_ids must be a list.")

    if not isinstance(host, str):
        raise ValueError("host must be a string.")

    if not isinstance(token, str):
        raise ValueError("token must be a string.")

    # Clear everything out
    # Delete workspaces
    for workspace in workspace_ids:
        try:
            sdk.catalog_workspace.delete_workspace(workspace_id=workspace)
            print(workspace, "deleted")
        except ValueError as ve:
            print("Error:", ve)

    # delete data filter
    api_url = f"{host}/api/v1/entities/workspaces/Staging/workspaceDataFilters/{wdf_id}"

    # Request headers with the Authorization header containing the API token
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        # Make a DELETE request to the API
        response = requests.delete(api_url, headers=headers)

        # Check if the request was successful (status code 200-299 indicates success)
        if 200 <= response.status_code < 300:
            print("API call was successful. Data filter deleted.")
        else:
            print(f"API call failed. Status code: {response.status_code}")
            print("Response:", response.text)

    except requests.exceptions.RequestException as e:
        print("Error making API call:", e)


if __name__ == "__main__":
    # host, token, sdk = init_gd()
    gooddata = LoadGoodDataSdk(endpoint="GOODDATA_HOST",
    token="GOODDATA_TOKEN")
    # for user in gooddata.users:
    #     print(f"user {user.id} with relations {user.relationships}")

    # VIEW func
    print("################# All hierarchy")
    print(gooddata.visualize_workspace_hierarchy())
    print("################# Production with one child")
    print(gooddata.visualize_workspace_hierarchy("production"))
    print("################# Test with")
    print(gooddata.visualize_workspace_hierarchy("test"))
    
    # json_data = gooddata.visualize_workspace_hierarchy()
    # print(json_data)

    # Create or Update
    # gooddata.create_wks("abc", "Department A", "ws-snowflake-demo")
    # gooddata.create_wks("def", "Department B", "ws-snowflake-demo")

    # gooddata.create_wks("ghi", "Department A1", "abc")
    # gooddata.manage_wks("test2", "Test", "production") # Change name, or delete. id and parent_id cannot be changed
    # gooddata.delete_wks("dev_hack")

    # Push to Prod
    # gooddata.get_wks("dev_hack")
    # gooddata.put_wks("prod_hack", gooddata.get_wks("dev_hack"))

    # Get yaml
    # print(gooddata.get_yaml("dev_hack"))

    # Get json
    # print(gooddata.get_json_from_yaml(gooddata.get_yaml("dev_hack")))
