import streamlit as st
from src.db import ensure_db
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


def _dev_banner() -> None:
    """Banner 'É Desenvolvedor?' com botão para o GitHub (estilo similar à imagem)."""
    st.markdown(
        """
<style>
.dev-banner {
  background: linear-gradient(180deg, #0b1324 0%, #0a162b 100%);
  border-radius: 18px;
  padding: 22px 22px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  margin-top: 18px;
}
.dev-left h2 {
  color: #ffffff;
  margin: 0;
  font-size: 30px;
  font-weight: 800;
}
.dev-left p {
  color: rgba(255,255,255,0.72);
  margin: 8px 0 0 0;
  font-size: 16px;
  line-height: 1.35;
  max-width: 880px;
}
.dev-meta {
  margin-top: 10px;
  color: rgba(255,255,255,0.70);
  font-size: 14px;
}
.dev-meta strong { color: rgba(255,255,255,0.92); }
.dev-right a {
  background: #47d1c6;
  color: #06211f;
  text-decoration: none;
  font-weight: 800;
  padding: 12px 18px;
  border-radius: 14px;
  display: inline-block;
  white-space: nowrap;
}
.dev-right a:hover { filter: brightness(0.95); }

/* Responsivo */
@media (max-width: 900px) {
  .dev-banner { flex-direction: column; align-items: flex-start; }
  .dev-right a { width: 100%; text-align: center; }
}
</style>

<div class="dev-banner">
  <div class="dev-left">
    <h2>É Desenvolvedor?</h2>
    <p>Toda ajuda é bem-vinda. Nosso código é aberto. Ajude a acelerar o desenvolvimento dessa ferramenta vital para JF.</p>
    <div class="dev-meta">
      <strong>Desenvolvedora:</strong> Thais Salzer Procópio • <strong>@thais_salzer</strong>
    </div>
  </div>
  <div class="dev-right">
    <a href="https://github.com/thaissalzer/doacao-inteligente-jf" target="_blank" rel="noopener noreferrer">
      Contribuir no GitHub
    </a>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(
        page_title="Doação Inteligente JF",
        page_icon="🌧️",
        layout="wide",
    )

    db_path = "data/doacao.db"
    ensure_db(db_path)
    try:
        import_oficiais()
    except Exception:
        pass

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

    # ✅ Substitui as seções antigas pelo banner de contribuição
    _dev_banner()

    st.info("💡 Dica: na página **Pontos**, use os filtros para ver só o que está **URGENTE** e foi atualizado recentemente.")


if __name__ == "__main__":
    main()