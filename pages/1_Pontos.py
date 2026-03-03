from __future__ import annotations

from datetime import datetime

import streamlit as st

from src.db import (
    ensure_db,
    get_ponto,
    last_update_for_ponto,
    list_necessidades,
    list_pontos,
)

try:
    from src.db import resolve_db_path
except ImportError:
    from src.db import DEFAULT_DB_PATH

    def resolve_db_path(db_path=None):
        return db_path or DEFAULT_DB_PATH

from src.ui import (
    badge_status,
    copyable_list,
    google_maps_url,
    parse_iso,
    whatsapp_url,
)


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
.meta-soft {
  color: rgba(255,255,255,0.66);
  font-size: 12px;
}
.point-title {
  margin: 0;
  font-size: 22px;
  font-weight: 900;
  color: #f8fafc;
}
.point-sub {
  margin: 2px 0 10px 0;
  color: rgba(255,255,255,0.66);
  font-size: 13px;
}
.link-list a {
  font-weight: 800;
  text-decoration: none;
}
.status-block h4 {
  margin: 0 0 6px 0;
  font-size: 14px;
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


def _human_last_update(updated_at_iso: str | None) -> str:
    hours = _hours_since(updated_at_iso)
    if hours is None:
        return "sem atualizacao registrada"
    if hours <= 0:
        return "agora ha pouco"
    if hours == 1:
        return "ha 1 hora"
    return f"ha {hours} horas"


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
  <p>Veja o que esta mais urgente, escolha o ponto certo e direcione sua ajuda com mais eficiencia.</p>
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
    st.sidebar.caption("Refine por local, categoria e recencia de atualizacao.")

    pontos_selecionados = st.sidebar.multiselect(
        "Pontos de coleta",
        options=rotulos_ordenados,
        default=[],
        help="Selecione um ou mais pontos. Vazio mostra todos.",
    )

    categorias = ["Todas", "Água", "Alimentos", "Higiene", "Limpeza", "Roupas", "Fraldas", "Outros"]
    status_opts = ["Todos", "URGENTE", "PRECISA", "OK"]

    filtro_cat = st.sidebar.selectbox("Categoria", categorias, index=0)
    filtro_status = st.sidebar.selectbox("Status", status_opts, index=0)

    bairros = sorted({p.bairro for p in pontos if p.bairro and p.bairro != "—"})
    filtro_bairro = st.sidebar.selectbox("Bairro/Regiao", ["Todos"] + bairros, index=0)
    max_horas = st.sidebar.slider("Atualizado nas ultimas (horas)", min_value=1, max_value=168, value=72)

    ponto_ids = [p.id for p in pontos]
    necessidades = list_necessidades(db_path, ponto_ids=ponto_ids, categoria=filtro_cat, status=filtro_status)

    by_ponto: dict[str, list] = {}
    for n in necessidades:
        by_ponto.setdefault(n.ponto_id, []).append(n)

    last_update_map = {p.id: last_update_for_ponto(db_path, p.id) for p in pontos}

    ids_escolhidos = None
    if pontos_selecionados:
        ids_escolhidos = {rotulo_para_id[r] for r in pontos_selecionados}

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
        st.error("Ponto nao encontrado.")
        return

    st.markdown(f"### {ponto.nome}")
    st.caption(f"{ponto.tipo} • {ponto.bairro}")
    st.write(f"📍 **Endereco:** {ponto.endereco}")
    st.write(f"🕒 **Horario:** {ponto.horario}")

    det_nec = list_necessidades(db_path, ponto_ids=[ponto_id], categoria="Todas", status="Todos")
    if not det_nec:
        st.info("Ainda nao ha itens cadastrados para este ponto.")
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
        urg = sum(1 for n in necessidades if n.status == "URGENTE")
        st.metric("Itens urgentes", urg)
    with col_c:
        ult_atual = [u for u in last_update_map.values() if u]
        st.metric("Pontos com atualizacao", len(ult_atual))

    st.caption("Status: 🔴 URGENTE | 🟡 PRECISA | 🟢 OK")
    st.divider()

    if not pontos_filtrados:
        st.info("Nenhum ponto encontrado com os filtros atuais.")
    for p in pontos_filtrados:
        itens = by_ponto.get(p.id, [])
        urgentes = [n for n in itens if n.status == "URGENTE"]
        precisa = [n for n in itens if n.status == "PRECISA"]
        ok = [n for n in itens if n.status == "OK"]
        last_upd = last_update_map.get(p.id)

        with st.container(border=True):
            top1, top2, top3 = st.columns([2.1, 1.0, 1.1])

            with top1:
                st.markdown(f'<p class="point-title">{p.nome}</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="point-sub">{p.tipo} • {p.bairro}</p>', unsafe_allow_html=True)
                st.write(f"📍 **Endereco:** {p.endereco}")
                st.write(f"🕒 **Horario:** {p.horario}")

            with top2:
                st.write("**Ultima atualizacao**")
                st.write(f"⏰ {_human_last_update(last_upd)}")
                if last_upd:
                    st.caption(last_upd.replace("T", " ").replace("+", " +"))
                else:
                    st.markdown('<div class="meta-soft">Sem registro de atualizacao.</div>', unsafe_allow_html=True)

            with top3:
                maps = google_maps_url(p.endereco)
                wa = whatsapp_url(
                    p.contato_whats,
                    text="Ola! Estou conferindo as necessidades do ponto. Pode confirmar o que esta precisando agora?",
                )
                st.markdown('<div class="link-list">', unsafe_allow_html=True)
                st.markdown(f"🗺️ **[Abrir no mapa]({maps})**")
                if wa:
                    st.markdown(f"💬 **[WhatsApp]({wa})**")
                else:
                    st.button("💬 WhatsApp", disabled=True, use_container_width=True, key=f"wa_disabled_{p.id}")
                st.markdown("</div>", unsafe_allow_html=True)

            st.divider()
            s1, s2, s3 = st.columns(3)

            with s1:
                st.markdown("#### 🔴 URGENTE")
                if urgentes:
                    for n in urgentes:
                        extra = f" - {n.observacao}" if n.observacao else ""
                        st.write(f"- {n.item}{extra}")
                else:
                    st.caption("Sem itens neste status.")

            with s2:
                st.markdown("#### 🟡 PRECISA")
                if precisa:
                    for n in precisa:
                        extra = f" - {n.observacao}" if n.observacao else ""
                        st.write(f"- {n.item}{extra}")
                else:
                    st.caption("Sem itens neste status.")

            with s3:
                st.markdown("#### 🟢 OK")
                if ok:
                    for n in ok:
                        extra = f" - {n.observacao}" if n.observacao else ""
                        st.write(f"- {n.item}{extra}")
                else:
                    st.caption("Sem itens neste status.")

            to_copy = [f"{badge_status(n.status)} • {n.categoria}: {n.item}" for n in (urgentes + precisa)]
            copyable_list(to_copy, title="Copiar lista (URGENTE + PRECISA)")


main()
