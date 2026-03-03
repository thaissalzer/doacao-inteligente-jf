from __future__ import annotations

import re
import unicodedata
from typing import Tuple

from src.db import (
    Ponto,
    ensure_db,
    insert_ponto_if_missing,
    list_existing_ponto_ids,
    resolve_db_path,
)

DB_PATH = resolve_db_path()

RAW = """
Prédio Sede da PJF – Av. Brasil, 2001 – térreo
Casa da Mulher – Av. Garibaldi Campinhos, 169 – Vitorino Braga
Escola Municipal Murilo Mendes – Rua Dr. Leonel Jaguaribe, 240 – Alto Grajaú
Escola Municipal Professor Nilo Camilo Ayupe – Rua Almirante Barroso, 155 – Paineiras
Shopping Jardim Norte – Av. Brasil, 6345 – Mariano Procópio
Unimed Juiz de Fora – Av. Rio Branco, 2540
Emcasa – Av. Sete de Setembro, 975 – Costa Carvalho
IF Sudeste MG – Rua Bernardo Mascarenhas, 1283 – Bairro Fábrica
Escola Municipal Paulo Rogério dos Santos – Rua Cel. Quintão, 136 – Monte Castelo
Supermercados Bahamas – todas as lojas
Sindicato dos Bancários – Rua Batista de Oliveira, 745
Igreja Metodista em Bela Aurora – Rua Dr. Costa Reis, 380 – Ipiranga
UniAcademia – Rua Halfeld, 1.179 – Centro
Independência Shopping – Av. Presidente Itamar Franco, 3600 – Cascatinha
AACI – Rua Doutor Dias da Cruz, 487 – Nova Era
Secretaria Especial de Igualdade Racial – Av. Rio Branco, 2234 – Centro
Loja Maçônica – Rua Cândido Tostes, 212 – São Mateus
Mister Shopping – Rua Mr. Moore, 70 – Centro
Souza Gomes Imóveis – Av. Presidente Itamar Franco, 2.800 – São Mateus
Trade Hotel – Av. Presidente Itamar Franco, 3800 – Cascatinha
Shopping Alameda - R. Morais e Castro, 300 - Passos, Juiz de Fora - MG
Salvaterra Restaurante - Avenida Deusdedith Salgado, 4735, Salvaterra
Praça de pedágio de Simão Pereira, km 819, BR-040
Sesc Mesa Brasil - Rua Carlos Chagas, 100, São Mateus

Escola Municipal Raymundo Hargreaves - Rua Luiz Fávero, 383, Bom Jardim
Escola Municipal Amélia Pires - Rua Itatiaia, 570, Monte Castelo
Escola Municipal Aurea Bicalho - Rua Odilon Braga, nº 119 - Linhares
Escola Municipal Dante Jaime Brochado - Rua Francisco Fontainha, 163, Santo Antônio
Escola Municipal Gabriel Gonçalves - Rua Gabriel Coimbra, nº 240, Ipiranga
Escola Municipal Belmira Duarte - Rua Adailton Garcia, nº 110, Bairro JK
Escola Estadual Padre Frederico - Rua Carlos Alves, 133, Bonfim
Escola Municipal Paulo Rogério - Rua Coronel Quintão, nº 136, Monte Castelo
Escola Municipal Henrique José de Souza - Rua Cidade do Sol, nº 370, Cidade do Sol
Escola Municipal Marlene Barros - Prolongamento da Rua Marumbi, nº 56 - Marumbi
Escola Municipal Adhemar Rezende - Av. Senhor dos Passos, 1596, São Pedro
Escola Municipal Professor Nilo Camilo Ayupe - R. Alm. Barroso, 155 - Paineiras
Escola Municipal Fernão Dias - Rua Gustavo Fernandes Barbosa, nº 155 - Bandeirantes
Escola Municipal Dilermando Cruz - Rua Dr. Altivo Halfeld, nº 44 - Vila Ideal
Escola Municipal Irineu Guimarães - Rua José Zacarias dos Santos, s/nº - São Benedito
Escola Estadual Antônio Carlos - Av. Cel. Vidal, 180 - Mariano Procópio
Escola Municipal Antônio Carlos Fagundes - Rua Antônio Lopes Júnior, 35 - Francisco Bernardino
Escola Municipal Amélia Mascarenhas - Rua Dr Maurício Guerra, 300, São Bernardo
""".strip()


