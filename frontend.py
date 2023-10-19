import streamlit as st

from common import LoadGoodDataSdk


def main():
    # 1 - initial selections and class variable
    if not "sels" in st.session_state:
        st.session_state["sels"] = {
            "users":  [],
            "groups":  [],
            "workspaces":  [],
            "dashboards": []
        }
    if not "gd" in st.session_state:
        st.session_state["gd"] = LoadGoodDataSdk()

    # 2 - set page layout
    st.set_page_config(
        page_title="GoodData configuration app",
        page_icon="✨",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title("GoodData visualizer")
    sidebar_cont = {
        "users": st.sidebar.container(),
        "groups": st.sidebar.container(),
        "wrksp": st.sidebar.container()
    }

    with sidebar_cont["users"]:  # Initial connection setup
        st.subheader("Select your user")
        user = st.selectbox(
                "Select one of your workspaces",
                options=[w.name for w in st.session_state["gd"].users],
                key="usr_sel"
            )
        confirm = st.form_submit_button("Select")
    with sidebar_cont["groups"]:  # Initial connection setup
        with st.form(key="gd_wrks"):
            st.subheader("Select your group")
            group = st.selectbox(
                    "Select one of your groups",
                    options=[w.name for w in st.session_state["gd"].users],
                    key="ug_sel"
                )
            confirm = st.form_submit_button("Select")
    with sidebar_cont["wrksp"]:  # Workspaces selector
        with st.form(key="gd_wrks"):
            workspace = st.selectbox(
                "Select one of your workspaces",
                options=[w.name for w in st.session_state["gd"].workspaces],
                key="wks_sel"
            )
            confirm = st.form_submit_button("Select")
    
    # 3 - act if button pressed
    if user:  # CASE selected custom fields to visualize
        # TODO: tools to export
        st.write(st.session_state["gd"].users)
    elif group:  # CASE visualize insight
        st.write(st.session_state["gd"].groups)
    elif confirm:  # CASE GD.C(N) connected
        del st.session_state["sels"]["users"][:]
        del st.session_state["sels"]["groups"][:]
        del st.session_state["sels"]["workspaces"][:]
        st.session_state["gd"].select(id=workspace, type="name")
        st.session_state["sels"]["users"] = st.session_state["gd"].list(
            "metric")
        st.session_state["sels"]["users"].append(
            st.session_state["gd"].list("fact"))
        st.session_state["sels"]["groups"] = st.session_state["gd"].list(
            "attr")
        st.session_state["sels"]["workspaces"] = st.session_state["gd"].list(
            "insight")
        st.write(
            f"usersures (Facts & Metrics): {st.session_state['sels']['users']}")
        st.write(
            f"Dimensions (Attributes): {st.session_state['sels']['groups']}")
        st.write(
            f"Insights (Visualizations): {st.session_state['sels']['visu']}")
    
    else:
        st.write("Please config GoodData instance and select proper items.")


if __name__ == "__main__":
    main()
