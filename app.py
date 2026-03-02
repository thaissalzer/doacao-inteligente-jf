import streamlit as st
from src.db import ensure_db, seed_if_empty
from scripts.import_pontos_oficiais import main as import_oficiais


def _go_to(page_path: str) -> None:
    """
    Navegação robusta:
    - Tenta st.switch_page (Streamlit mais novo)
    - Se não existir, mostra aviso (fallback visual fica nos page_link abaixo)
    """
    switch = getattr(st, "switch_page", None)
    if callable(switch):
        switch(page_path)
    else:
        st.warning("Seu Streamlit não suporta navegação por botão. Use os links no menu lateral.")


def main() -> None:
    st.set_page_config(
        page_title="Doação Inteligente JF",
        page_icon="🌧️",
        layout="wide",
    )

    db_path = "data/doacao.db"
    ensure_db(db_path)
    import_oficiais()

    st.title("🌧️ Doação Inteligente JF")
    st.subheader("Direcionando solidariedade com eficiência.")

    st.markdown(
        """
Em momentos de tragédia, a vontade de ajudar é enorme.  
O desafio é garantir que cada doação chegue ao lugar certo, no momento certo.

A **Doação Inteligente JF** organiza e divulga, de forma clara e atualizada, **o que cada ponto de arrecadação em Juiz de Fora realmente precisa**.

**Nosso objetivo é simples:**  
ajudar você a saber exatamente **o que doar** e **onde doar**.
        """
    )

    # --- CTAs (botões) sem quebrar layout
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("📍 Ver pontos e necessidades", use_container_width=True):
            _go_to("pages/1_Pontos.py")

    with col2:
        if st.button("🔐 Área Admin", use_container_width=True):
            _go_to("pages/2_Admin.py")

    with col3:
        st.caption("Ou navegue pelo menu à esquerda: **Pontos** / **Admin**.")

    # Fallback visual (aparece sempre e é bem estável)
    st.caption("Atalhos:")
    c1, c2 = st.columns(2)
    with c1:
        st.page_link("pages/1_Pontos.py", label="📍 Ir para Pontos", icon="📍")
    with c2:
        st.page_link("pages/2_Admin.py", label="🔐 Ir para Admin", icon="🔐")

    st.divider()

    st.markdown("### 🎯 Como funciona")
    st.markdown(
        """
Reunimos informações diretamente dos pontos de arrecadação e abrigos ativos e organizamos:

- 📍 Localização do ponto  
- 📦 Itens necessários no momento  
- 🚫 Itens com estoque suficiente  
- ⏰ Data e horário da última atualização  

Assim, evitamos desperdícios e promovemos um melhor direcionamento das doações.
        """
    )

    st.markdown("### 🤝 Nosso compromisso")
    st.markdown(
        """
- Transparência nas informações divulgadas  
- Atualizações frequentes  
- Clareza sobre a origem dos dados  
- Foco na eficiência da ajuda  

A Doação Inteligente JF não substitui os pontos de arrecadação ou a Defesa Civil.  
Nosso papel é conectar informação e solidariedade.
        """
    )

    st.info("💡 Dica: na página **Pontos**, use os filtros para ver só o que está **URGENTE** e foi atualizado recentemente.")


if __name__ == "__main__":
    main()