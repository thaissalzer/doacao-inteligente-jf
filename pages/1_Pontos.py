import streamlit as st

from src.db import list_pontos, list_necessidades, last_update_for_ponto, get_ponto
from src.ui import badge_status, human_hours_ago, google_maps_url, whatsapp_url, copyable_list

def main() -> None:
    st.set_page_config(page_title="Pontos • Doação Inteligente JF", page_icon="📍", layout="wide")

    db_path = "data/doacao.db"

    st.title("📍 Pontos de doação e necessidades")

    pontos = list_pontos(db_path, only_active=True)
    if not pontos:
        st.warning("Nenhum ponto ativo cadastrado ainda.")
        return

    # --- Filtros
    st.sidebar.header("Filtros")
    categorias = ["Todas", "Água", "Alimentos", "Higiene", "Limpeza", "Roupas", "Fraldas", "Outros"]
    status_opts = ["Todos", "URGENTE", "PRECISA", "OK"]

    filtro_cat = st.sidebar.selectbox("Categoria", categorias, index=0)
    filtro_status = st.sidebar.selectbox("Status", status_opts, index=0)

    bairros = sorted({p.bairro for p in pontos})
    filtro_bairro = st.sidebar.selectbox("Bairro/Região", ["Todos"] + bairros, index=0)

    max_horas = st.sidebar.slider("Atualizado nas últimas (horas)", min_value=1, max_value=168, value=72)

    # Carrega necessidades já filtradas por categoria/status para construir os cards
    ponto_ids = [p.id for p in pontos]
    necessidades = list_necessidades(db_path, ponto_ids=ponto_ids, categoria=filtro_cat, status=filtro_status)

    # Indexa necessidades por ponto
    by_ponto: dict[str, list] = {}
    for n in necessidades:
        by_ponto.setdefault(n.ponto_id, []).append(n)

    # Filtra pontos por bairro e “atualizado nas últimas X horas”
    def within_hours(ponto_id: str) -> bool:
        last_upd = last_update_for_ponto(db_path, ponto_id)
        if not last_upd:
            return False
        # usa a mesma lógica de "human_hours_ago", mas aqui só aproximamos por string → horas via delta no ui
        # para simplicidade: reaproveita o texto e não filtra com precisão de minutos
        # (se quiser precisão, eu ajusto para calcular delta em segundos aqui)
        txt = human_hours_ago(last_upd)
        if txt == "agora há pouco":
            return True
        if txt.startswith("há "):
            try:
                h = int(txt.replace("há ", "").replace(" horas", "").replace(" hora", ""))
                return h <= max_horas
            except Exception:
                return True
        return True

    pontos_filtrados = []
    for p in pontos:
        if filtro_bairro != "Todos" and p.bairro != filtro_bairro:
            continue
        if not within_hours(p.id):
            continue
        pontos_filtrados.append(p)

    # --- Resumo rápido
    colA, colB, colC = st.columns(3)
    with colA:
        st.metric("Pontos exibidos", len(pontos_filtrados))
    with colB:
        urg = sum(1 for n in necessidades if n.status == "URGENTE")
        st.metric("Itens URGENTES (no filtro)", urg)
    with colC:
        st.caption("Dica: clique em um ponto para ver detalhes e copiar lista.")

    st.divider()

    # --- Lista de cards
    for p in pontos_filtrados:
        last_upd = last_update_for_ponto(db_path, p.id)
        itens = by_ponto.get(p.id, [])

        with st.container(border=True):
            top1, top2, top3 = st.columns([2.2, 1.1, 1.2])

            with top1:
                st.markdown(f"### {p.nome}")
                st.caption(f"{p.tipo} • {p.bairro}")
                st.write(f"📍 **Endereço:** {p.endereco}")
                st.write(f"🕒 **Horário:** {p.horario}")

            with top2:
                st.write("**Última atualização**")
                st.write(f"⏰ {human_hours_ago(last_upd)}")
                if last_upd:
                    st.caption(last_upd.replace("T", " ").replace("+", " +"))

            with top3:
                maps = google_maps_url(p.endereco)
                st.link_button("🗺️ Abrir no mapa", maps, use_container_width=True)

                wa = whatsapp_url(p.contato_whats, text="Olá! Estou conferindo as necessidades do ponto. Pode confirmar o que está precisando agora?")
                if wa:
                    st.link_button("💬 WhatsApp", wa, use_container_width=True)
                else:
                    st.button("💬 WhatsApp", disabled=True, use_container_width=True)

            st.divider()

            if not itens:
                st.info("Sem itens neste filtro para este ponto.")
            else:
                # separa por status
                urgentes = [n for n in itens if n.status == "URGENTE"]
                precisa = [n for n in itens if n.status == "PRECISA"]
                ok = [n for n in itens if n.status == "OK"]

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown("#### 🔴 URGENTE")
                    for n in urgentes:
                        extra = f" — {n.observacao}" if n.observacao else ""
                        st.write(f"- {n.item}{extra}")
                with c2:
                    st.markdown("#### 🟡 PRECISA")
                    for n in precisa:
                        extra = f" — {n.observacao}" if n.observacao else ""
                        st.write(f"- {n.item}{extra}")
                with c3:
                    st.markdown("#### 🟢 OK (estoque suficiente)")
                    for n in ok:
                        extra = f" — {n.observacao}" if n.observacao else ""
                        st.write(f"- {n.item}{extra}")

                # Copiar lista (só urgente+precisa)
                to_copy = [f"{badge_status(n.status)} • {n.categoria}: {n.item}" for n in (urgentes + precisa)]
                copyable_list(to_copy, title="📋 Copiar lista (URGENTE + PRECISA)")

            # Link interno: "detalhe" usando query param
            st.page_link("pages/1_Pontos.py", label="🔎 Ver detalhe deste ponto (use o seletor acima)", icon="🔎")

    st.divider()

    # --- Seletor de detalhe (simples, sem rota)
    st.markdown("## 🔎 Detalhe de um ponto")
    ponto_map = {f"{p.nome} — {p.bairro}": p.id for p in pontos}
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
        return

    st.markdown("#### Itens cadastrados")
    for n in det_nec:
        extra = f" — {n.observacao}" if n.observacao else ""
        st.write(f"- {badge_status(n.status)} • **{n.categoria}**: {n.item}{extra} _(atualizado: {n.updated_at})_")

if __name__ == "__main__":
    main()