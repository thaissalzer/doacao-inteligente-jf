from __future__ import annotations

from datetime import datetime
from html import escape

import streamlit as st

from src.db import ensure_db, get_ponto, last_update_for_ponto, list_necessidades, list_pontos
from src.ui import badge_status, parse_iso

try:
    from src.db import resolve_db_path
except ImportError:
    from src.db import DEFAULT_DB_PATH

    def resolve_db_path(db_path=None):
        return db_path or DEFAULT_DB_PATH


def _inject_page_css() -> None:
    st.markdown(
        """
<style>
.pontos-hero {
  border-radius: 16px;
  padding: 18px 20px;
  background: linear-gradient(135deg, #0f1f35 0%, #133053 100%);
  border: 1px solid rgba(255,255,255,0.08);
  margin-bottom: 12px;
}
.pontos-hero h2 {
  margin: 0;
  color: #ffffff;
  font-size: 28px;
  font-weight: 900;
  letter-spacing: -0.3px;
}
.pontos-hero p {
  margin: 8px 0 0 0;
  color: rgba(255,255,255,0.80);
  font-size: 15px;
}
.updates-card {
  border: 1px solid #cfe9de;
  border-radius: 18px;
  padding: 18px 18px 14px 18px;
  background: #ffffff;
  box-shadow: 0 1px 0 rgba(14, 23, 38, 0.04);
  margin-bottom: 14px;
}
.updates-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: flex-start;
}
.updates-title {
  margin: 0;
  color: #111827;
  font-size: 38px;
  font-weight: 900;
  line-height: 1.12;
}
.updates-subline {
  margin-top: 8px;
  color: #4b5563;
  font-size: 28px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.pill-type {
  border-radius: 999px;
  border: 1px solid #8ad7bc;
  color: #06784e;
  background: #e9fbf3;
  font-weight: 700;
  padding: 4px 12px;
  font-size: 24px;
}
.pill-urgent-count {
  border-radius: 999px;
  background: #ff2e44;
  color: #ffffff;
  font-weight: 800;
  padding: 6px 14px;
  font-size: 24px;
  white-space: nowrap;
}
.updates-address {
  margin-top: 14px;
  color: #374151;
  font-size: 32px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.updates-divider {
  border: none;
  border-top: 1px solid #dbe8e2;
  margin: 14px 0 12px 0;
}
.need-title {
  margin: 0 0 8px 0;
  color: #4b5563;
  font-size: 24px;
  letter-spacing: 0.5px;
  font-weight: 800;
}
.need-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 7px;
}
.need-left {
  color: #111827;
  font-size: 34px;
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.cat-pill {
  border-radius: 10px;
  padding: 3px 10px;
  border: 1px solid #d1d5db;
  font-size: 22px;
  font-weight: 700;
  white-space: nowrap;
}
.cat-agua,.cat-alimentos,.cat-limpeza,.cat-higiene,.cat-roupas,.cat-fraldas,.cat-outros {
  color: #0f3f95;
  background: #eef4ff;
  border-color: #bfd6ff;
}
.status-pill {
  border-radius: 12px;
  padding: 4px 12px;
  font-size: 24px;
  font-weight: 700;
  white-space: nowrap;
}
.status-urgente { color: #c8102e; background: #ffe5e8; border: 1px solid #f7b6c0; }
.status-precisa { color: #b45309; background: #fff2d9; border: 1px solid #f5daa1; }
.status-ok { color: #166534; background: #e9f9ee; border: 1px solid #b7e7c4; }
.updates-foot { margin-top: 8px; font-size: 27px; }
.foot-urg { color: #d10016; font-weight: 700; }
.foot-pre { color: #c76b00; font-weight: 700; margin-left: 10px; }
.foot-ok { color: #0b7a40; font-weight: 700; margin-left: 10px; }

@media (max-width: 920px) {
  .updates-title { font-size: 28px; }
  .updates-subline { font-size: 18px; }
  .pill-type, .pill-urgent-count { font-size: 15px; }
  .updates-address { font-size: 22px; }
  .need-title { font-size: 16px; }
  .need-left { font-size: 20px; }
  .cat-pill { font-size: 14px; }
  .status-pill { font-size: 15px; }
  .updates-foot { font-size: 18px; }
}
</style>
        """,
        unsafe_allow_html=True,
    )


