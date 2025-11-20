import streamlit as st
import base64

st.set_page_config(page_title="Data Flow Lineage Visualizer", layout="wide")

st.set_option("client.toolbarMode", "viewer")

# st.markdown("""
#     <style>
#     .stToolbarActionButton {
#         display: none !important;    
#     }

#     footer {
#         visibility: hidden;
#     }

#     </style>
#     """, unsafe_allow_html=True)


st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    </style>
    """, unsafe_allow_html=True)


if "verified" not in st.session_state:
    st.session_state.verified = False

params = st.experimental_get_query_params()
encoded_data = params.get("data", [""])[0]

if not encoded_data:
    st.error("❌ Invalid access. Please open this app through Power Apps.")
    st.stop()

try:
    decoded_email = base64.b64decode(encoded_data).decode("utf-8")
except Exception:
    st.error("❌ Invalid or corrupted link.")
    st.stop()

if not st.session_state.verified:
    
    st.title("Data Flow Lineage Visualizer")

    st.write("Please verify your email to continue:")
    user_email = st.text_input("Enter your company email:")

    if st.button("Verify"):
        if not user_email:
            st.warning("Please enter your email.")

        elif user_email.strip().lower() == decoded_email.strip().lower():
            st.session_state.verified = True
            st.session_state.user_email = user_email
            st.success(f"✅ Access granted! Welcome, {user_email}")

            st.rerun()
        else:
            st.error("❌ Access denied.")

    st.stop()


import streamlit as st
import pandas as pd
import graphviz
import textwrap

if "page" not in st.session_state:
    st.session_state.page = "graph"

def go_to_system_info():
    st.session_state.page = "system_info"

def go_to_graph():
    st.session_state.page = "graph"


if st.session_state.page == "graph":

    st.set_page_config(page_title="Data FLow Lineage Visualizer", layout="wide")
    st.title("L-R Directed Data Flow")

    file_path = "Sooraj7.xlsx"
    sheet1 = "Sheet1"
    sheet2 = "Sheet2"
    sheet3 = "Sheet3"

    df = pd.read_excel(file_path, sheet_name=sheet1)
    df_desc = pd.read_excel(file_path, sheet_name=sheet2)
    df_product = pd.read_excel(file_path, sheet_name=sheet3)

    df.columns = df.columns.str.strip().str.lower()
    df.rename(columns={
        "product": "Product",
        "source system": "Source",
        "connection": "Connection",
        "target system": "Target",
        "upstream system": "Upstream",
        "downstream system": "Downstream"
    }, inplace=True)

    st.sidebar.header("Filters")
    upstream_options = ["All"] + sorted(df["Upstream"].dropna().unique().tolist())
    upstream_filter = st.sidebar.selectbox("Parent System:", upstream_options)

    if upstream_filter != "All":
        df_filtered_upstream = df[df["Upstream"] == upstream_filter]
        product_options = ["All"] + sorted(df_filtered_upstream["Product"].dropna().unique().tolist())
        target_options = ["All"] + sorted(df_filtered_upstream["Target"].dropna().unique().tolist())
    else:
        product_options = ["All"] + sorted(df["Product"].dropna().unique().tolist())
        target_options = ["All"] + sorted(df["Target"].dropna().unique().tolist())



    product_filter = st.sidebar.selectbox("Product:", product_options)
    target_filter = st.sidebar.selectbox("System:", target_options)

    graph_choice = st.sidebar.radio(
        "Select Graph Type:",
        ["Summary Graph", "Detailed Graph"],
        index=0
    )

    st.sidebar.button("System Info", on_click=go_to_system_info)
    filtered_df = df.copy()

    if upstream_filter != "All":
        filtered_df = filtered_df[filtered_df["Upstream"] == upstream_filter]

    if product_filter != "All":
        filtered_df = filtered_df[filtered_df["Product"] == product_filter]

    if target_filter != "All":
        filtered_df = filtered_df[(filtered_df["Source"] == target_filter) |
            (filtered_df["Target"] == target_filter)]

    unique_edges = filtered_df[["Source", "Connection", "Target"]].drop_duplicates()

    products_by_pair = (
        filtered_df.groupby(["Source", "Target"])["Product"]
        .apply(lambda x: sorted(set(x.dropna())))
        .to_dict()
    )

    sources = set(unique_edges["Source"])
    targets = set(unique_edges["Target"])
    upstream_nodes = sources - targets
    downstream_nodes = targets - sources



    def get_color(node):
        if node in upstream_nodes:
            return "#6DB4ED"
        elif node in downstream_nodes:
            return "#4CAF50"
        else:
            return "#FFC107"

    def wrap_text(text, width=30):
        return "<BR/>".join(textwrap.wrap(text, width=width))

    def add_node(dot_obj, node, color, include_products=False):
        incoming = []
        outgoing = []

        for (src, tgt), plist in products_by_pair.items():
            if tgt == node:
                incoming.extend(plist)
            if src == node:
                outgoing.extend(plist)

        incoming = sorted(set(incoming))
        outgoing = sorted(set(outgoing))

        source_row = df_desc[df_desc["Source_Code"].astype(str).str.strip() == str(node).strip()]
        system_name = source_row["Source_System"].iloc[0] if not source_row.empty else ""
        desc = source_row["Source_Desc"].iloc[0] if not source_row.empty else ""

        wrapped_system_name = wrap_text(str(system_name), width=30)

        header_lines = f"""
        <TABLE BORDER="0" CELLBORDER="0" CELLPADDING="1" CELLSPACING="0">
            <TR><TD ALIGN="CENTER"><B><FONT POINT-SIZE='10'>{node}</FONT></B></TD></TR>
            <TR><TD ALIGN="CENTER"><FONT POINT-SIZE='9'>{wrapped_system_name}</FONT></TD></TR>
        </TABLE>
        """

        rows = f"""
        <TR><TD ALIGN="CENTER" BORDER="0" CELLPADDING="3" VALIGN="MIDDLE">{header_lines}</TD></TR>
        """

        if include_products:
            rows += """<TR><TD BORDER="0" BGCOLOR="black" HEIGHT="1" FIXEDSIZE="TRUE" WIDTH="100%"></TD></TR>"""
            rows += f"""<TR><TD ALIGN="CENTER"><FONT POINT-SIZE="10"><B><U>Products</U></B></FONT></TD></TR>"""
            all_products = sorted(set(incoming + outgoing))
            if all_products:
                for p in all_products:
                    wrapped = wrap_text(str(p), width=30)
                    rows += f"""<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="10">{p}</FONT></TD></TR>"""

        label = f"""<
        <TABLE BORDER="1" CELLBORDER="0" CELLPADDING="3" CELLSPACING="0"
               ALIGN="CENTER" BGCOLOR="{color}">
            {rows}
        </TABLE>
        >"""

        dot_obj.node(node, label=label, shape="none", fontsize="16", fontname="Arial")

    def build_graph(include_products=False):
        dot = graphviz.Digraph(format="svg")
        dot.attr(rankdir="LR", fontname="Calibri", ratio="fill")
        added_nodes = set()

        for _, row in unique_edges.iterrows():
            s, c, t = row["Source"], row["Connection"], row["Target"]

            if s not in added_nodes:
                add_node(dot, s, get_color(s), include_products=include_products)
                added_nodes.add(s)

            if t not in added_nodes:
                add_node(dot, t, get_color(t), include_products=include_products)
                added_nodes.add(t)

            dot.edge(s, t, label=c)

        return dot


    if graph_choice == "Detailed Graph":
        st.subheader("Detailed Graph")
        st.graphviz_chart(build_graph(include_products=True), width="stretch")

    elif graph_choice == "Summary Graph":
        st.subheader("Summary Graph")
        st.graphviz_chart(build_graph(include_products=False), width="stretch")


def render_table(df):
    if df.empty:
        return st.info("No data available.")

    df = df.fillna("")

    html_table = df.to_html(index=False, classes="styled-table")

    st.markdown("""
        <style>
        .styled-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            border-radius: 12px;
            overflow: hidden;
            background-color: #1E1E1E;
            color: #E0E0E0;
            font-size: 15px;
        }

        .styled-table th {
            text-align: center !important;
        }

        .styled-table thead {
            background: linear-gradient(90deg, #2A2A2A, #242424);
            color: #FFFFFF !important;
            font-weight: bold;
        }

        .styled-table th, .styled-table td {
            padding: 12px 14px;
            border-bottom: 1px solid #333;
        }

        .styled-table tr:nth-child(even) {
            background-color: #262626;
        }

        .styled-table tr:nth-child(odd) {
            background-color: #1F1F1F;
        }

        .styled-table tr:hover {
            background-color: #333333;
            transition: 0.2s ease-in-out;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(html_table, unsafe_allow_html=True)


if st.session_state.page == "system_info":

    st.sidebar.button("Back to Graph", on_click=go_to_graph)
    st.sidebar.header("Filters")

    st.set_page_config(page_title="System Information", layout="wide")
    st.title("System Information")

    file_path = "Sooraj7.xlsx"
    sheet1 = "Sheet1"
    sheet2 = "Sheet2"
    sheet3 = "Sheet3"

    df_map = pd.read_excel(file_path, sheet_name=sheet1)
    df_desc = pd.read_excel(file_path, sheet_name=sheet2)
    df_product = pd.read_excel(file_path, sheet_name=sheet3)

    df_map.columns = df_map.columns.str.strip().str.lower()

    system_product_pairs = []

    for _, r in df_map.iterrows():
        product = r["product"]

        for sys in [
            r["source system"]
        ]:
            if pd.notna(sys) and pd.notna(product):
                system_product_pairs.append((sys.strip(), product.strip()))



    df_map_clean = pd.DataFrame(system_product_pairs, columns=["System", "Product"])

    all_systems = sorted(df_desc["Source_Code"].dropna().unique().tolist())
    system_options_with_all = ["All"] + all_systems

    selected_systems = st.sidebar.multiselect(
        "System:",
        options=system_options_with_all,
        default=["All"]
    )

    if "All" in selected_systems:
        selected_systems_clean = all_systems
    else:
        selected_systems_clean = selected_systems

    products_for_selected_systems = (
        df_map_clean[df_map_clean["System"].isin(selected_systems_clean)]["Product"]
        .unique()
        .tolist()
    )

    all_products = sorted(products_for_selected_systems)
    product_options_with_all = ["All"] + all_products

    selected_products = st.sidebar.multiselect(
        "Product:",
        options=product_options_with_all,
        default=["All"]
    )

    if "All" in selected_products:
        selected_products_clean = all_products
    else:
        selected_products_clean = selected_products

    df_desc_filtered = df_desc[df_desc["Source_Code"].isin(selected_systems_clean)]
    df_product_filtered = df_product[df_product["Prod_Name"].isin(selected_products_clean)]


    st.subheader("Source Description")

    if df_desc_filtered.empty:
        st.info("No system description found")
    else:
        df_desc_filtered = df_desc_filtered.sort_values(
            by=df_desc_filtered.columns[0],
            key=lambda col: col.str.lower()
        )
        render_table(df_desc_filtered)


    st.subheader("Product Description")

    if df_product_filtered.empty:
        st.info("No products found")
    else:
        df_product_filtered = df_product_filtered.sort_values(
            by=df_product_filtered.columns[0],
            key=lambda col: col.str.lower()
        )
        render_table(df_product_filtered)


#-------------------------------------------------------------------------------------------------------------

# import streamlit as st
# import base64
# import pandas as pd
# import requests
# from io import BytesIO
# import graphviz
# import textwrap
# import warnings

# warnings.filterwarnings("ignore", message="Unverified HTTPS request")

# flow_url = "https://a3c669f6ac2e4e77ad43beab3e15be.e7.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/f5a74c737e714f8eb83902879047a935/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=g5Zyvj8xIGnKizi0lv6XCdTWbaWuahF1krJTBBq35KI"


# try:
#     response = requests.post(flow_url, json={}, verify=False)

#     if response.status_code != 200:
#         st.error(f"❌ Flow failed (HTTP {response.status_code}). It did not return data.")
#         st.stop()

#     content_type = response.headers.get("Content-Type", "").lower()
#     if "text/html" in content_type:
#         st.error("❌ Power Automate returned an HTML error page (Flow crashed upstream).")
#         st.stop()

#     try:
#         parsed_json = response.json()
#         if isinstance(parsed_json, dict) and "error" in parsed_json:
#             st.error(f"❌ Flow Error: {parsed_json['error']}")
#             st.stop()
#     except:
#         pass

#     if len(response.content) == 0:
#         st.error("❌ Flow returned empty content. Flow likely failed internally.")
#         st.stop()

#     excel_bytes = None

#     if "application/json" in content_type:
#         json_body = response.json()

#         for key in ["file", "fileContent", "body", "content"]:
#             if key in json_body:
#                 excel_bytes = base64.b64decode(json_body[key])
#                 break

#         if excel_bytes is None:
#             st.error("❌ No Excel file content found in JSON response.")
#             st.stop()

#     else:
#         excel_bytes = response.content

   
#     excel_data = BytesIO(excel_bytes)
#     df = pd.read_excel(excel_data, sheet_name="LineageFile")
#     df_desc = pd.read_excel(excel_data, sheet_name="Source Master")

#     st.success(f"✅ Loaded {len(df)} rows from SharePoint Excel")

# except Exception as e:
#     err = str(e).lower()
#     if "403" in err or "forbidden" in err or "unauthorized" in err:
#         st.error("❌ You do not have permission to access the SharePoint file.")
#     else:
#         st.error(f"❌ Failed to load Excel: {e}")
#     st.stop()


# st.info("Fetching Excel from SharePoint via Power Automate...")

# with st.expander("🔍 Preview Data"):
#     st.write("**Lineage File:**")
#     st.dataframe(df)
#     st.write("**Source Master:**")
#     st.dataframe(df_desc)

# df.columns = df.columns.str.strip().str.lower()
# df.rename(
#     columns={
#         "product": "Product",
#         "source system": "Source",
#         "connection": "Connection",
#         "target system": "Target",
#         "upstream system": "Upstream",
#         "downstream system": "Downstream",
#     },
#     inplace=True,
# )

# st.sidebar.header("🎛️ Filters")

# show_with_products = st.sidebar.checkbox("Summary Graph", value=False)
# show_without_products = st.sidebar.checkbox("Detailed Graph", value=True)

# upstream_options = ["All"] + sorted(df["Upstream"].dropna().unique().tolist())
# product_options = ["All"] + sorted(df["Product"].dropna().unique().tolist())
# target_options = ["All"] + sorted(df["Target"].dropna().unique().tolist())

# upstream_filter = st.sidebar.selectbox("Upstream System:", upstream_options)
# product_filter = st.sidebar.selectbox("Product:", product_options)
# target_filter = st.sidebar.selectbox("Target System:", target_options)

# filtered_df = df.copy()

# if upstream_filter != "All":
#     filtered_df = filtered_df[filtered_df["Upstream"] == upstream_filter]
# if product_filter != "All":
#     filtered_df = filtered_df[filtered_df["Product"] == product_filter]
# if target_filter != "All":
#     filtered_df = filtered_df[filtered_df["Target"] == target_filter]

# filtered_upstreams = ["All"] + sorted(filtered_df["Upstream"].dropna().unique().tolist())
# filtered_products = ["All"] + sorted(filtered_df["Product"].dropna().unique().tolist())
# filtered_targets = ["All"] + sorted(filtered_df["Target"].dropna().unique().tolist())

# with st.sidebar.expander("🧠 Available Options (after filtering)"):
#     st.write("Upstream:", filtered_upstreams)
#     st.write("Product:", filtered_products)
#     st.write("Target:", filtered_targets)

# if not show_with_products and not show_without_products:
#     st.sidebar.warning("⚠️ Please select at least one graph type to display.")
#     st.stop()

# unique_edges = filtered_df[["Source", "Connection", "Target"]].drop_duplicates()

# products_by_pair = (
#     filtered_df.groupby(["Source", "Target"])["Product"]
#     .apply(lambda x: sorted(set(x.dropna())))
#     .to_dict()
# )

# sources = set(unique_edges["Source"])
# targets = set(unique_edges["Target"])
# upstream_nodes = sources - targets
# downstream_nodes = targets - sources

# def get_color(node):
#     if node in upstream_nodes:
#         return "#6DB4ED"
#     elif node in downstream_nodes:
#         return "#4CAF50"
#     else:
#         return "#FFC107"

# def wrap_text(text, width=30):
#     return "<BR/>".join(textwrap.wrap(text, width=width))

# def add_node(dot_obj, node, color, include_products=False):
#     if not node or str(node).strip() == "":
#         return

#     node = str(node).strip()

#     incoming, outgoing = [], []
#     for (src, tgt), plist in products_by_pair.items():
#         if str(tgt).strip() == node:
#             incoming.extend(plist)
#         if str(src).strip() == node:
#             outgoing.extend(plist)

#     incoming, outgoing = sorted(set(incoming)), sorted(set(outgoing))

#     source_row = df_desc[df_desc["Source_Code"].astype(str).str.strip() == node]
#     system_name = source_row["Source_System"].iloc[0] if not source_row.empty else ""
#     desc = source_row["Source_Desc"].iloc[0] if not source_row.empty else ""

#     header_lines = f"""
#     <TABLE BORDER="0" CELLBORDER="0" CELLPADDING="1" CELLSPACING="0">
#         <TR><TD ALIGN="CENTER"><B><FONT POINT-SIZE='10'>{node.upper()}</FONT></B></TD></TR>
#         <TR><TD ALIGN="CENTER"><FONT POINT-SIZE='10'>{system_name}</FONT></TD></TR>
#         <TR><TD ALIGN="CENTER"><FONT POINT-SIZE='10'>{desc}</FONT></TD></TR>
#     </TABLE>
#     """

#     rows = f"<TR><TD ALIGN='CENTER'>{header_lines}</TD></TR>"

#     if include_products:
#         rows += """<TR><TD BGCOLOR="black" HEIGHT="1" WIDTH="100%"></TD></TR>"""
#         rows += """<TR><TD ALIGN="CENTER"><FONT POINT-SIZE="10"><B><U>Products:</U></B></FONT></TD></TR>"""
#         all_products = sorted(set(incoming + outgoing))
#         for p in all_products:
#             rows += f"<TR><TD ALIGN='CENTER'><FONT POINT-SIZE='10'>{wrap_text(str(p), 30)}</FONT></TD></TR>"""

#     label = f"""<
#     <TABLE BORDER="1" CELLBORDER="0" CELLPADDING="3" CELLSPACING="0" ALIGN="CENTER" BGCOLOR="{color}">
#         {rows}
#     </TABLE>
#     >"""

#     dot_obj.node(node, label=label, shape="none", fontsize="16", fontname="Arial")

# def build_graph(include_products=False):
#     dot = graphviz.Digraph(format="svg")
#     dot.attr(rankdir="LR", fontname="Calibri")
#     added_nodes = set()

#     for _, row in unique_edges.iterrows():
#         s, c, t = str(row["Source"]).strip(), str(row["Connection"]).strip(), str(row["Target"]).strip()
#         if not s or not t:
#             continue

#         if s not in added_nodes:
#             add_node(dot, s, get_color(s), include_products)
#             added_nodes.add(s)
#         if t not in added_nodes:
#             add_node(dot, t, get_color(t), include_products)
#             added_nodes.add(t)

#         dot.edge(s, t, label=str(c))

#     return dot

# if show_without_products:
#     st.subheader("📘 Detailed Graph")
#     st.graphviz_chart(build_graph(include_products=False), use_container_width=True)

# if show_with_products:
#     st.subheader("📗 Summary Graph")
#     st.graphviz_chart(build_graph(include_products=True), use_container_width=True)


# #--------------------------------------------------------------------------------------
# import streamlit as st
# import base64
# import pandas as pd
# import requests
# from io import BytesIO
# import graphviz
# import textwrap
# import warnings

# warnings.filterwarnings("ignore", message="Unverified HTTPS request")

# # 🚨 Your Flow URL
# flow_url = "https://a3c669f6ac2e4e77ad43beab3e15be.e7.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/f5a74c737e714f8eb83902879047a935/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=g5Zyvj8xIGnKizi0lv6XCdTWbaWuahF1krJTBBq35KI"

# st.title("📊 Data Lineage Dashboard")
# st.info("Verifying SharePoint permissions...")

# # ============================================
# # 🚨 CALL POWER AUTOMATE FLOW
# # ============================================
# try:
#     response = requests.post(flow_url, json={}, verify=False, allow_redirects=False)

#     # -------------------------------
#     # 🔒 CASE 1 — Redirect to login
#     # -------------------------------
#     if response.status_code in [301, 302, 307, 308]:
#         st.error("❌ Access denied: You do not have permission to access the SharePoint file.")
#         st.stop()

#     # -------------------------------
#     # 🔒 CASE 2 — User not authorized
#     # -------------------------------
#     if response.status_code in [401, 403]:
#         st.error("❌ Access denied: Your account does not have access to the SharePoint file.")
#         st.stop()

#     # -------------------------------
#     # 🔒 CASE 3 — HTML returned (login page)
#     # -------------------------------
#     content_type = response.headers.get("Content-Type", "")
#     if "text/html" in content_type:
#         st.error("❌ Access denied: Unable to authenticate to SharePoint.")
#         st.stop()

#     # -------------------------------
#     # 🟢 CASE 4 — OK, extract Excel file
#     # -------------------------------
#     response.raise_for_status()

#     if "application/json" in content_type:
#         file_json = response.json()
#         excel_bytes = None
#         for key in ["file", "fileContent", "body", "content"]:
#             if key in file_json:
#                 excel_bytes = base64.b64decode(file_json[key])
#                 break
#         if excel_bytes is None:
#             raise ValueError("Excel file content not found in Flow response.")
#     else:
#         excel_bytes = response.content

#     excel_data = BytesIO(excel_bytes)

#     df = pd.read_excel(excel_data, sheet_name="LineageFile")
#     df_desc = pd.read_excel(excel_data, sheet_name="Source Master")

#     st.success(f"✅ SharePoint access verified — Loaded {len(df)} rows")

# except Exception as e:
#     st.error(f"❌ Could not load data: {e}")
#     st.stop()


# # ====================================================
# # 🔍 PREVIEW DATA
# # ====================================================
# with st.expander("🔍 Preview Data"):
#     st.write("**Lineage File:**")
#     st.dataframe(df)
#     st.write("**Source Master:**")
#     st.dataframe(df_desc)


# # ====================================================
# # 🧹 CLEAN COLUMNS
# # ====================================================
# df.columns = df.columns.str.strip().str.lower()

# df.rename(
#     columns={
#         "product": "Product",
#         "source system": "Source",
#         "connection": "Connection",
#         "target system": "Target",
#         "upstream system": "Upstream",
#         "downstream system": "Downstream",
#     },
#     inplace=True,
# )

# # ====================================================
# # 🎛️ FILTERS
# # ====================================================
# st.sidebar.header("🎛️ Filters")

# show_with_products = st.sidebar.checkbox("Summary Graph", value=False)
# show_without_products = st.sidebar.checkbox("Detailed Graph", value=True)

# upstream_options = ["All"] + sorted(df["Upstream"].dropna().unique().tolist())
# product_options = ["All"] + sorted(df["Product"].dropna().unique().tolist())
# target_options = ["All"] + sorted(df["Target"].dropna().unique().tolist())

# upstream_filter = st.sidebar.selectbox("Upstream System:", upstream_options)
# product_filter = st.sidebar.selectbox("Product:", product_options)
# target_filter = st.sidebar.selectbox("Target System:", target_options)


# # ====================================================
# # 🔎 APPLY FILTERS
# # ====================================================
# filtered_df = df.copy()

# if upstream_filter != "All":
#     filtered_df = filtered_df[filtered_df["Upstream"] == upstream_filter]
# if product_filter != "All":
#     filtered_df = filtered_df[filtered_df["Product"] == product_filter]
# if target_filter != "All":
#     filtered_df = filtered_df[filtered_df["Target"] == target_filter]


# # ====================================================
# # 🧠 FOR CHECKBOX PREVIEW
# # ====================================================
# filtered_upstreams = ["All"] + sorted(filtered_df["Upstream"].dropna().unique())
# filtered_products = ["All"] + sorted(filtered_df["Product"].dropna().unique())
# filtered_targets = ["All"] + sorted(filtered_df["Target"].dropna().unique())

# with st.sidebar.expander("🧠 Available Options"):
#     st.write("Upstream:", filtered_upstreams)
#     st.write("Product:", filtered_products)
#     st.write("Target:", filtered_targets)


# if not show_with_products and not show_without_products:
#     st.sidebar.warning("⚠️ Select at least one graph.")
#     st.stop()


# # ====================================================
# # 🔗 GRAPH DATA
# # ====================================================
# unique_edges = filtered_df[["Source", "Connection", "Target"]].drop_duplicates()

# products_by_pair = (
#     filtered_df.groupby(["Source", "Target"])["Product"]
#     .apply(lambda x: sorted(set(x.dropna())))
#     .to_dict()
# )

# sources = set(unique_edges["Source"])
# targets = set(unique_edges["Target"])

# upstream_nodes = sources - targets
# downstream_nodes = targets - sources


# # ====================================================
# # 🎨 GRAPH HELPERS
# # ====================================================
# def get_color(node):
#     if node in upstream_nodes:
#         return "#6DB4ED"
#     elif node in downstream_nodes:
#         return "#4CAF50"
#     else:
#         return "#FFC107"


# def wrap_text(text, width=30):
#     return "<BR/>".join(textwrap.wrap(text, width))


# def add_node(dot_obj, node, color, include_products=False):

#     node = str(node).strip()
#     if not node:
#         return

#     incoming, outgoing = [], []
#     for (src, tgt), plist in products_by_pair.items():
#         if tgt == node:
#             incoming.extend(plist)
#         if src == node:
#             outgoing.extend(plist)

#     incoming = sorted(set(incoming))
#     outgoing = sorted(set(outgoing))

#     src_row = df_desc[df_desc["Source_Code"].astype(str).str.strip() == node]
#     system_name = src_row["Source_System"].iloc[0] if not src_row.empty else ""
#     desc = src_row["Source_Desc"].iloc[0] if not src_row.empty else ""

#     table_header = f"""
#     <TABLE BORDER="0" CELLBORDER="0">
#         <TR><TD ALIGN="CENTER"><B>{node.upper()}</B></TD></TR>
#         <TR><TD ALIGN="CENTER">{system_name}</TD></TR>
#         <TR><TD ALIGN="CENTER">{desc}</TD></TR>
#     </TABLE>
#     """

#     rows = f"<TR><TD>{table_header}</TD></TR>"

#     if include_products:
#         rows += "<TR><TD BGCOLOR='black' HEIGHT='1'></TD></TR>"
#         rows += "<TR><TD ALIGN='CENTER'><B><U>Products</U></B></TD></TR>"

#         for p in sorted(set(incoming + outgoing)):
#             rows += f"<TR><TD ALIGN='CENTER'>{wrap_text(str(p))}</TD></TR>"

#     label = f"""<
#     <TABLE BORDER="1" BGCOLOR="{color}">
#         {rows}
#     </TABLE>
#     >"""

#     dot_obj.node(node, label=label, shape="none")


# def build_graph(include_products=False):
#     dot = graphviz.Digraph(format="svg")
#     dot.attr(rankdir="LR")

#     added_nodes = set()

#     for _, row in unique_edges.iterrows():
#         s = str(row["Source"]).strip()
#         c = str(row["Connection"]).strip()
#         t = str(row["Target"]).strip()

#         if s and s not in added_nodes:
#             add_node(dot, s, get_color(s), include_products)
#             added_nodes.add(s)

#         if t and t not in added_nodes:
#             add_node(dot, t, get_color(t), include_products)
#             added_nodes.add(t)

#         dot.edge(s, t, label=c)

#     return dot


# # ====================================================
# # 📊 DISPLAY GRAPHS
# # ====================================================
# if show_without_products:
#     st.subheader("📘 Detailed Graph")
#     st.graphviz_chart(build_graph(include_products=False), use_container_width=True)

# if show_with_products:
#     st.subheader("📗 Summary Graph")
#     st.graphviz_chart(build_graph(include_products=True), use_container_width=True)



#----------------------------------------------------------
