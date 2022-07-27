import json
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
from requests.exceptions import RequestException

st.set_page_config(page_title="Emoji Kitchen", page_icon="‍:stew:", layout="wide")

st.title(":stew: ‍Emoji Kitchen")


# Add css to make button text larger
st.markdown(
    """
<style>
button {
    font-size: 3.5rem;
    border: none !important;
}
</style>
""",
    unsafe_allow_html=True,
)


def emoji_url(code_point) -> str:
    return f"https://raw.githubusercontent.com/googlefonts/noto-emoji/main/png/128/emoji_u${code_point}.png"


def code_point_to_emoji(code_point) -> str:
    cps = [int(hex, 16) for hex in code_point.split("-")]
    emoji = "".join(chr(cp) for cp in cps)
    return emoji


@st.experimental_singleton
def get_matches() -> pd.DataFrame:
    return pd.read_parquet("matches.parquet")


def mixmoji_url(code_point1: str, code_point2: str) -> str:
    # date = "20201001"
    matches = get_matches()

    try:
        match = matches[
            ((matches["emoji1"] == code_point1) & (matches["emoji2"] == code_point2))
            | ((matches["emoji1"] == code_point2) & (matches["emoji2"] == code_point1))
        ].iloc[0]
    except IndexError:
        return "NO MATCH"

    date = match["date"]
    code_point1 = match["emoji1"]
    code_point2 = match["emoji2"]

    code_point1 = "-u".join(code_point1.split("-"))
    code_point2 = "-u".join(code_point2.split("-"))

    return f"https://www.gstatic.com/android/keyboard/emojikitchen/{date}/u{code_point1}/u{code_point1}_u{code_point2}.png"


# Load dictionary from points.json
points = json.loads(Path("points.json").read_text())

if "clicked" not in st.session_state:
    st.session_state["clicked"] = []

clicked = st.session_state["clicked"]

if not clicked:
    first = "?"
    second = "?"
    third = "?"

elif len(clicked) == 1:
    first = code_point_to_emoji(clicked[0])
    second = "?"
    third = "?"

elif len(clicked) == 2:
    combo_url = mixmoji_url(clicked[0], clicked[1])
    first = code_point_to_emoji(clicked[0])
    second = code_point_to_emoji(clicked[1])
    third = combo_url

_, col1, col2, col3, col4, col5, _ = st.columns([7, 1, 1, 1, 1, 1, 7])

col1.write(f"# {first}")
col2.write(f"# +")
col3.write(f"# {second}")
col4.write("# =")
if third == "?":
    col5.write(f"# {third}")
else:
    try:
        requests.head(third).raise_for_status()
        col5.image(third, use_column_width=True)
    except RequestException:
        col5.write(f"## Not found")


N_COLS = 20

columns = st.columns(N_COLS)


for idx, point in enumerate(points):
    emoji = code_point_to_emoji(point)
    col = columns[idx % N_COLS]
    with col:
        if st.button(emoji):
            st.session_state["clicked"].append(point)
            if len(st.session_state["clicked"]) > 2:
                st.session_state["clicked"].pop(0)
            st.experimental_rerun()

# st.write(st.session_state["clicked"])
