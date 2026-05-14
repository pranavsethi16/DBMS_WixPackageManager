import streamlit as st
import pandas as pd
from backend.db_manager import DatabaseManager
from streamlit_agraph import agraph, Node, Edge, Config
from collections import defaultdict

st.set_page_config(
    page_title="Wix Package Manager",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def get_db_connection():
    db = DatabaseManager(host='localhost', database='wix_test', user='root', password='pranav')
    db.connect()
    return db

db = get_db_connection()

with st.sidebar:
    st.title(" Navigation")
    st.markdown("---")
    menu = [" Search Packages", " Environment View", " Dependency Tree", " Install Package", " Graph"]
    choice = st.radio("Go to", menu, label_visibility="collapsed")
    st.markdown("---")
    st.caption("Wix Package Management System v1.0")

st.title("Wix Package Management System")
st.markdown("Manage and visualize your package environments, dependencies, and installations.")
st.divider()

if choice == " Search Packages":
    st.subheader(" Search Packages")
    st.caption("Find packages containing a specific keyword.")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        keyword = st.text_input("Enter package keyword:", placeholder="e.g., react, database, ui...")
    with col2:
        st.write("")
        st.write("")
        search_btn = st.button("Search", use_container_width=True, type="primary")
        
    if search_btn:
        if keyword:
            with st.spinner("Searching..."):
                results = db.query_1_search_packages(keyword)
            if results:
                st.success(f"Found {len(results)} package(s)")
                st.dataframe(pd.DataFrame(results), use_container_width=True)
            else:
                st.warning("No packages found containing that keyword.")
        else:
            st.warning("Please enter a keyword to search.")

elif choice == " Environment View":
    st.subheader(" Environment View")
    st.caption("Review the complete list of installed packages across all available environments.")
    
    if st.button("Load Environment Packages", type="primary"):
        with st.spinner("Loading environments..."):
            results = db.query_9_env_packages()
        if results:
            st.dataframe(pd.DataFrame(results), use_container_width=True)
        else:
            st.warning("No installed packages found in any environment.")

elif choice == " Dependency Tree":
    st.subheader(" Dependency Tree")
    st.caption("Explore the full recursive dependency tree for a specific package version.")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        version_id = st.number_input("Enter Version ID", min_value=1, step=1, value=1)
    with col2:
        st.write("")
        st.write("")
        view_btn = st.button("View Dependencies", use_container_width=True, type="primary")
        
    if view_btn:
        with st.spinner("Fetching dependency tree..."):
            results = db.query_13_recursive_dependencies(version_id)
        if results:
            st.dataframe(pd.DataFrame(results), use_container_width=True)
        else:
            st.info(f"No dependencies found for Version ID {version_id}.")

elif choice == " Install Package":
    st.subheader(" Install Package (Trigger Test)")
    st.caption("Attempt to install a package to test database triggers and dependency constraints.")
    
    with st.spinner("Loading options..."):
        envs = db.get_all_environments()
        versions = db.get_all_versions()
    
    if not envs or not versions:
        st.error("Error: Could not load environments or versions from the database.")
    else:
        env_options = {f"Env {e['env_id']}: {e['env_name']}": e['env_id'] for e in envs}
        version_options = {f"ID {v['version_id']} - {v['package_name']} (v{v['version_no']})": v['version_id'] for v in versions}
        
        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1:
                selected_env_label = st.selectbox("Select Environment", list(env_options.keys()))
                env_id = env_options[selected_env_label]
            with col2:
                selected_version_label = st.selectbox("Select Package Version", list(version_options.keys()))
                version_id = version_options[selected_version_label]
                
            st.write("")
            install_btn = st.button("Install Package", use_container_width=True, type="primary")
            
        if install_btn:
            with st.spinner("Installing..."):
                success = db.test_trigger_install_package(env_id, version_id)
            
            if success:
                st.success(f" Success! Version ID {version_id} successfully installed into Environment ID {env_id}.")
            else:
                st.error(" Installation Failed: Blocked by database trigger. Check terminal output for logs to see if it was due to a conflict or missing dependency.")

elif choice == " Graph":
    st.subheader(" Interactive Dependency Graph")
    st.caption("Visualizing what versions depend on which packages. Package nodes grow larger based on dependency count.")
    
    with st.spinner("Rendering universe..."):
        raw_edges = db.query_dependency_graph_data()
        
    if not raw_edges:
        st.info("No dependencies found in the database to graph.")
    else:
        nodes_dict = {}
        edges = []
        package_dependency_count = defaultdict(int)
        
        COLOR_LIGHTER = "#D0E1E1"
        COLOR_LIGHT = "#546E7A"
        COLOR_TEAL = "#65A6A7"
        COLOR_DARK = "#3A6F75"
        COLOR_DARKER = "#162D35"
        COLOR_EDGE = "rgba(100, 100, 100, 0.3)"
        
        VERSION_NODE_SIZE = 5
        MIN_PACKAGE_SIZE = 10
        MAX_PACKAGE_SIZE = 35
        GROWTH_PER_DEPENDENCY = 1
        
        for row in raw_edges:
            v_node_id = f"V_{row['version_id']}"
            p_node_id = f"P_{row['required_package_id']}"
            
            package_dependency_count[p_node_id] += 1
            
            edges.append(
                Edge(
                    source=v_node_id, 
                    target=p_node_id, 
                    color=COLOR_EDGE, 
                    width=1,
                    length=200
                )
            )
            
            if v_node_id not in nodes_dict:
                nodes_dict[v_node_id] = Node(
                    id=v_node_id, 
                    label=f"{row['dependent_pkg_name']}\n(v{row['dependent_version_no']})", 
                    size=VERSION_NODE_SIZE, 
                    shape="dot",
                    borderWidth=2,
                    color={
                        "background": "transparent", 
                        "border": COLOR_TEAL,        
                        "highlight": {"border": COLOR_LIGHTER, "background": "transparent"}
                    },
                    font={"color": COLOR_LIGHTER, "size": 12} 
                )
            
            if p_node_id not in nodes_dict:
                nodes_dict[p_node_id] = {
                    "id": p_node_id,
                    "label": row['required_pkg_name'],
                }

        for p_id, count in package_dependency_count.items():
            nodes_dict[p_id] = Node(
                id=p_id,
                label=nodes_dict[p_id]["label"],
                size=min(MAX_PACKAGE_SIZE, MIN_PACKAGE_SIZE + (count * GROWTH_PER_DEPENDENCY)),
                shape="dot", 
                color={
                    "background": COLOR_DARK, 
                    "border": COLOR_DARKER,
                    "highlight": {"background": COLOR_TEAL, "border": COLOR_LIGHTER}
                },
                font={"color": COLOR_LIGHTER, "size": 14, "face": "bold"} 
            )

        config = Config(
            width="100%",
            height=700,
            directed=True,
            physics=True,
            hierarchical=False,
            nodeHighlightBehavior=True,
            highlightColor=COLOR_LIGHTER,
            collapsible=False,
            layout={"improvedLayout": True},
            interaction={
                "zoomSpeed": 0.3,       
                "dragView": True,       
                "hover": True
            }
        )

        st.markdown("---")
        
        with st.container(border=True):
            agraph(nodes=list(nodes_dict.values()), edges=edges, config=config)
        
        st.caption(f"⭕ **Hollow Teal Circles**: Specific Package Versions | 🟢 **Filled Dark Circles**: Base Packages (Size = popularity)")