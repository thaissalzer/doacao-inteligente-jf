import streamlit as st
from src.db import ensure_db
from scripts.import_pontos_oficiais import main as import_oficiais

try:
    from src.db import resolve_db_path
except ImportError:
    from src.db import DEFAULT_DB_PATH

    def resolve_db_path(db_path=None):
        return db_path or DEFAULT_DB_PATH


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

/* =========================
   SIDEBAR MAIS EVIDENTE
   ========================= */
section[data-testid="stSidebar"]{
  background: linear-gradient(180deg, #0b1324 0%, #0f1c33 100%);
  border-right: 1px solid rgba(255,255,255,0.10);
}
section[data-testid="stSidebar"] *{
  color: rgba(255,255,255,0.88);
}
.sidebar-title{
  font-size: 18px;
  font-weight: 900;
  color: #ffffff;
  margin-bottom: 6px;
}
.sidebar-sub{
  color: rgba(255,255,255,0.72);
  font-size: 13px;
  line-height: 1.35;
}
.sidebar-chip{
  display:inline-flex;
  align-items:center;
  gap:8px;
  padding:8px 10px;
  border-radius: 12px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.10);
  color: rgba(255,255,255,0.86);
  font-size: 13px;
  margin-top: 8px;
}
.sidebar-link a{
  color: #47d1c6 !important;
  text-decoration: none;
  font-weight: 800;
}
.sidebar-link a:hover{
  text-decoration: underline;
}

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

/* CTA principal: ver pontos */
div[data-testid="stButton"] > button[kind="primary"] {
  background: linear-gradient(180deg, #fb7185 0%, #ef4444 100%);
  color: #ffffff;
  border: 1px solid #dc2626;
  border-radius: 14px;
  min-height: 82px;
  font-size: 19px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  box-shadow: 0 10px 22px rgba(220, 38, 38, 0.28);
  transition: transform 0.15s ease, filter 0.15s ease, box-shadow 0.15s ease;
}
div[data-testid="stButton"] > button[kind="primary"]::before {
  content: "";
  width: 74px;
  height: 74px;
  flex: 0 0 74px;
  background-repeat: no-repeat;
  background-size: contain;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 140 140'%3E%3Cdefs%3E%3CradialGradient id='g' cx='50%25' cy='38%25' r='72%25'%3E%3Cstop offset='0%25' stop-color='%232d3a46'/%3E%3Cstop offset='100%25' stop-color='%23070b11'/%3E%3C/radialGradient%3E%3C/defs%3E%3Ccircle cx='70' cy='70' r='67' fill='%23d1d5db'/%3E%3Ccircle cx='70' cy='70' r='58' fill='%23f59e0b'/%3E%3Ccircle cx='70' cy='70' r='50' fill='url(%23g)'/%3E%3Ctext x='70' y='62' text-anchor='middle' font-size='22' font-weight='900' font-family='Arial, sans-serif' fill='%23fbbf24'%3ECLIQUE%3C/text%3E%3Ctext x='70' y='88' text-anchor='middle' font-size='22' font-weight='900' font-family='Arial, sans-serif' fill='%23f59e0b'%3EAQUI!%3C/text%3E%3C/svg%3E");
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
  transform: translateY(-1px);
  filter: brightness(1.03);
  box-shadow: 0 12px 26px rgba(220, 38, 38, 0.34);
}

/* Responsivo */
@media (max-width: 920px) {
  .hero h1 { font-size: 40px; }
  .cards { grid-template-columns: 1fr; }
  .dev-banner { flex-direction: column; align-items: flex-start; }
  .dev-right a { width: 100%; text-align: center; }
  div[data-testid="stButton"] > button[kind="primary"] {
    min-height: 68px;
    font-size: 14px;
    letter-spacing: 0.2px;
  }
  div[data-testid="stButton"] > button[kind="primary"]::before {
    width: 50px;
    height: 50px;
    flex-basis: 50px;
  }
}
</style>
        """,
        unsafe_allow_html=True,
    )


def _sidebar() -> None:
    with st.sidebar:
        st.markdown('<div class="sidebar-title">🌧️ Doação Inteligente para JF</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-sub">Direcionando solidariedade DE TODO O BRASIL com eficiência em Juiz de Fora.</div>', unsafe_allow_html=True)

        st.markdown('<div class="sidebar-chip">📍 Pontos • 🔴 URGENTE • ⏰ Atualizações</div>', unsafe_allow_html=True)
        st.divider()

        st.markdown("**Navegação**")
        st.caption("Use o menu padrão do Streamlit (Pontos / Admin) ou os botões na home.")
        st.markdown('<div class="sidebar-link"><a href="https://github.com/thaissalzer/doacao-inteligente-jf" target="_blank">🐙 GitHub do projeto</a></div>', unsafe_allow_html=True)

        st.divider()
        st.caption("Desenvolvedora: **Thais Salzer Procópio** · @thais_salzer")


def _hero() -> None:
    st.markdown(
        """
<div class="hero">
  <h1>🌧️ Doação Inteligente para JF</h1>
  <h2>Direcionando solidariedade DE TODO O BRASIL com eficiência.</h2>
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
    _sidebar()

    db_path = resolve_db_path()
    ensure_db(db_path)
    try:
        import_oficiais()
    except Exception:
        pass

    _hero()
    _highlights()

    st.markdown("")

    # CTAs
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if st.button("VER PONTOS E NECESSIDADES", use_container_width=True, type="primary"):
            _go_to("pages/1_Pontos.py")
    with col2:
        if st.button("🔐 Área Admin", use_container_width=True):
            _go_to("pages/2_Admin.py")
    with col3:
        st.caption("Ou use o menu à esquerda: **Pontos** / **Admin**.")

    # ✅ Atalhos (fallback) só se não houver switch_page
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