def _hours_since(updated_at_iso: str | None) -> int | None:
    if not updated_at_iso:
        return None
    dt = parse_iso(updated_at_iso)
    if not dt:
        return None
    delta = datetime.now(dt.tzinfo) - dt
    return int(delta.total_seconds() // 3600)


def _cat_class(categoria: str) -> str:
    base = (categoria or "outros").strip().lower().replace(" ", "-")
    allowed = {"agua", "alimentos", "limpeza", "higiene", "roupas", "fraldas", "outros"}
    return f"cat-{base}" if base in allowed else "cat-outros"


def _status_class(status: str) -> str:
    s = (status or "").upper().strip()
    if s == "URGENTE":
        return "status-urgente"
    if s == "PRECISA":
        return "status-precisa"
    return "status-ok"


def main() -> None:
    st.set_page_config(page_title="Pontos - Doação Inteligente JF", page_icon="📍", layout="wide")
    _inject_page_css()

    db_path = resolve_db_path()
    ensure_db(db_path)

    try:
        from scripts.import_pontos_oficiais import main as import_oficiais

        import_oficiais()
    except Exception:
        pass

    st.markdown(
        """
<div class="pontos-hero">
  <h2>Lista de Pontos de Doação e Necessidades</h2>
  <p>Veja o que está mais urgente, escolha o ponto certo e direcione sua ajuda com eficiência.</p>
</div>
        """,
        unsafe_allow_html=True,
    )

    pontos = list_pontos(db_path, only_active=True)
    if not pontos:
        st.warning("Nenhum ponto ativo cadastrado ainda.")
        return

    rotulo_para_id = {f"{p.nome} - {p.bairro}": p.id for p in pontos}
    rotulos_ordenados = sorted(rotulo_para_id.keys())

    st.sidebar.header("Filtros")
    st.sidebar.caption("Refine por local, categoria e recência de atualização.")
    pontos_selecionados = st.sidebar.multiselect(
        "Pontos de coleta", options=rotulos_ordenados, default=[], help="Selecione um ou mais pontos. Vazio mostra todos."
    )
    categorias = ["Todas", "Água", "Alimentos", "Higiene", "Limpeza", "Roupas", "Fraldas", "Outros"]
    status_opts = ["Todos", "URGENTE", "PRECISA", "OK"]
    filtro_cat = st.sidebar.selectbox("Categoria", categorias, index=0)
    filtro_status = st.sidebar.selectbox("Status", status_opts, index=0)
    bairros = sorted({p.bairro for p in pontos if p.bairro and p.bairro != "—"})
    filtro_bairro = st.sidebar.selectbox("Bairro/Região", ["Todos"] + bairros, index=0)
    max_horas = st.sidebar.slider("Atualizado nas últimas (horas)", min_value=1, max_value=168, value=72)

    ponto_ids = [p.id for p in pontos]
    necessidades = list_necessidades(db_path, ponto_ids=ponto_ids, categoria=filtro_cat, status=filtro_status)

    by_ponto: dict[str, list] = {}
    for n in necessidades:
        by_ponto.setdefault(n.ponto_id, []).append(n)

    last_update_map = {p.id: last_update_for_ponto(db_path, p.id) for p in pontos}

    ids_escolhidos = {rotulo_para_id[r] for r in pontos_selecionados} if pontos_selecionados else None
    pontos_filtrados = []
    for p in pontos:
        if ids_escolhidos and p.id not in ids_escolhidos:
            continue
        if filtro_bairro != "Todos" and p.bairro != filtro_bairro:
            continue
        hrs = _hours_since(last_update_map.get(p.id))
        if hrs is None or hrs > max_horas:
            continue
        pontos_filtrados.append(p)

    def ranking_key(ponto):
        itens = by_ponto.get(ponto.id, [])
        urg = sum(1 for n in itens if n.status == "URGENTE")
        pre = sum(1 for n in itens if n.status == "PRECISA")
        upd = _hours_since(last_update_map.get(ponto.id))
        upd_score = 999999 if upd is None else upd
        return (-urg, -pre, upd_score, ponto.nome.lower())

    pontos_filtrados.sort(key=ranking_key)

    st.markdown("## Detalhe de um ponto")
    ponto_map = {f"{p.nome} - {p.bairro}": p.id for p in pontos}
    escolha = st.selectbox("Escolha um ponto para ver detalhes", list(ponto_map.keys()))
    ponto_id = ponto_map[escolha]
    ponto = get_ponto(db_path, ponto_id)
    if not ponto:
        st.error("Ponto não encontrado.")
        return

    st.markdown(f"### {ponto.nome}")
    st.caption(f"{ponto.tipo} • {ponto.bairro}")
    st.write(f"📍 **Endereço:** {ponto.endereco}")
    st.write(f"🕒 **Horário:** {ponto.horario}")

    det_nec = list_necessidades(db_path, ponto_ids=[ponto_id], categoria="Todas", status="Todos")
    if not det_nec:
        st.info("Ainda não há itens cadastrados para este ponto.")
    else:
        st.markdown("#### Itens cadastrados")
        for n in det_nec:
            extra = f" - {n.observacao}" if n.observacao else ""
            st.write(f"- {badge_status(n.status)} • **{n.categoria}**: {n.item}{extra} _(atualizado: {n.updated_at})_")

    st.divider()
    st.markdown("## Últimas Atualizações de Necessidades em Pontos de Doação")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Pontos exibidos", len(pontos_filtrados))
    with col_b:
        st.metric("Itens urgentes", sum(1 for n in necessidades if n.status == "URGENTE"))
    with col_c:
        st.metric("Pontos com atualização", len([u for u in last_update_map.values() if u]))

    st.divider()

    if not pontos_filtrados:
        st.info("Nenhum ponto encontrado com os filtros atuais.")
        return

    for p in pontos_filtrados:
        itens = by_ponto.get(p.id, [])
        urgentes = [n for n in itens if n.status == "URGENTE"]
        precisa = [n for n in itens if n.status == "PRECISA"]
        ok = [n for n in itens if n.status == "OK"]
        itens_ordenados = urgentes + precisa + ok

        needs_rows = []
        for n in itens_ordenados:
            cat_cls = _cat_class(n.categoria)
            st_cls = _status_class(n.status)
            cat = escape(n.categoria or "Outros")
            item = escape(n.item or "")
            status = escape(n.status.title())
            needs_rows.append(
                f"""
<div class="need-row">
  <div class="need-left">
    <span class="cat-pill {cat_cls}">{cat}</span>
    <span>{item}</span>
  </div>
  <span class="status-pill {st_cls}">{status}</span>
</div>
                """.strip()
            )

        needs_html = "\n".join(needs_rows) if needs_rows else '<div class="meta-soft">Sem itens neste filtro.</div>'
        card_html = f"""
<div class="updates-card">
  <div class="updates-head">
    <div>
      <h3 class="updates-title">{escape(p.nome)}</h3>
      <div class="updates-subline">
        <span class="pill-type">{escape(p.tipo)}</span>
        <span>• {escape(p.bairro)}</span>
      </div>
    </div>
    <span class="pill-urgent-count">{len(urgentes)} urgente{'s' if len(urgentes) != 1 else ''}</span>
  </div>
  <div class="updates-address">📍 {escape(p.endereco)}</div>
  <hr class="updates-divider" />
  <h4 class="need-title">NECESSIDADES</h4>
  {needs_html}
  <div class="updates-foot">
    <span class="foot-urg">{len(urgentes)} urgente{'s' if len(urgentes) != 1 else ''}</span>
    <span class="foot-pre">{len(precisa)} necessário{'s' if len(precisa) != 1 else ''}</span>
    <span class="foot-ok">{len(ok)} ok</span>
  </div>
</div>
        """.strip()
        st.markdown(card_html, unsafe_allow_html=True)


main()
