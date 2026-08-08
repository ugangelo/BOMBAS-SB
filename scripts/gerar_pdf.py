from __future__ import annotations

import html
import json
import subprocess
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "BOMBAS-SB-cronograma-2026-2.pdf"
NODE = Path(r"C:\Users\Gabriel\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe")
MESES = {8: "ago", 9: "set", 10: "out", 11: "nov", 12: "dez"}


def carregar_conteudos() -> dict:
    codigo = "global.window={}; require('./conteudos.js'); process.stdout.write(JSON.stringify(window.conteudosAulas));"
    resultado = subprocess.run(
        [str(NODE), "-e", codigo], cwd=ROOT, check=True,
        capture_output=True, text=True, encoding="utf-8",
    )
    return json.loads(resultado.stdout)


def data_curta(data_iso: str) -> str:
    data = datetime.strptime(data_iso, "%Y-%m-%d")
    return f"{data.day:02d}/{MESES[data.month]}"


def detalhes(conteudo: dict) -> str:
    linhas = []
    if conteudo.get("resumo"):
        linhas.append(html.escape(conteudo["resumo"]))
    for item in conteudo.get("itens", []):
        assunto = html.escape(item.get("topico") or item.get("conteudo") or "")
        referencia = html.escape(item.get("referencia") or item.get("pagina") or "")
        linhas.append(f"{assunto} ({referencia})" if referencia else assunto)
    return "<br/>".join(linhas)


def tipo(conteudo: dict) -> str:
    if conteudo.get("laboratorio"):
        return "LAB"
    if (conteudo.get("titulo") or "").upper().startswith("AA"):
        return "AVALIAÇÃO"
    return "TEORIA"


def gerar_pdf() -> None:
    conteudos = sorted(carregar_conteudos().items())
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    estilos = getSampleStyleSheet()
    vermelho = colors.HexColor("#C90016")
    vinho = colors.HexColor("#650014")
    rosa = colors.HexColor("#FFF0F2")
    amarelo = colors.HexColor("#FFF4CE")
    cinza = colors.HexColor("#F6F3F4")
    borda = colors.HexColor("#D9C7CB")

    estilos.add(ParagraphStyle(
        name="CapaTitulo", parent=estilos["Title"], fontName="Helvetica-Bold",
        fontSize=26, leading=31, textColor=vinho, alignment=TA_CENTER, spaceAfter=6 * mm,
    ))
    estilos.add(ParagraphStyle(
        name="Secao", parent=estilos["Heading1"], fontName="Helvetica-Bold",
        fontSize=17, leading=21, textColor=vinho, spaceAfter=3 * mm,
    ))
    estilos.add(ParagraphStyle(name="Celula", parent=estilos["BodyText"], fontSize=7.2, leading=8.7))
    estilos.add(ParagraphStyle(
        name="CelulaTitulo", parent=estilos["Celula"], fontName="Helvetica-Bold", textColor=vinho,
    ))
    estilos.add(ParagraphStyle(
        name="Cabecalho", parent=estilos["CelulaTitulo"], textColor=colors.white, alignment=TA_CENTER,
    ))

    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=landscape(A4), leftMargin=13 * mm, rightMargin=13 * mm,
        topMargin=13 * mm, bottomMargin=13 * mm,
        title="Bombas e Sistemas de Bombeamento - Cronograma 2026/2",
        author="Universidade Presbiteriana Mackenzie",
    )

    historia = [
        Spacer(1, 22 * mm),
        Paragraph("BOMBAS E SISTEMAS DE BOMBEAMENTO", estilos["CapaTitulo"]),
        Paragraph("Calendário da disciplina - 2º semestre de 2026", estilos["Heading2"]),
        Spacer(1, 10 * mm),
    ]
    resumo = [
        [Paragraph("Organização", estilos["Cabecalho"]), Paragraph("Datas", estilos["Cabecalho"])],
        ["Aulas", "Terças e sextas-feiras"],
        ["Semana da Escola de Engenharia", "31/ago a 04/set - sem aulas"],
        ["Provas institucionais", "AVI: 17/set | Avalia: 04/nov"],
        ["Laboratório disponível", "09/out | 30/out | 13/nov"],
        ["Encerramento", "SUB: 30/nov a 05/dez | PAFE: 07 a 12/dez"],
    ]
    tabela_resumo = Table(resumo, colWidths=[72 * mm, 142 * mm])
    tabela_resumo.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), vermelho),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, rosa]),
        ("GRID", (0, 0), (-1, -1), 0.5, borda),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    historia.extend([tabela_resumo, PageBreak(), Paragraph("Cronograma de aulas", estilos["Secao"])])

    linhas = [[
        Paragraph("Data", estilos["Cabecalho"]), Paragraph("Tipo", estilos["Cabecalho"]),
        Paragraph("Aula", estilos["Cabecalho"]), Paragraph("Conteúdos e referências", estilos["Cabecalho"]),
    ]]
    tipos = []
    for data_iso, conteudo in conteudos:
        categoria = tipo(conteudo)
        tipos.append(categoria)
        linhas.append([
            Paragraph(data_curta(data_iso), estilos["CelulaTitulo"]),
            Paragraph(categoria, estilos["CelulaTitulo"]),
            Paragraph(html.escape(conteudo.get("titulo") or "Conteúdo"), estilos["CelulaTitulo"]),
            Paragraph(detalhes(conteudo), estilos["Celula"]),
        ])

    tabela = Table(linhas, colWidths=[18 * mm, 25 * mm, 62 * mm, 164 * mm], repeatRows=1)
    comandos = [
        ("BACKGROUND", (0, 0), (-1, 0), vinho),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, cinza]),
        ("GRID", (0, 0), (-1, -1), 0.4, borda),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for linha, categoria in enumerate(tipos, start=1):
        if categoria == "LAB":
            comandos.append(("BACKGROUND", (0, linha), (-1, linha), amarelo))
        elif categoria == "AVALIAÇÃO":
            comandos.append(("BACKGROUND", (0, linha), (-1, linha), colors.HexColor("#EFD6DC")))
    tabela.setStyle(TableStyle(comandos))
    historia.append(tabela)

    def rodape(canvas, documento):
        canvas.saveState()
        canvas.setStrokeColor(vermelho)
        canvas.setLineWidth(1.4)
        canvas.line(13 * mm, 9 * mm, landscape(A4)[0] - 13 * mm, 9 * mm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(vinho)
        canvas.drawString(13 * mm, 5.5 * mm, "Mackenzie - Bombas e Sistemas de Bombeamento - 2026/2")
        canvas.drawRightString(landscape(A4)[0] - 13 * mm, 5.5 * mm, f"Página {documento.page}")
        canvas.restoreState()

    doc.build(historia, onFirstPage=rodape, onLaterPages=rodape)
    print(OUTPUT)


if __name__ == "__main__":
    gerar_pdf()
