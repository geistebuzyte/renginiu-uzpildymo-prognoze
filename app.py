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
    "galutinį užpildymą, lankytojų skaičių bei pajamas."
)

st.divider()


# ============================================================
# RENGINIO DATOS
# ============================================================

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


# Realus dienų skaičius nuo šiandien iki renginio
dienos_iki_renginio = max(
    (renginio_data - siandien).days,
    0
)


# Visas bilietų prekybos laikotarpis
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


# ============================================================
# RENGINIO DUOMENYS
# ============================================================

st.subheader("Renginio duomenys")


talpa = st.number_input(
    "Renginio talpa",
    min_value=1,
    value=10000,
    step=100
)


vidutine_bilieto_kaina = st.number_input(
    "Vidutinė bilieto kaina (€)",
    min_value=0.0,
    value=20.0,
    step=0.50,
    format="%.2f"
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


# ============================================================
# PROGNOZĖ
# ============================================================

if st.button(
    "PROGNOZUOTI",
    use_container_width=True
):

    # --------------------------------------------------------
    # DUOMENŲ PATIKRA
    # --------------------------------------------------------

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
            "ne trumpesnis kaip 30 dienų, nes modelis "
            "naudoja pardavimus po 30 dienų."
        )
        st.stop()


    # --------------------------------------------------------
    # MODELIO KINTAMIEJI
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # BETA REGRESIJOS KOEFICIENTAI
    # --------------------------------------------------------

    coef = {
        "const": 0.2951,
        "Talpa": -0.1183,
        "Pokytis_1_7": 0.4962,
        "Pokytis_1_30": -0.4666,
        "Iki renginio dienos:": 0.3133,
        "Užpildytumas po mėn": 1.3086,
        "Arena": 0.2813
    }


    # --------------------------------------------------------
    # STANDARD SCALER PARAMETRAI
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # DUOMENYS MODELIUI
    # --------------------------------------------------------

    X = {
        "Talpa": talpa,
        "Pokytis_1_7": pokytis_1_7,
        "Pokytis_1_30": pokytis_1_30,
        "Iki renginio dienos:": prekybos_dienos,
        "Užpildytumas po mėn": uzpildytumas_po_men,
        "Arena": arena_kodas
    }


    # --------------------------------------------------------
    # STANDARTIZAVIMAS
    # --------------------------------------------------------

    X_scaled = {}

    for variable in X:
        X_scaled[variable] = (
            (X[variable] - means[variable])
            / stds[variable]
        )


    # --------------------------------------------------------
    # BETA REGRESIJOS PROGNOZĖ
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # LANKYTOJAI
    # --------------------------------------------------------

    prognozuojami_lankytojai = round(
        prognoze * talpa
    )


    # --------------------------------------------------------
    # PAJAMOS
    # --------------------------------------------------------

    prognozuojamos_pajamos = (
        prognozuojami_lankytojai
        * vidutine_bilieto_kaina
    )


    # ========================================================
    # 95 % APYTIKSLIS PROGNOZĖS INTERVALAS
    # ========================================================

    rmse = 0.1032

    z_95 = 1.96

    intervalo_paklaida = (
        z_95 * rmse
    )


    intervalo_min = max(
        prognoze - intervalo_paklaida,
        0
    )


    intervalo_max = min(
        prognoze + intervalo_paklaida,
        1
    )


    # --------------------------------------------------------
    # LANKYTOJŲ INTERVALAS
    # --------------------------------------------------------

    lankytojai_min = round(
        intervalo_min * talpa
    )


    lankytojai_max = round(
        intervalo_max * talpa
    )


    # --------------------------------------------------------
    # PAJAMŲ INTERVALAS
    # --------------------------------------------------------

    pajamos_min = (
        lankytojai_min
        * vidutine_bilieto_kaina
    )


    pajamos_max = (
        lankytojai_max
        * vidutine_bilieto_kaina
    )


    # ========================================================
    # PROGNOZĖS REZULTATAS
    # ========================================================

    st.success(
        "Prognozė apskaičiuota."
    )


    st.subheader(
        "Prognozės rezultatas"
    )


    col1, col2, col3 = st.columns(3)


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


    with col3:
        st.metric(
            "Prognozuojamos renginio pajamos",
            f"{prognozuojamos_pajamos:,.2f} €".replace(
                ",",
                " "
            )
        )


    st.progress(
        prognoze
    )


    st.divider()


    # ========================================================
    # PROGNOZĖS INTERVALAS
    # ========================================================

    st.subheader(
        "Prognozės intervalas"
    )


    col1, col2 = st.columns(2)


    with col1:
        st.metric(
            "Apytikslis 95 % užpildymo intervalas",
            f"{intervalo_min:.1%} – {intervalo_max:.1%}"
        )


    with col2:
        st.metric(
            "Galimas lankytojų intervalas",
            f"{lankytojai_min:,} – {lankytojai_max:,}".replace(
                ",",
                " "
            )
        )


    st.metric(
        "Galimų pajamų intervalas",
        f"{pajamos_min:,.2f} € – {pajamos_max:,.2f} €".replace(
            ",",
            " "
        )
    )


    st.caption(
        "Intervalas yra apytikslis ir apskaičiuotas "
        "pagal modelio RMSE = 0,1032 bei 95 % koeficientą."
    )


    st.divider()


    # ========================================================
    # APSKAIČIUOTI RODIKLIAI
    # ========================================================

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


    # ========================================================
    # PROGNOZĖS INFORMACIJA
    # ========================================================

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
        "Apytikslis 95 % prognozės intervalas apskaičiuotas "
        "remiantis modelio RMSE = 0,1032."
    )


    st.caption(
        "Prognozavimo sistemą sukūrė Geistė Buzytė."
    )
