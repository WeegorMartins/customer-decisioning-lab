import json
import re
from pathlib import Path

import pandas as pd
import streamlit as st

try:
    from google import genai
except ImportError:
    genai = None


st.set_page_config(
    page_title="Customer Decisioning Lab",
    page_icon="🎯",
    layout="wide"
)


SUMMARY_PATH = Path(
    "data/app/policy_summary.json"
)


@st.cache_data
def load_summary():
    with open(
        SUMMARY_PATH,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


summary = load_summary()


PII_PATTERNS = [
    r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b",
    (
        r"\b[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+"
        r"\.[A-Za-z]{2,}\b"
    ),
    (
        r"\b(?:\+?55\s?)?"
        r"\(?\d{2}\)?\s?"
        r"\d{4,5}-?\d{4}\b"
    ),
    r"\b(?:\d[ -]*?){13,19}\b"
]


def contains_pii(text):
    return any(
        re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )
        for pattern in PII_PATTERNS
    )


def policy_table(summary):
    rows = []
    for name in [
        "control",
        "challenger",
        "champion"
    ]:
        values = summary[name]
        rows.append({
            "Política": name,
            "Clientes": values["customers"],
            "Conversão":
                values["conversion_rate"],
            "Valor médio":
                values["average_net_value"],
            "Opt-out":
                values["optout_rate"]
        })
    return pd.DataFrame(rows)


st.title("Customer Decisioning Lab")

st.warning(
    "Portfólio com dados públicos e sintéticos. "
    "Nenhum valor representa impacto real."
)

tabs = st.tabs([
    "Resumo",
    "Experimento",
    "Restrições",
    "Copiloto"
])


with tabs[0]:
    table = policy_table(summary)

    champion = summary["champion"]
    control = summary["control"]

    difference = (
        champion["average_net_value"]
        - control["average_net_value"]
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Champion — valor médio",
        f"R$ {champion['average_net_value']:.2f}"
    )

    col2.metric(
        "Controle — valor médio",
        f"R$ {control['average_net_value']:.2f}"
    )

    col3.metric(
        "Diferença simulada",
        f"R$ {difference:.2f}"
    )

    st.dataframe(
        table.style.format({
            "Conversão": "{:.2%}",
            "Valor médio": "R$ {:.2f}",
            "Opt-out": "{:.2%}"
        }),
        use_container_width=True
    )


with tabs[1]:
    st.subheader("Desenho")
    st.write(
        "Controle: 10% | Challenger: 18% | "
        "Champion: 72%"
    )

    chart_data = policy_table(
        summary
    ).set_index("Política")[[
        "Conversão",
        "Opt-out"
    ]]

    st.bar_chart(chart_data)

    st.caption(
        "Resultados simulados para testar o fluxo."
    )


with tabs[2]:
    constraints = summary["constraints"]

    st.json(constraints)

    st.write(
        "O modelo estima. O otimizador recomenda. "
        "O experimento prova. O humano aprova."
    )


with tabs[3]:
    st.subheader("Copiloto auditável")

    question = st.text_input(
        "Pergunta sobre métricas agregadas"
    )

    if st.button("Perguntar"):
        if not question.strip():
            st.info("Digite uma pergunta.")

        elif contains_pii(question):
            st.error(
                "Não posso processar dados pessoais."
            )

        elif (
            "GEMINI_API_KEY" not in st.secrets
            or genai is None
        ):
            st.info(
                "Modo offline: a aplicação continua "
                "funcionando sem API."
            )
            st.json(summary)

        else:
            client = genai.Client(
                api_key=st.secrets[
                    "GEMINI_API_KEY"
                ]
            )

            prompt = f"""
Use somente o JSON abaixo.
Não invente números.
O resultado é uma simulação.
Não ative campanhas.
Toda decisão requer aprovação humana.

JSON:
{json.dumps(summary, ensure_ascii=False)}

Pergunta:
{question}
"""

            response = (
                client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt
                )
            )

            st.write(response.text)
            st.caption(
                "Fonte: policy_summary.json"
            )
