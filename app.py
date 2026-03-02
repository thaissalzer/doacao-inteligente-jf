import streamlit as st
from src.db import ensure_db
from scripts.import_pontos_oficiais import main as import_oficiais


def _go_to(page_path: str) -> None:
    """Navegação robusta (compatível com versões diferentes do Streamlit)."""
    switch = getattr(st, "switch_page", None)
    if callable(switch):
        switch(page_path)
    else:
        st.warning("Seu Streamlit não suporta navegação por botão. Use os links no menu lateral.")


def _inject_css() -> None:
    st.markdown(
        """
<style>
/* Layout geral */
.block-container { padding-top: 2.2rem; }

/* Hero */
.hero {
  background: linear-gradient(135deg, rgba(12,22,38,1) 0%, rgba(13,28,50,1) 55%, rgba(8,16,28,1) 100%);
  border-radius: 20px;
  padding: 28px 28px;
  border: 1px solid rgba(255,255,255,0.06);
}
.hero h1 {
  margin: 0;
  color: #ffffff;
  font-size: 48px;
  line-height: 1.05;
  font-weight: 900;
  letter-spacing: -0.5px;
}
.hero h2 {
  margin: 10px 0 0 0;
  color: rgba(255,255,255,0.78);
  font-size: 22px;
  font-weight: 700;
}
.hero p {
  margin: 14px 0 0 0;
  color: rgba(255,255,255,0.72);
  font-size: 16px;
  line-height: 1.45;
  max-width: 980px;
}
.hero-badges {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255,255,255,0.08);
  color: rgba(255,255,255,0.80);
  font-size: 13px;
  border: 1px solid rgba(255,255,255,0.10);
}

/* Cards */
.cards {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-top: 14px;
}
.card {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 18px;
  padding: 16px 16px;
}
.card h3 {
  margin: 0;
  color: rgba(255,255,255,0.92);
  font-size: 16px;
  font-weight: 800;
}
.card p {
  margin: 8px 0 0 0;
  color: rgba(255,255,255,0.70);
  font-size: 14px;
  line-height: 1.35;
}

/* Banner dev */
.dev-banner {
  background: linear-gradient(180deg, #0b1324 0%, #0a162b 100%);
  border-radius: 18px;
  padding: 20px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  border: 1px solid rgba(255,255,255,0.06);
}
.dev-left h3 {
  color: #ffffff;
  margin: 0;
  font-size: 26px;
  font-weight: 900;
}
.dev-left p {
  color: rgba(255,255,255,0.72);
  margin: 8px 0 0 0;
  font-size: 15px;
  line-height: 1.35;
  max-width: 880px;
}
.dev-meta {
  margin-top: 10px;
  color: rgba(255,255,255,0.70);
  font-size: 13px;
}
.dev-meta strong { color: rgba(255,255,255,0.92); }
.dev-right a {
  background: #47d1c6;
  color: #06211f;
  text-decoration: none;
  font-weight: 900;
  padding: 12px 18px;
  border-radius: 14px;
  display: inline-block;
  white-space: nowrap;
}
.dev-right a:hover { filter: brightness(0.95); }

/* Responsivo */
@media (max-width: 920px) {
  .hero h1 { font-size: 40px; }
  .cards { grid-template-columns: 1fr; }
  .dev-banner { flex-direction: column; align-items: flex-start; }
  .dev-right a { width: 100%; text-align: center; }
}
</style>
        """,
        unsafe_allow_html=True,
    )


def _hero() -> None:
    st.markdown(
        """
<div class="hero">
  <h1>🌧️ Doação Inteligente JF</h1>
  <h2>Direcionando solidariedade com eficiência.</h2>
  <p>
    Em momentos de tragédia, a vontade de ajudar é enorme.
    O desafio é garantir que cada doação chegue ao lugar certo, no momento certo.
    <br><br>
    A <b>Doação Inteligente JF</b> organiza e divulga, de forma clara e atualizada, <b>o que cada ponto de arrecadação em Juiz de Fora realmente precisa</b>.
    <br>
    <b>Objetivo:</b> ajudar você a saber exatamente <b>o que doar</b> e <b>onde doar</b>.
  </p>

  <div class="hero-badges">
    <div class="badge">📍 Pontos oficiais</div>
    <div class="badge">⏰ Data/hora da última atualização</div>
    <div class="badge">🔴 URGENTE / 🟡 PRECISA / 🟢 OK</div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def _highlights() -> None:
    st.markdown(
        """
<div class="cards">
  <div class="card">
    <h3>🧭 Direcionamento</h3>
    <p>Veja rapidamente onde sua doação faz mais diferença, evitando acúmulos e desperdícios.</p>
  </div>
  <div class="card">
    <h3>🔎 Transparência</h3>
    <p>Informações organizadas por ponto, com status e registro de atualização.</p>
  </div>
  <div class="card">
    <h3>⚡ Praticidade</h3>
    <p>Filtros por ponto, bairro, categoria, status e recência da atualização.</p>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def _dev_banner() -> None:
    st.markdown(
        """
<div class="dev-banner">
  <div class="dev-left">
    <h3>É Desenvolvedor?</h3>
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
    st.set_page_config(page_title="Doação Inteligente JF", page_icon="🌧️", layout="wide")
    _inject_css()

    db_path = "data/doacao.db"
    ensure_db(db_path)
    try:
        import_oficiais()
    except Exception:
        pass

    _hero()
    _highlights()

    st.markdown("")

# CTAs (padrão único, sem duplicar)
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button("📍 Ver pontos e necessidades", use_container_width=True):
        _go_to("pages/1_Pontos.py")

with col2:
    if st.button("🔐 Área Admin", use_container_width=True):
        _go_to("pages/2_Admin.py")

with col3:
    st.caption("Ou use o menu à esquerda: **Pontos** / **Admin**.")

# ✅ Fallback: só mostra links se não existir switch_page
if not callable(getattr(st, "switch_page", None)):
    st.caption("Atalhos (fallback):")
    c1, c2 = st.columns(2)
    with c1:
        st.page_link("pages/1_Pontos.py", label="📍 Ir para Pontos", icon="📍")
    with c2:
        st.page_link("pages/2_Admin.py", label="🔐 Ir para Admin", icon="🔐")
    st.markdown("")
    _dev_banner()

    st.info("💡 Dica: na página **Pontos**, use os filtros para ver só o que está **URGENTE** e foi atualizado recentemente.")

    st.markdown(
        "<div style='margin-top:14px; color: rgba(255,255,255,0.45); font-size: 12px;'>"
        "Doação Inteligente JF • código aberto no GitHub • informações públicas e de voluntários"
        "</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()