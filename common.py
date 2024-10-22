from dotenv import dotenv_values
# import FPDF
from gooddata_sdk import (GoodDataSdk, CatalogPermissionAssignments, CatalogDeclarativeDashboardPermissionsForAssignee,
                          CatalogDataSourcePermissionAssignment, CatalogWorkspacePermissionAssignment,
                          CatalogAssigneeRule, CatalogAssigneeIdentifier, CatalogPermissionsForAssigneeRule,
                          CatalogWorkspace, CatalogUser, CatalogUserGroup)
from gooddata_pandas import GoodPandas
import graphviz
import math
from pandas import read_csv
from pathlib import Path
from tabulate import tabulate
from treelib import Tree
import requests


class LoadGoodDataSdk:
    def __init__(self, gd_host: str = "", gd_token: str = ""):
        print(
            "--- Using SEE monkey-patched GoodData wrapper ---"
            "Your workspace environment variables:\n",
            f"GOODDATA_HOST: {gd_host} / GOODDATA_API_TOKEN: {len(gd_token)} characters",
        )
        if gd_host:
            self._sdk = GoodDataSdk.create(gd_host, gd_token)
            self._gp = GoodPandas(gd_host, gd_token)
            self._df = None
            self.workspaces = self._sdk.catalog_workspace.list_workspaces()
            try:
                self.users = (
                    self._sdk.catalog_user.list_users()
                )  # alternative get_declarative_users()
                self.groups = self._sdk.catalog_user.list_user_groups()
                self.datasources = self._sdk.catalog_data_source.list_data_sources()
                self.admin = True
            except Exception as ex:
                self.admin = False
                print(ex)

    def clear_cache(self, ds_id: str):
        if ds_id:
            self._sdk.catalog_data_source.register_upload_notification(data_source_id=ds_id)
        else:
            print("no datasource id submitted...")

    def create(self, ent_id: str, name: str = "", of_type: str = "ws", parent: str = ""):
        if of_type == 'ws':  # workspace
            self._sdk.catalog_workspace.create_or_update(
                CatalogWorkspace(workspace_id=ent_id, name=name, parent_id=parent)
            )
        elif of_type == 'us':  # user
            self._sdk.catalog_user.create_or_update_user(
                CatalogUser.init(user_id=ent_id, firstname=name.split(" ")[0], lastname=name.split(" ")[-1],
                                 user_group_ids=[parent])
            )
        elif of_type == 'ug':  # user group
            self._sdk.catalog_user.create_or_update_user_group(
                CatalogUserGroup.init(user_group_id=ent_id, user_group_name=name)
            )
        if of_type == 'wf':  # workspace filter
            self._sdk.catalog_workspace.create_or_update(
                CatalogWorkspace(workspace_id=ent_id, name=name, parent_id=parent)
            )
        elif of_type == 'uf':  # user filter
            self._sdk.catalog_user.create_or_update_user(
                CatalogUser.init(user_id=ent_id, firstname=name.split(" ")[0], lastname=name.split(" ")[-1],
                                 user_group_ids=[parent])
            )

    def data(self, ws_id="", vis_id="", pdf_export=False, path="", using_pandas=True):
        # returns data frame or pdf / must run details first
        if vis_id:
            if pdf_export:
                dataframe_to_pdf(self._df.for_visualization(visualization_id=vis_id), pdf_path=path, num_pages=2)
            else:
                if using_pandas:
                    return self._df.for_visualization(visualization_id=vis_id)
                else:
                    x = self._sdk.visualizations.get_visualization(workspace_id=ws_id, visualization_id=vis_id)
                    return self._sdk.tables.for_visualization(workspace_id=ws_id, visualization=x)
        else:
            return self._gp.data_frames(ws_id)

    def details(self, wks_id: str = "", by: str = "id") -> []:
        # display details about workspace in detail (all objects within)
        if not wks_id:
            wks_id = self.first(of_type="workspace")
            print("selecting first workspace as no one submitted")
        if by != "id":
            wks_id = self.get_id(wks_id, of_type="workspace")
        self._df = self.data(ws_id=wks_id)
        return self._sdk.catalog_workspace_content.get_declarative_analytics_model(wks_id).analytics

    def export(self, wks_id: str = "", by: str = "id", vis_id: str = "", export_format: str = "",
               location: str = ""):
        # export workspace to a physical drive
        if not wks_id:
            wks_id = self.first(of_type="workspace")
            print(f"selecting first workspace (id: {wks_id}) as no one submitted")
        if by != "id":
            wks_id = self.get_id(wks_id, of_type="workspace")
        if export_format.lower() == "pdf":
            if vis_id:
                return self._sdk.export.export_tabular_by_visualization_id(vis_id, wks_id, "PDF", "insight_data")
            else:
                return self._sdk.export.export_pdf(wks_id, self.first("dashboard"), "Dashboard_1.pdf")
        elif export_format.lower() == "csv":
            if vis_id:
                return self._sdk.export.export_tabular_by_visualization_id(vis_id, wks_id, "CSV", "insight_data")
            else:
                return self._sdk.catalog_workspace_content.load_declarative_analytics_model(wks_id, Path(location))
        else:
            return self._sdk.catalog_workspace_content.load_declarative_analytics_model(wks_id, Path(location))

    def first(self, of_type="user", by="id"):
        if of_type == "user":
            return first_item(self.users, by)
        elif of_type == "group":
            return first_item(self.groups, by)
        elif of_type == "datasource":
            return first_item(self.datasources, by)
        elif of_type == "dashboard":
            analytics = self.details(first_item(self.workspaces, by))
            return first_item(analytics.analytical_dashboards, by)
        elif of_type == "workspace":
            return first_item(self.workspaces, by)

    def get_id(self, name, of_type, main=""):
        if not name:
            return None
        if of_type == "user":
            return [u.id for u in self.users if name == u.name][0]
        elif of_type == "group":
            return [g.id for g in self.groups if name == g.name][0]
        elif of_type == "datasource":
            return [d.id for d in self.datasources if name == d.name][0]
        elif of_type == "workspace":
            return [w.id for w in self.workspaces if name == w.name][0]
        else:
            temp = self.details(wks_id=main, by="id")
            if of_type == "insight":
                return [i.id for i in temp.visualization_objects if name == i.title][0]
            elif of_type == "dashboard":
                return [w.id for w in temp.analytical_dashboards if name == w.title][0]
            elif of_type == "metric":
                return [w.id for w in temp.metrics if name == w.title][0]

    def organization(self):
        # print(f"\nCurrent organization id:{self._sdk.catalog_organization.get_organization().id}")
        # pretty(self._sdk.catalog_organization.get_organization().to_dict())
        return self._sdk.catalog_organization.get_organization()

    def altug(self, of_type='user', level=0, id='',
              ds_id='', ds_right='USE',
              ws_id='', ws_right='VIEW',
              ):
        # initial attempt to control users and groups
        print(f"\nAltering users/groups:")  # ORGANIZATION INFO
        if level == 0:
            permission_assignment = CatalogPermissionAssignments(
                workspaces=[CatalogWorkspacePermissionAssignment(
                    id=ws_id,
                    permissions=[ws_right],
                    hierarchy_permissions=[]
                )],
                data_sources=[CatalogDataSourcePermissionAssignment(
                    id=ds_id,
                    permissions=[ds_right]
                )]
            )
            if of_type == 'user':
                self._sdk.catalog_user.manage_user_permissions(user_id=id, permission_assignments=permission_assignment)
                return print("created permissions over a user")
            else:
                self._sdk.catalog_user.manage_user_group_permissions(user_group_id=id,
                                                                     permission_assignments=permission_assignment)
                return print("created permissions over a group")
        else:
            if of_type == 'user':
                assignee = CatalogAssigneeIdentifier(id=id, type="userGroup")
            else:
                assignee = CatalogAssigneeIdentifier(id=id, type="user")

            permission_assignment = CatalogDeclarativeDashboardPermissionsForAssignee(
            )
            self._sdk.catalog_permission.manage_dashboard_permissions(
                workspace_id=ws_id, dashboard_id=ds_id,
                permissions_for_assignee=[permission_assignment]
            )

    def specific(self, value, of_type="user", by="id", ws_id=""):
        # return specific object from semantic definition by its type
        if by != "id":
            value = self.get_id(value, of_type, main=ws_id)
            by = "id"
        if of_type == "user":
            return self._sdk.catalog_user.get_user(value)
        elif of_type == "group":
            return self._sdk.catalog_user.get_user_group(value)
        elif of_type == "datasource":
            return self._sdk.catalog_data_source.get_data_source(value)
        elif of_type == "workspace":
            return self._sdk.catalog_workspace.get_workspace(value)
        elif of_type == "dashboard":
            return [d for d in self.details(ws_id, by).analytical_dashboards if d.id == value][0]
        elif of_type == "insight":
            # return self._sdk.insights.get_insight(value)
            return self.data(ws_id=ws_id, vis_id=value)
        elif of_type == "metric":
            return [m for m in self._sdk.catalog_workspace_content.get_metrics_catalog(ws_id) if m.id == value][0]

    def tree(self, of_id: str = "") -> Tree:
        # gives you all node descendants or the whole structure (or of a specific id instead)
        tree = Tree()
        tree.create_node("Workspace list", "root")
        for workspace in self.workspaces:
            parent_id = workspace.parent_id if workspace.parent_id else "root"
            if of_id and of_id not in (workspace.parent_id, workspace.id):  # TODO: check if filters well
                continue  # searching only for valid descendants
            if tree.get_node(workspace.id):
                continue  # we already established the node
            elif tree.get_node(parent_id):
                tree.create_node(workspace.name, workspace.id, parent=parent_id)
            else:
                temp_root = self.specific(parent_id, of_type="workspace")
                temp_parent_id = temp_root.parent_id if temp_root.parent_id else "root"
                tree.create_node(temp_root.name, temp_root.id, parent=temp_parent_id)
                tree.create_node(workspace.name, workspace.id, parent=parent_id)
        # tree.show(line_type="ascii-em")
        return tree

    def schema(self, dashboard_name, ws_id):
        # create a dashboard schema by parsing its sections and visuals
        schema = graphviz.Digraph()
        schema.attr(ratio='0.5', fontsize="25")
        temp = self.specific(dashboard_name, of_type="dashboard", by="name", ws_id=ws_id)

        root = temp.title
        # Create nodes for each section
        for section in temp.content['layout']['sections']:  # IDashboardLayoutSection
            if 'header' in section and len(section['header']) > 0:
                schema.edge(root, f"Section-{section['header']['title']}")
                sec_root = f"Section-{section['header']['title']}"
            else:
                sec_root = root
            for item in section['items']:  # IDashboardLayoutItem
                if item['widget']['type'] == "insight":
                    if 'title' in item['widget']:
                        schema.edge(sec_root, f"Insight-{item['widget']['title']}")
                    else:
                        print(f"no title in Insight {item['widget']}")
                elif item['widget']['type'] == "richText":
                    schema.edge(sec_root, "RichText")
                else:
                    print(f"unknown thing on dashboard: {item['widget']}")

        return schema

    def users_in_group(self, group_id):
        # return users that belong to a specific group
        listed = [user for user in self.users if user.relationships for group in user.relationships.user_groups.data if
                  group and group.id == group_id]
        return listed


