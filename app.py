import streamlit as st
import numpy as np
from scipy.special import expit
from datetime import date

st.set_page_config(
    page_title="Renginio lankomumo prognozė",
    layout="centered"
)

st.title("Renginio lankomumo prognozė")
st.write(
    "Įveskite renginio duomenis ir gaukite prognozuojamą "
    "galutinį užpildymą bei lankytojų skaičių."
)

st.divider()

st.subheader("Renginio datos")

bilietu_paleidimo_data = st.date_input(
    "Bilietų prekybos pradžios data",
    value=date.today()
)

renginio_data = st.date_input(
    "Renginio data",
    value=date.today()
)

siandien = date.today()

if renginio_data < bilietu_paleidimo_data:
    st.error(
        "Renginio data negali būti ankstesnė už "
        "bilietų prekybos pradžios datą."
    )
    st.stop()

dienos_iki_renginio = max(
    (renginio_data - siandien).days,
    0
)

prekybos_dienos = (
    renginio_data - bilietu_paleidimo_data
).days

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Iki renginio liko",
        f"{dienos_iki_renginio} d."
    )

with col2:
    st.metric(
        "Bilietų prekybos laikotarpis",
        f"{prekybos_dienos} d."
    )

st.divider()

st.subheader("Renginio duomenys")

talpa = st.number_input(
    "Renginio talpa",
    min_value=1,
    value=10000,
    step=100
)

bilietai_1 = st.number_input(
    "Parduotų bilietų skaičius po 1 dienos",
    min_value=0,
    value=0,
    step=1
)

bilietai_7 = st.number_input(
    "Parduotų bilietų skaičius po 7 dienų",
    min_value=0,
    value=0,
    step=1
)

bilietai_30 = st.number_input(
    "Parduotų bilietų skaičius po 30 dienų",
    min_value=0,
    value=0,
    step=1
)

arena = st.selectbox(
    "Renginio vieta",
    ["Arena", "Ne arena"]
)

st.divider()

