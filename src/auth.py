from __future__ import annotations

import streamlit as st
import secrets
from typing import Optional


def _get_secret_password() -> Optional[str]:
    # Defina em .streamlit/secrets.toml: ADMIN_PASSWORD="sua_senha"
    return st.secrets.get("ADMIN_PASSWORD", None)


def is_admin_logged_in() -> bool:
    return bool(st.session_state.get("is_admin", False))


def logout() -> None:
    st.session_state["is_admin"] = False


def login_widget() -> None:
    """Renderiza um login simples. Não expõe a senha e usa compare seguro."""
    secret_pw = _get_secret_password()
    if not secret_pw:
        st.warning("Admin desativado: defina ADMIN_PASSWORD em `.streamlit/secrets.toml`.")
        return

    if is_admin_logged_in():
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("Sair", use_container_width=True):
                logout()
                st.rerun()
        with col2:
            st.success("Você está logada como Admin.")
        return

    pw = st.text_input("Senha de Admin", type="password", placeholder="Digite a senha")
    if st.button("Entrar", use_container_width=True):
        if secrets.compare_digest(pw, secret_pw):
            st.session_state["is_admin"] = True
            st.rerun()
        else:
            st.error("Senha incorreta.")