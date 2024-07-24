import json
import random
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
from requests.exceptions import RequestException

st.set_page_config(page_title="Emoji Kitchen", page_icon=":stew:", layout="wide")

st.title(":stew: Emoji Kitchen")


st.markdown(
    """
<style>
[data-testid="stVerticalBlock"]:has(.emoji-grid) button p {
    font-size: 3.5rem;
    border: none !important;
}

[data-testid="stVerticalBlock"]:has(.emoji-grid) {
    display: inline-block !important;
}

[data-testid="stVerticalBlock"]:has(.emoji-grid) .element-container {
    display: inline-block !important;
    width: 80px;
}

[data-testid="stVerticalBlock"]:has(.emoji-grid) .stButton {
    width: 0 !important;
}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data
def emoji_url(code_point) -> str:
    return f"https://raw.githubusercontent.com/googlefonts/noto-emoji/main/png/128/emoji_u${code_point}.png"


def code_point_to_emoji(code_point) -> str:
    cps = [int(hex, 16) for hex in code_point.split("-")]
    emoji = "".join(chr(cp) for cp in cps)
    return emoji


@st.cache_resource
def get_matches() -> pd.DataFrame:
    return pd.read_parquet("matches.parquet")


@st.cache_data
def get_other_matches(code_point1: str) -> list[str]:
    matches = get_matches()
    return (
        matches[matches["emoji1"] == code_point1]["emoji2"].tolist()
        + matches[matches["emoji2"] == code_point1]["emoji1"].tolist()
    )


@st.cache_data
def mixmoji_url(code_point1: str, code_point2: str) -> str:
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
    st.session_state["clicked"] = st.query_params.get_all("clicked")

clicked = st.session_state["clicked"]

if not clicked:
    first = "?"
    second = "?"
    third = "❌"

elif len(clicked) == 1:
    first = code_point_to_emoji(clicked[0])
    second = "?"
    third = "❌"

elif len(clicked) == 2:
    combo_url = mixmoji_url(clicked[0], clicked[1])
    first = code_point_to_emoji(clicked[0])
    second = code_point_to_emoji(clicked[1])
    third = combo_url

else:
    raise ValueError("Too many clicks")

_, clear_col, col1, col2, col3, col4, col5, random_col, _ = st.columns(
    [4, 1, 1, 1, 1, 1, 1, 1, 4]
)


def clear_clicked():
    st.session_state["clicked"] = []
    st.query_params.update({"clicked": []})


clear_col.button("# 🗑️", on_click=clear_clicked)

col1.write(f"# {first}")
col2.write("# +")
col3.write(f"# {second}")
col4.write("# =")


def pick_random_emoji():
    point_1 = random.choice(points)
    point_2 = random.choice(get_other_matches(point_1))
    st.session_state["clicked"] = [point_1, point_2]
    st.query_params.update({"clicked": st.session_state["clicked"]})


random_col.button("# 🎲", on_click=pick_random_emoji)


@st.cache_data
def img_exists(url):
    if url == "NO MATCH":
        return False
    try:
        requests.head(url).raise_for_status()
        return True
    except RequestException:
        return False


if third == "?":
    col5.write(f"# {third}")
else:
    if img_exists(third):
        col5.image(third, width=70)
    else:
        col5.write("## ❌")


def button_clicked(point):
    st.session_state["clicked"].insert(0, point)
    if len(st.session_state["clicked"]) > 2:
        st.session_state["clicked"].pop(2)

    st.query_params.update({"clicked": st.session_state["clicked"]})


def draw_emoji_grid():
    try:
        point_1 = st.session_state["clicked"][0]
        other_matches = get_other_matches(point_1)
    except IndexError:
        point_1 = None
        other_matches = []

    with st.container(height=800):
        st.html("<span class='emoji-grid'></span>")
        for point in points:
            emoji = code_point_to_emoji(point)
            st.button(
                emoji,
                on_click=button_clicked,
                args=(point,),
                disabled=point not in other_matches and point_1 is not None,
            )


draw_emoji_grid()