def pretty(d, indent=1, char="-"):
    for key, value in d.items():
        if isinstance(value, dict):
            pretty(value, indent + 2)
        else:
            print(f"{char * indent} {str(key)} : {str(value)}")


def first_item(dataset, attr=""):
    if len(dataset) < 1:
        return None
    else:
        return next(iter(dataset)).__getattribute__(attr)


def encapsulate(column_name: str):
    if not column_name.startswith('"') and not column_name.endswith('"'):
        return '"' + column_name + '"'
    else:
        return column_name


def dataframe_to_pdf(dataframe, pdf_path, num_pages):
    rows_per_page = math.ceil(len(dataframe) / num_pages)
    # pdf = FPDF()
    for page in range(num_pages):
        start_idx = page * rows_per_page
        end_idx = min((page + 1) * rows_per_page, len(dataframe))
        page_df = dataframe.iloc[start_idx:end_idx]
        # pdf.add_page()
        # Convert DataFrame to a formatted table
        table = tabulate(page_df, headers='keys', tablefmt='grid', showindex=False)
        # Add the table to the PDF
        # pdf.set_font("Arial", size=12)
        # pdf.multi_cell(0, 10, table)
    # Save the PDF
    # pdf.output(pdf_path)


def csv_to_sql(csv_filename, limit=200):
    # return single SQL query from CSV content
    df = read_csv(csv_filename)
    columns = df.columns
    # Construct the SQL query using list comprehension
    rows = [
        "SELECT "
        + ", ".join(
            [
                f"'{str(row[col])}' AS {encapsulate(col.strip())}"
                if isinstance(row[col], str)
                else f"{str(row[col])} AS {encapsulate(col.strip())}"
                for col in columns
            ]
        )
        for _, row in df.iterrows()
    ]
    # return the dictionary of the final SQL query and table_name
    return {"title": csv_filename, "query": " UNION ALL ".join(rows[:limit]) + ";"}


