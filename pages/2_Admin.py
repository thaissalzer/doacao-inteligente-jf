import streamlit as st

from src.auth import login_widget, is_admin_logged_in
from src.db import (
    ensure_db,
    Ponto,
    list_pontos,
    upsert_ponto,
    add_necessidade,
    set_ponto_ativo,
)
from scripts.import_pontos_oficiais import main as import_oficiais


def main() -> None:
    st.set_page_config(
        page_title="Admin • Doação Inteligente JF",
        page_icon="🔐",
        layout="wide",
    )

    db_path = "data/doacao.db"

    # ✅ Sempre garante banco + tabelas (Cloud pode abrir direto esta página)
    ensure_db(db_path)

    # ✅ Garante pontos oficiais (upsert: não duplica)
    # Se der algum erro inesperado, não derruba a área admin
    try:
        import_oficiais()
    except Exception as e:
        st.warning(f"Não foi possível importar pontos oficiais agora: {e}")

    st.title("🔐 Área Admin")
    st.caption("Acesso restrito para cadastrar pontos e atualizar necessidades.")

    login_widget()
    if not is_admin_logged_in():
        st.stop()

    st.divider()

    tab1, tab2, tab3 = st.tabs(
        ["➕ Cadastrar/Editar ponto", "📝 Atualizar necessidades", "⚙️ Ativar/Desativar ponto"]
    )

    # ------------------- TAB 1 -------------------
    with tab1:
        st.markdown("### ➕ Cadastrar/Editar ponto")
        st.info("Use um ID simples (ex: `ponto_centro_1`). Se já existir, será atualizado.")

        col1, col2 = st.columns(2)
        with col1:
            ponto_id = st.text_input("ID do ponto", placeholder="ponto_centro_1")
            nome = st.text_input("Nome do ponto", placeholder="Ponto Centro")
            tipo = st.selectbox("Tipo", ["Ponto de arrecadação", "Abrigo"])
            bairro = st.text_input("Bairro/Região", placeholder="Centro")
        with col2:
            endereco = st.text_input("Endereço", placeholder="Rua X, 123")
            horario = st.text_input("Horário", placeholder="09:00–18:00")
            contato_nome = st.text_input("Nome do contato", placeholder="Maria")
            contato_whats = st.text_input("WhatsApp (com DDD)", placeholder="32999990000")

        ativo = st.checkbox("Ativo", value=True)

        if st.button("Salvar ponto", use_container_width=True):
            if not ponto_id.strip() or not nome.strip():
                st.error("ID e Nome são obrigatórios.")
            else:
                ponto = Ponto(
                    id=ponto_id.strip(),
                    nome=nome.strip(),
                    tipo=tipo,
                    bairro=bairro.strip() or "—",
                    endereco=endereco.strip() or "—",
                    horario=horario.strip() or "—",
                    contato_nome=contato_nome.strip() or "—",
                    contato_whats=contato_whats.strip() or "",
                    ativo=1 if ativo else 0,
                )
                upsert_ponto(db_path, ponto)
                st.success("Ponto salvo/atualizado com sucesso.")

    # ------------------- TAB 2 -------------------
    with tab2:
        st.markdown("### 📝 Atualizar necessidades de um ponto")

        pontos = list_pontos(db_path, only_active=False)
        if not pontos:
            st.warning("Nenhum ponto cadastrado.")
        else:
            rotulos = [f"{p.nome} — {p.bairro} ({'Ativo' if p.ativo else 'Inativo'})" for p in pontos]
            idx = st.selectbox(
                "Escolha o ponto",
                list(range(len(rotulos))),
                format_func=lambda i: rotulos[i],
            )
            ponto = pontos[idx]

            colA, colB = st.columns(2)
            with colA:
                categoria = st.selectbox(
                    "Categoria",
                    ["Água", "Alimentos", "Higiene", "Limpeza", "Roupas", "Fraldas", "Outros"],
                )
                item = st.text_input("Item", placeholder="Ex: Água mineral 1,5L")
            with colB:
                status = st.selectbox("Status", ["URGENTE", "PRECISA", "OK"])
                updated_by = st.text_input("Quem atualizou (opcional)", placeholder="Equipe/Voluntário")

            observacao = st.text_input("Observação (opcional)", placeholder="Ex: Somente embalado / sem roupas usadas")

            if st.button("Adicionar atualização", use_container_width=True):
                if not item.strip():
                    st.error("O campo Item é obrigatório.")
                else:
                    add_necessidade(
                        db_path=db_path,
                        ponto_id=ponto.id,
                        categoria=categoria,
                        item=item.strip(),
                        status=status,
                        observacao=observacao.strip(),
                        updated_by=updated_by.strip(),
                    )
                    st.success("Atualização registrada! (aparece imediatamente na página pública)")

    # ------------------- TAB 3 -------------------
    with tab3:
        st.markdown("### ⚙️ Ativar/Desativar ponto")

        pontos = list_pontos(db_path, only_active=False)
        if not pontos:
            st.warning("Nenhum ponto cadastrado.")
        else:
            for p in pontos:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2.5, 1, 1])
                    with c1:
                        st.markdown(f"**{p.nome}**")
                        st.caption(f"{p.tipo} • {p.bairro} • ID: {p.id}")
                    with c2:
                        st.write("Status")
                        st.write("✅ Ativo" if p.ativo else "⛔ Inativo")
                    with c3:
                        if p.ativo:
                            if st.button("Desativar", key=f"off_{p.id}", use_container_width=True):
                                set_ponto_ativo(db_path, p.id, False)
                                st.rerun()
                        else:
                            if st.button("Ativar", key=f"on_{p.id}", use_container_width=True):
                                set_ponto_ativo(db_path, p.id, True)
                                st.rerun()


main()