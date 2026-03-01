from __future__ import annotations

from datetime import datetime
from typing import Optional

import streamlit as st

from src.db import ISO_FMT


def badge_status(status: str) -> str:
    s = (status or "").upper().strip()
    if s == "URGENTE":
        return "🔴 URGENTE"
    if s == "PRECISA":
        return "🟡 PRECISA"
    return "🟢 OK"


def parse_iso(dt: str) -> Optional[datetime]:
    try:
        return datetime.strptime(dt, ISO_FMT)
    except Exception:
        return None


def human_hours_ago(updated_at_iso: Optional[str]) -> str:
    if not updated_at_iso:
        return "sem atualização registrada"
    dt = parse_iso(updated_at_iso)
    if not dt:
        return "data inválida"
    delta = datetime.now(dt.tzinfo) - dt
    hours = int(delta.total_seconds() // 3600)
    if hours <= 0:
        return "agora há pouco"
    if hours == 1:
        return "há 1 hora"
    return f"há {hours} horas"


def google_maps_url(address: str) -> str:
    # Link simples sem geocodificação
    q = address.replace(" ", "+")
    return f"https://www.google.com/maps/search/?api=1&query={q}"


def whatsapp_url(phone: str, text: str = "") -> Optional[str]:
    digits = "".join([c for c in phone if c.isdigit()])
    if not digits:
        return None
    msg = text.replace(" ", "%20")
    return f"https://wa.me/{digits}?text={msg}"


def point_card_header(nome: str, tipo: str, bairro: str) -> None:
    st.markdown(f"### {nome}")
    st.caption(f"{tipo} • {bairro}")


def copyable_list(items: list[str], title: str = "Copiar lista") -> None:
    if not items:
        st.info("Sem itens para listar.")
        return
    text = "\n".join([f"- {i}" for i in items])
    st.text_area(title, value=text, height=140)