def slugify(text: str) -> str:
    txt = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    txt = txt.lower()
    txt = re.sub(r"[^a-z0-9]+", "_", txt).strip("_")
    return txt[:48] if len(txt) > 48 else txt


def split_parts(line: str) -> list[str]:
    # normaliza traços
    normalized = line.replace("—", "–")
    # primeiro tenta separar por " – "
    if " – " in normalized:
        parts = [p.strip() for p in normalized.split("–")]
        return [p for p in parts if p]
    # depois tenta por " - "
    if " - " in normalized:
        parts = [p.strip() for p in normalized.split("-")]
        return [p for p in parts if p]
    return [line.strip()]


def clean_bairro(raw_bairro: str) -> str:
    b = raw_bairro.strip()

    # Caso comum: "Passos, Juiz de Fora - MG" -> bairro = "Passos"
    if "," in b:
        first = b.split(",", 1)[0].strip()
        if first:
            return first

    # Se sobrar só UF/cidade/rodovia, trata como "—"
    junk = {"MG", "JUIZ DE FORA", "BR-040", "BR040", "BR 040"}
    if b.upper() in junk:
        return "—"

    return b if b else "—"


def parse_line(line: str) -> Tuple[str, str, str]:
    """
    Retorna (nome, endereco, bairro)
    Regras:
      - "Nome – Endereço – Bairro" -> ok
      - "Nome - Endereço - Bairro, Juiz de Fora - MG" -> pega bairro antes da vírgula
      - "Supermercados Bahamas – todas as lojas" -> bairro "-"
      - "Praça de pedágio de Simão Pereira, km 819, BR-040" -> bairro "Simão Pereira"
    """
    parts = split_parts(line)

    # Caso "Praça de pedágio de Simão Pereira, km..., BR-040"
    if "Simão Pereira" in line and "pedágio" in line.lower():
        return line.strip(), "km 819, BR-040", "Simão Pereira"

    if len(parts) >= 3:
        nome = parts[0].strip()

        # Se tiver mais de 3 partes, o bairro é o ÚLTIMO "pedaço" útil
        # e o endereço vira tudo entre nome e bairro.
        raw_bairro = parts[-1].strip()
        bairro = clean_bairro(raw_bairro)

        endereco_parts = parts[1:-1]
        endereco = " - ".join([p.strip() for p in endereco_parts if p.strip()]) or "—"

        return nome, endereco, bairro

    if len(parts) == 2:
        nome, endereco_or_note = parts[0].strip(), parts[1].strip()

        if re.search(r"(todas\s+as\s+lojas|todas\s+as\s+unidades|todas\s+as\s+agencias)", endereco_or_note, re.I):
            return nome, endereco_or_note, "—"

        return nome, endereco_or_note, "—"

    return line.strip(), "—", "—"


def main() -> None:
    ensure_db(DB_PATH)

    contato_padrao_nome = "Oficial"
    contato_padrao_whats = ""
    horario_padrao = "—"

    linhas = [l.strip() for l in RAW.splitlines() if l.strip()]
    pontos = []
    for line in linhas:
        nome, endereco, bairro = parse_line(line)

        ponto_id = f"oficial_{slugify(nome)}"
        pontos.append(
            Ponto(
                id=ponto_id,
                nome=nome,
                tipo="Ponto de arrecadação",
                bairro=bairro,
                endereco=endereco,
                horario=horario_padrao,
                contato_nome=contato_padrao_nome,
                contato_whats=contato_padrao_whats,
                ativo=1,
            )
        )

    existing_ids = list_existing_ponto_ids(DB_PATH, [p.id for p in pontos])
    novos = [p for p in pontos if p.id not in existing_ids]
    for ponto in novos:
        # Preserva qualquer ajuste feito por administradores no banco local.
        insert_ponto_if_missing(DB_PATH, ponto)

    print(f"Importados/atualizados: {len(novos)} novos pontos oficiais em {DB_PATH}")


if __name__ == "__main__":
    main()
