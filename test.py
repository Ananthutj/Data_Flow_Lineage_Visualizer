import streamlit as st
import base64

st.set_page_config(page_title="Secure Streamlit Portal", layout="centered")
st.title("🔐 Secure Streamlit Portal")

params = st.query_params
encoded_data = params.get("data", [""])[0]

if not encoded_data:
    st.error("Invalid access. Please open this app through Power Apps.")
    st.stop()

try:
    decoded_email = base64.b64decode(encoded_data).decode("utf-8")
except Exception:
    st.error("Invalid or corrupted link.")
    st.stop()

# Session state for login
if "verified" not in st.session_state:
    st.session_state.verified = False

# If NOT verified → show login screen
if not st.session_state.verified:

    st.write("Please verify your email to continue:")
    user_email = st.text_input("Enter your company email:")

    if st.button("Verify"):
        if not user_email:
            st.warning("Please enter your email.")
        elif user_email.strip().lower() == decoded_email.strip().lower():
            st.session_state.verified = True
            st.session_state.user_email = user_email
            st.experimental_rerun()
        else:
            st.error("Email does not match. Access denied.")

# If STILL not verified → STOP ENTIRE APP
if not st.session_state.verified:
    st.stop()

# ------------------------------------------------------
# STEP 2 — SHOW YOUR DATA-FLOW GRAPH ONLY AFTER LOGIN
# ------------------------------------------------------

st.success(f"Access granted! Welcome, {st.session_state.user_email}")

# ---- FROM HERE, YOUR ORIGINAL STEP 2 CODE GOES BELOW ----

import pandas as pd
import requests
from io import BytesIO
import graphviz
import textwrap
import warnings

st.set_page_config(page_title="Data Flow Graph", layout="wide")
st.title("L-R Directed Data Flow")

warnings.filterwarnings("ignore", message="Unverified HTTPS request")

flow_url = "https://a3c669f6ac2e4e77ad43beab3e15be.e7.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/7a9b274a8f51431298fa337db36263a7/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=78Ck9Lh3DrNmJsOwSybAbDojXj_kra1LXiAxcet6MeI"



st.info("Fetching Excel from SharePoint via Power Automate...")

try:
    response = requests.post(flow_url, json={}, verify=False)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")
    excel_bytes = None

    if "application/json" in content_type:
        file_json = response.json()
        for key in ["file", "fileContent", "body", "content"]:
            if key in file_json:
                excel_bytes = base64.b64decode(file_json[key])
                break
        if excel_bytes is None:
            raise ValueError("No base64 Excel content found in JSON response")
    else:
        excel_bytes = response.content

    excel_data = BytesIO(excel_bytes)
    df = pd.read_excel(excel_data, sheet_name="LineageFile")
    df_desc = pd.read_excel(excel_data, sheet_name="Source Master")

    df = df.fillna("")
    df_desc = df_desc.fillna("")

    st.success(f"✅ Loaded {len(df)} rows from SharePoint Excel")

except Exception as e:
    st.error(f"❌ Failed to load Excel: {e}")
    st.stop()

with st.expander("🔍 Preview Data"):
    st.write("**Lineage File:**")
    st.dataframe(df)
    st.write("**Source Master:**")
    st.dataframe(df_desc)

df.columns = df.columns.str.strip().str.lower()
df.rename(
    columns={
        "product": "Product",
        "source system": "Source",
        "connection": "Connection",
        "target system": "Target",
        "upstream system": "Upstream",
        "downstream system": "Downstream",
    },
    inplace=True,
)

st.sidebar.header("🎛️ Filters")

show_with_products = st.sidebar.checkbox("Summary Graph", value=False)
show_without_products = st.sidebar.checkbox("Detailed Graph", value=True)

upstream_options = ["All"] + sorted(df["Upstream"].dropna().unique().tolist())
product_options = ["All"] + sorted(df["Product"].dropna().unique().tolist())
target_options = ["All"] + sorted(df["Target"].dropna().unique().tolist())

upstream_filter = st.sidebar.selectbox("Upstream System:", upstream_options)
product_filter = st.sidebar.selectbox("Product:", product_options)
target_filter = st.sidebar.selectbox("Target System:", target_options)

filtered_df = df.copy()