### BELOW is archive connected to jupyter notebooks

def init_gd(default_env: str = "test"):
    # Load environment variables from .env.* file stored in root directory
    temp = read_env_file(file_name_append=default_env)

    # Access the environment variables
    host = temp["GOODDATA_HOST"]
    token = temp["GOODDATA_API_TOKEN"]

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
    # TODO: clear that out?

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


def visualize_workspace_hierarchy(sdk: classmethod) -> None:
    tree = Tree()
    tree.create_node("GoodData", "root")
    for workspace in sdk.catalog_workspace.list_workspaces():
        parent_id = workspace.parent_id if workspace.parent_id else "root"
        if tree.get_node(workspace.id):
            continue  # we already established the node
        elif tree.get_node(parent_id):
            tree.create_node(workspace.name, workspace.id, parent=parent_id)
        else:
            temp_root = sdk.catalog_workspace.get_workspace(parent_id)
            temp_parent_id = temp_root.parent_id if temp_root.parent_id else "root"
            tree.create_node(temp_root.name, temp_root.id, parent=temp_parent_id)
            tree.create_node(workspace.name, workspace.id, parent=parent_id)
    tree.show(line_type="ascii-em")


## ULTIMATE hack to read locally present env files

def read_env_file(file_name_append: str = "test"):
    return dotenv_values(Path(__file__).resolve().parent / f".env.{file_name_append}")


if __name__ == "__main__":
    temp = read_env_file(file_name_append="trial")  # read file .env.test
    gooddata = LoadGoodDataSdk(temp["GOODDATA_HOST"], temp["GOODDATA_API_TOKEN"])

    # print(gooddata.tree().show(line_type="ascii-em"))

    gooddata.altug(of_type='group', level=0, id='view.access',
                   ds_id='public-demo-database', ds_right='USE',
                   ws_id='gooddata_prod', ws_right='VIEW', )
