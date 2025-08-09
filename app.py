import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from run_assistant import run_pipeline 
from pathlib import Path

for p in ["data/raw", "data/cleaned", "logs"]:
    Path(p).mkdir(parents=True, exist_ok=True)


st.title("AI-Powered Data Cleaning Assistant")

# Download sample dataset
with open("data/raw/sample_messy_alt.csv", "rb") as f:
    st.download_button(
        label="Download Sample Dataset",
        data=f,
        file_name="sample_messy.csv",
        mime="text/csv"
    )

uploaded_file = st.file_uploader("Upload your messy CSV", type=["csv"])

if uploaded_file:
    # Save uploaded file
    with open("data/raw/user_upload.csv", "wb") as f:
        f.write(uploaded_file.read())

    # Run cleaning
    run_pipeline("data/raw/user_upload.csv")

    # Load comparison CSV
    df = pd.read_csv("data/cleaned/tableau_comparison.csv")

    # ---------- Pretty Before/After table + visuals ----------

    st.subheader("Before vs After Preview")

    # Split by source
    before = df[df["Source"].str.lower() == "before"].copy()
    after  = df[df["Source"].str.lower() == "after"].copy()

    # Ensure RowID exists and is int for a stable join
    if "RowID" not in before.columns:
        if "Row ID" in before.columns:  # Tableau sometimes renames it
            before = before.rename(columns={"Row ID": "RowID"})
            after  = after.rename(columns={"Row ID": "RowID"})

    before["RowID"] = before["RowID"].astype(int)
    after["RowID"]  = after["RowID"].astype(int)

    # Build a side-by-side table (interleaving columns: name_before, name_after, age_before, age_after, ...)
    join_cols = [c for c in before.columns if c not in ("Source", "RowID")]
    wide = before[["RowID"] + join_cols].merge(
        after[["RowID"] + join_cols],
        on="RowID", how="outer", suffixes=("_Before", "_After")
    ).sort_values("RowID")

    # Nice column order: RowID first, then each field's Before/After pair
    ordered = ["RowID"]
    for c in join_cols:
        ordered += [f"{c}_Before", f"{c}_After"]
    wide = wide[ordered]

    # Styler to highlight cells that changed
    def highlight_changes(s):
        # s is a Series (column). We only style *_After vs its *_Before sister.
        if not s.name.endswith("_After"):
            return [""] * len(s)
        base = s.name[:-6]  # strip "_After"
        before_col = f"{base}_Before"
        if before_col in s.index:  # (Styler applies per-column; we compare row-wise later)
            pass
        # Build a mask by comparing this After column to the matching Before column row-wise.
        diffs = s.values != wide[before_col].values
        # Treat NaN vs NaN as same
        import numpy as np
        both_nan = np.isnan(s.values) & np.isnan(wide[before_col].values) if s.dtype.kind in "f" else (pd.isna(s.values) & pd.isna(wide[before_col].values))
        diffs = diffs & ~both_nan
        return ["background-color: #2b9348; color: white" if x else "" for x in diffs]

    styled = wide.style.apply(highlight_changes, axis=0).set_properties(
        **{"border-color": "#333", "border-width": "1px", "border-style": "solid"}
    )

    st.dataframe(styled, use_container_width=True)

    # ---------- Topline metrics ----------
    rows_before = len(before)
    rows_after  = len(after)
    st.markdown("### Topline")
    m1, m2, m3 = st.columns(3)
    m1.metric("Rows (Before)", rows_before)
    m2.metric("Rows (After)", rows_after, delta=rows_after - rows_before)
    m3.metric("Duplicates Removed", max(0, rows_before - rows_after))

    # ---------- Missing values by column (Before vs After) ----------
    st.markdown("### 🕳️ Missing Values by Column")
    def null_counts(frame):
        return frame.drop(columns=["Source","RowID"], errors="ignore").isna().sum()

    miss_before = null_counts(before).rename("Before")
    miss_after  = null_counts(after).rename("After")
    miss = pd.concat([miss_before, miss_after], axis=1).fillna(0).astype(int)
    st.bar_chart(miss)

    # ---------- Numeric distributions (Before vs After) ----------
    st.markdown("### Numeric Distributions (Before vs After)")
    numeric_cols = []
    for c in join_cols:
        # detect numeric by trying to coerce
        b_num = pd.to_numeric(before[c], errors="coerce")
        a_num = pd.to_numeric(after[c], errors="coerce")
        if b_num.notna().sum() + a_num.notna().sum() > 0:
            numeric_cols.append(c)

    if numeric_cols:
        pick = st.selectbox("Choose a numeric column to compare:", numeric_cols, index=0)
        b_series = pd.to_numeric(before[pick], errors="coerce")
        a_series = pd.to_numeric(after[pick], errors="coerce")
        comp = pd.DataFrame({"Before": b_series, "After": a_series})
        st.line_chart(comp)  # simple overlay line; for many rows, consider st.area_chart or Altair histogram
    else:
        st.info("No numeric columns detected to chart.")

    # ---------- Age comparison (kept, case-insensitive) ----------
    age_col = None
    for candidate in ["Age", "age"]:
        if candidate in df.columns:
            age_col = candidate
            break
    if age_col is None and "age" in join_cols:
        age_col = "age"
    elif age_col is None and "Age" in join_cols:
        age_col = "Age"

    if age_col:
        st.markdown("### Age Comparison (line)")
        age_wide = wide[["RowID", f"{age_col}_Before", f"{age_col}_After"]].set_index("RowID").rename(
            columns={f"{age_col}_Before": "Before", f"{age_col}_After": "After"}
        )
        st.line_chart(age_wide)

st.title("📊 Example Dashboard - AI Data Cleaning Comparison")
st.markdown(
    "Below is a Tableau dashboard built from another sample dataset. "
    "When you upload your own CSV, your data will be cleaned and shown similarly!"
)

TABLEAU_URL = (
    "https://public.tableau.com/views/Book5_17546910925600/Sheet1"
    "?:showVizHome=no&:embed=y&:toolbar=top&:tabs=no&:device=desktop"
)

components.html(
    f"""
    <div style="display:flex; justify-content:center; margin: 0.5rem 0 2rem;">
      <iframe
        src="{TABLEAU_URL}"
        style="
          width: 900px;
          height: 900px;
          border: 0;
          border-radius: 12px;
          box-shadow: 0 6px 24px rgba(0,0,0,.15);
          background: white;"
        allowfullscreen
      ></iframe>
    </div>
    """,
    height=930,
    width = 900,
)