if upstream_filter != "All":
    filtered_df = filtered_df[filtered_df["Upstream"] == upstream_filter]
if product_filter != "All":
    filtered_df = filtered_df[filtered_df["Product"] == product_filter]
if target_filter != "All":
    filtered_df = filtered_df[filtered_df["Target"] == target_filter]

filtered_upstreams = ["All"] + sorted(filtered_df["Upstream"].dropna().unique().tolist())
filtered_products = ["All"] + sorted(filtered_df["Product"].dropna().unique().tolist())
filtered_targets = ["All"] + sorted(filtered_df["Target"].dropna().unique().tolist())

with st.sidebar.expander("🧠 Available Options (after filtering)"):
    st.write("Upstream:", filtered_upstreams)
    st.write("Product:", filtered_products)
    st.write("Target:", filtered_targets)

if not show_with_products and not show_without_products:
    st.sidebar.warning("⚠️ Please select at least one graph type to display.")
    st.stop()

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
    import textwrap
    return "<BR/>".join(textwrap.wrap(text, width=width))

def add_node(dot_obj, node, color, include_products=False):
    if not node or str(node).strip() == "":
        return

    node = str(node).strip()

    incoming, outgoing = [], []
    for (src, tgt), plist in products_by_pair.items():
        if str(tgt).strip() == node:
            incoming.extend(plist)
        if str(src).strip() == node:
            outgoing.extend(plist)

    incoming, outgoing = sorted(set(incoming)), sorted(set(outgoing))

    source_row = df_desc[df_desc["Source_Code"].astype(str).str.strip() == node]
    system_name = source_row["Source_System"].iloc[0] if not source_row.empty else ""
    desc = source_row["Source_Desc"].iloc[0] if not source_row.empty else ""

    header_lines = f"""
    <TABLE BORDER="0" CELLBORDER="0" CELLPADDING="1" CELLSPACING="0">
        <TR><TD ALIGN="CENTER"><B><FONT POINT-SIZE='10'>{node.upper()}</FONT></B></TD></TR>
        <TR><TD ALIGN="CENTER"><FONT POINT-SIZE='10'>{system_name}</FONT></TD></TR>
        <TR><TD ALIGN="CENTER"><FONT POINT-SIZE='10'>{desc}</FONT></TD></TR>
    </TABLE>
    """

    rows = f"<TR><TD ALIGN='CENTER'>{header_lines}</TD></TR>"

    if include_products:
        rows += """<TR><TD BGCOLOR="black" HEIGHT="1" WIDTH="100%"></TD></TR>"""
        rows += """<TR><TD ALIGN="CENTER"><FONT POINT-SIZE="10"><B><U>Products:</U></B></FONT></TD></TR>"""
        all_products = sorted(set(incoming + outgoing))
        for p in all_products:
            rows += f"<TR><TD ALIGN='CENTER'><FONT POINT-SIZE='10'>{wrap_text(str(p), 30)}</FONT></TD></TR>"""

    label = f"""<
    <TABLE BORDER="1" CELLBORDER="0" CELLPADDING="3" CELLSPACING="0" ALIGN="CENTER" BGCOLOR="{color}">
        {rows}
    </TABLE>
    >"""

    import graphviz
    dot_obj.node(node, label=label, shape="none", fontsize="16", fontname="Arial")

def build_graph(include_products=False):
    import graphviz
    dot = graphviz.Digraph(format="svg")
    dot.attr(rankdir="LR", fontname="Calibri")
    added_nodes = set()

    for _, row in unique_edges.iterrows():
        s, c, t = str(row["Source"]).strip(), str(row["Connection"]).strip(), str(row["Target"]).strip()
        if not s or not t:
            continue

        if s not in added_nodes:
            add_node(dot, s, get_color(s), include_products)
            added_nodes.add(s)
        if t not in added_nodes:
            add_node(dot, t, get_color(t), include_products)
            added_nodes.add(t)

        dot.edge(s, t, label=str(c))

    return dot

if show_without_products:
    st.subheader("📘 Detailed Graph")
    st.graphviz_chart(build_graph(include_products=False), use_container_width=True)

if show_with_products:
    st.subheader("📗 Summary Graph")
    st.graphviz_chart(build_graph(include_products=True), use_container_width=True)
