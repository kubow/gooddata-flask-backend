import streamlit as st
# from common import LoadGoodDataSdk, visualize_workspace_hierarchy

def check_params(dictionary):
    return dictionary

def main():
    #gooddata = LoadGoodDataSdk()
    # 1 - initial selections and class variable
    # Check the URL route
    if not st.experimental_get_query_params():
        st.write()
    else:
        st.write(check_params(st.experimental_get_query_params()))
        # st.write(visualize_workspace_hierarchy(gooddata._sdk))

if __name__ == "__main__":
    main()
