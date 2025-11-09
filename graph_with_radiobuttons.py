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

    st.set_page_config(page_title="Data Flow Graph", layout="wide")
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