if st.button(
    "PROGNOZUOTI",
    use_container_width=True
):

    if bilietai_7 < bilietai_1:
        st.error(
            "Parduotų bilietų skaičius po 7 dienų "
            "negali būti mažesnis nei po 1 dienos."
        )
        st.stop()

    if bilietai_30 < bilietai_7:
        st.error(
            "Parduotų bilietų skaičius po 30 dienų "
            "negali būti mažesnis nei po 7 dienų."
        )
        st.stop()

    if (
        bilietai_1 > talpa
        or bilietai_7 > talpa
        or bilietai_30 > talpa
    ):
        st.error(
            "Parduotų bilietų skaičius negali būti "
            "didesnis už renginio talpą."
        )
        st.stop()

    if prekybos_dienos < 30:
        st.error(
            "Bilietų prekybos laikotarpis turi būti "
            "ne trumpesnis kaip 30 dienų, nes prognozės "
            "modelis naudoja pardavimus po 30 dienų."
        )
        st.stop()

    # -----------------------------
    # Modelio kintamieji
    # -----------------------------

    eps_change = 1e-6

    pokytis_1_7 = (
        (bilietai_7 - bilietai_1)
        / (bilietai_1 + eps_change)
    )

    pokytis_1_30 = (
        (bilietai_30 - bilietai_1)
        / (bilietai_1 + eps_change)
    )

    uzpildytumas_po_men = (
        bilietai_30 / talpa
    )

    arena_kodas = (
        1 if arena == "Arena" else 0
    )

    # -----------------------------
    # Beta regresijos koeficientai
    # -----------------------------

    coef = {
        "const": 0.2951,
        "Talpa": -0.1183,
        "Pokytis_1_7": 0.4962,
        "Pokytis_1_30": -0.4666,
        "Iki renginio dienos:": 0.3133,
        "Užpildytumas po mėn": 1.3086,
        "Arena": 0.2813
    }

    # -----------------------------
    # StandardScaler parametrai
    # -----------------------------

    means = {
        "Talpa": 3984.6774193548385,
        "Pokytis_1_7": 2.80322621,
        "Pokytis_1_30": 8638710.45364094,
        "Iki renginio dienos:": 107.12903225806451,
        "Užpildytumas po mėn": 0.20507965027357142,
        "Arena": 0.4838709677419355
    }

    stds = {
        "Talpa": 2608.5791755851624,
        "Pokytis_1_7": 86947696.79579352,
        "Pokytis_1_30": 219556955.3296927,
        "Iki renginio dienos:": 58.052669042296785,
        "Užpildytumas po mėn": 0.2010505362618864,
        "Arena": 0.49973978867804687
    }

    # -----------------------------
    # Duomenys modeliui
    # -----------------------------

    X = {
        "Talpa": talpa,
        "Pokytis_1_7": pokytis_1_7,
        "Pokytis_1_30": pokytis_1_30,
        "Iki renginio dienos:": prekybos_dienos,
        "Užpildytumas po mėn": uzpildytumas_po_men,
        "Arena": arena_kodas
    }

    # -----------------------------
    # Standartizavimas
    # -----------------------------

    X_scaled = {}

    for variable in X:
        X_scaled[variable] = (
            (X[variable] - means[variable])
            / stds[variable]
        )

    # -----------------------------
    # Beta regresijos prognozė
    # -----------------------------

    linear_predictor = (
        coef["const"]
        + coef["Talpa"]
        * X_scaled["Talpa"]
        + coef["Pokytis_1_7"]
        * X_scaled["Pokytis_1_7"]
        + coef["Pokytis_1_30"]
        * X_scaled["Pokytis_1_30"]
        + coef["Iki renginio dienos:"]
        * X_scaled["Iki renginio dienos:"]
        + coef["Užpildytumas po mėn"]
        * X_scaled["Užpildytumas po mėn"]
        + coef["Arena"]
        * X_scaled["Arena"]
    )

    prognoze = expit(
        linear_predictor
    )

    prognoze = float(
        np.clip(
            prognoze,
            0,
            1
        )
    )

    prognozuojami_lankytojai = round(
        prognoze * talpa
    )

    # -----------------------------
    # Prognozės rezultatas
    # -----------------------------

    st.success(
        "Prognozė apskaičiuota."
    )

    st.subheader(
        "Prognozės rezultatas"
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Prognozuojamas galutinis užpildymas",
            f"{prognoze:.1%}"
        )

    with col2:
        st.metric(
            "Prognozuojamas lankytojų skaičius",
            f"{prognozuojami_lankytojai:,}".replace(
                ",",
                " "
            )
        )

    st.progress(
        prognoze
    )

    st.divider()

    # -----------------------------
    # Apskaičiuoti rodikliai
    # -----------------------------
st.subheader(
    "Apskaičiuoti rodikliai"
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Užpildymas po 30 d.",
        f"{uzpildytumas_po_men:.1%}"
    )

with col2:
    st.metric(
        "Pardavimai po 1 d.",
        f"{bilietai_1}"
    )

with col3:
    st.metric(
        "Pardavimai po 7 d.",
        f"{bilietai_7}"
    )

with col4:
    st.metric(
        "Pardavimai po 30 d.",
        f"{bilietai_30}"
    )

    st.divider()

    # -----------------------------
    # Prognozės informacija
    # -----------------------------

    st.subheader(
        "Prognozės informacija"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Prognozės data",
            siandien.strftime("%Y-%m-%d")
        )

    with col2:
        st.metric(
            "Renginio data",
            renginio_data.strftime("%Y-%m-%d")
        )

    with col3:
        st.metric(
            "Iki renginio liko",
            f"{dienos_iki_renginio} d."
        )

    st.divider()

    st.caption(
        "Prognozė apskaičiuota naudojant Beta regresijos "
        "modelį, sukurtą remiantis ankstesnių renginių "
        "duomenimis."
    )

    st.caption(
        "Prognozavimo sistemą sukūrė Geistė Buzytė."
    )
