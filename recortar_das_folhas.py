# -*- coding: utf-8 -*-
u"""
============================================================
 RECORTAR AS FIGURAS DAS FOLHAS DE PAPEL — O Espelho e o Contrário (2º ano)

 ⭐ A REGRA QUE MANDA AQUI (Marcos, 14/set/2026): *"procure na internet, nada de
    imagem gerada por IA, utilize das atividades"*. Toda figura deste caderno sai
    de uma das quatro folhas que o crivo (`_sequencias/POTE-SINON2.md`) chamou
    de "mina de figuras":

   · d37 (Mundo Indica) — *"ESCREVA O ANTÔNIMO CORRESPONDENTE"*: quatro pares
     fotográficos do MESMO objeto mudando só a qualidade — sopa quente/fria,
     roupa molhada/seca, janela aberta/fechada, cesto cheio/vazio.
   · d11 (Mundo Indica) — *"LIGUE CADA PALAVRA AO SEU ANTÔNIMO"*: dez medalhões
     coloridos (feliz, grande, bravo, limpo, quente × manso, sujo, triste,
     pequeno, frio).
   · d06 (tudoportugues) — *"Observe as imagens com atenção e ligue cada palavra
     ao seu antônimo"*: cinco pares a traço (solto/preso, grande/pequeno,
     alto/baixo, ensolarado/nublado, preto/branco).
   · d31 (SOS Professor) — *"Escreva os antônimos"*: oito cenas em par (rato
     alegre/triste, porco sujo/limpo, sol/lua, acordado/dormindo). Os prédios
     alto/baixo e a moto/bicicleta ficaram de fora: dividem a mesma linha de
     chão com o vizinho e saem grudados um no outro.

 ⚠️ AS CAIXAS FORAM MEDIDAS, NÃO CHUTADAS: saem de uma varredura de ILHAS DE
    TINTA em cada folha (`scipy.ndimage.label` sobre os pixels escuros, com
    dilatação para juntar os pedaços do mesmo desenho), impressa e lida antes
    de dar nome a cada uma. Onde a ilha veio grudada ao rótulo ou à moldura, a
    peça `so_o_desenho` fica só com a maior mancha de tinta densa — o rótulo é
    uma mancha pequena e a moldura é oca.

 ⚠️ E O NOME TEM DE BATER COM O DESENHO. Trocar um nome aqui não dá erro nenhum:
    só faz a criança ver um gato preto onde a palavra diz BRANCO. Conferir
    OLHANDO a folha de contato (a 300 px, que é onde o defeito existiria).

 Uso:  python3 _sinon2/recortar_das_folhas.py
============================================================
"""
from __future__ import print_function

import io
import json
import os
import sys
from collections import deque

try:
    from PIL import Image
    import numpy as np
except ImportError as e:                                   # pragma: no cover
    print(u"preciso de Pillow+numpy (%s)" % e)
    sys.exit(2)

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
FOLHAS = os.path.join(RAIZ, u"_sequencias", u"folhas_sinon2")
DEST = os.path.join(AQUI, u"img")
PREFIXO = u"ec_"

LIM_AGUA = 210
FADE_LO = 210.0
FADE_HI = 226.0
LIM = 200
FOLGA = 4
MAIOR = 300        # a régua de resolução do leiaute_mao reprova figura ampliada
                   # acima de 1,35x; guardar em 300 px evita o borrão nas telas
                   # onde ela aparece grande (a folha 1 mostra o par lado a lado)

# ---------------------------------------------------------------------------
# AS CAIXAS, MEDIDAS NA IMAGEM (y1, x1, y2, x2) — impressas pela varredura
# ---------------------------------------------------------------------------
# d37 (743 x 1050): os quatro pares fotográficos, uma ilha por foto
D37 = {u"arquivo": u"d37_c8d95d.jpg", u"caixas": [
    (u"sopa_quente",   (234, 70, 357, 186)),
    (u"sopa_fria",     (260, 306, 357, 423)),
    (u"roupa_molhada", (420, 72, 515, 207)),
    (u"roupa_seca",    (409, 304, 514, 429)),
    (u"janela_aberta", (584, 72, 717, 207)),
    (u"janela_fechada", (584, 314, 717, 439)),
    (u"cesto_cheio",   (798, 75, 918, 204)),
    (u"cesto_vazio",   (818, 302, 915, 451)),
]}
# d11 (743 x 1050): os dez medalhões. As fileiras saíram da varredura dos anéis
# da coluna esquerda (200-363, 366-528, 532-694, 699-860 e o quinto em
# 865-1027); a coluna direita tem o mesmo raio, centrada em x=645. O anel é
# uma moldura OCA e o rótulo é pequeno: os dois saem no `so_o_desenho`.
_LIN11 = [(200, 363), (366, 528), (532, 694), (699, 860), (865, 1027)]
D11 = {u"arquivo": u"d11_76ccc0.jpg", u"circulo": True, u"caixas":
       [(n, (y1, 35, y2, 197)) for n, (y1, y2) in zip(
           [u"feliz", u"grande", u"bravo", u"limpo", u"quente"], _LIN11)] +
       [(n, (y1, 565, y2, 727)) for n, (y1, y2) in zip(
           [u"manso", u"sujo", u"triste", u"pequeno", u"frio"], _LIN11)]}
# d06 (1810 x 2560): cinco pares a traço. A coluna esquerda veio ilha a ilha da
# varredura (com o rótulo grudado, que o `so_o_desenho` tira). A coluna direita
# veio grudada à linha divisória da folha; as caixas dela são as da varredura
# fina (preso, nublado, baixo) e, para o pato pequeno e o gato branco, a área
# entre os vizinhos medidos (abaixo do enunciado, acima do próximo desenho).
# ⚠️ TRAÇO FINO: aqui o `so_o_desenho` NÃO entra — o gato branco é só contorno,
#    tem densidade baixa, e a peça ficou com a palavra "Branco" e jogou o gato
#    fora (visto na folha de contato, 18/set). Em vez disso as caixas param
#    ACIMA da caixinha do rótulo, que foi medida na varredura fina.
D06 = {u"arquivo": u"d06_f717e7.jpg", u"traco": True, u"caixas": [
    (u"solto",      (556, 123, 718, 352)),
    (u"pequeno_pato", (545, 660, 715, 880)),
    (u"grande_pato", (842, 101, 1110, 376)),
    (u"preso",      (834, 664, 1102, 877)),
    (u"alto_cao",   (1209, 123, 1565, 368)),
    (u"nublado",    (1262, 627, 1492, 851)),
    (u"ensolarado", (1659, 112, 1960, 443)),
    (u"baixo_cao",  (1689, 674, 1925, 823)),
    (u"preto",      (2111, 106, 2322, 379)),
    (u"branco",     (2120, 640, 2335, 880)),
]}
# d31 (1132 x 1600): as cenas que a varredura devolveu SEPARADAS.
# ⚠️ A CAIXINHA DE ESCREVER ENCOSTA NO DESENHO em todas as oito cenas (vista na
#    folha de contato, 18/set): virou UMA ilha com ele e a régua de interior não
#    a pegou. Então a caixa é medida e APAGADA antes do recorte (`apaga`), ou a
#    cena para acima dela quando ela fica inteira embaixo.
D31 = {u"arquivo": u"d31_c79010.png", u"caixas": [
    (u"rato_alegre", (375, 557, 586, 848)),
    (u"rato_triste", (247, 838, 450, 1091)),
    (u"porco_sujo",  (650, 33, 785, 457)),
    (u"sol",         (662, 475, 838, 828)),
    (u"lua",         (557, 866, 722, 1076)),
    (u"porco_limpo", (864, 69, 1030, 340)),
    (u"acordado",    (835, 394, 1101, 760)),
    (u"dormindo",    (807, 755, 1087, 1072)),
], u"apaga": {
    u"sol": [(718, 555, 812, 830)],
    u"acordado": [(1028, 394, 1101, 665)],
    u"dormindo": [(1025, 790, 1090, 1072)],
}}
GRUPOS = [D37, D11, D06, D31]

SELOS = ((u"ec_trofeu.png", u"banco:trofeu"),
         (u"ec_selo.png", u"banco:selo"),
         (u"ec_selo_off.png", u"banco:selo"))


def papel_de(px, x, y):
    r, g, b, al = px[x, y]
    return al < 16 or (r >= LIM_AGUA and g >= LIM_AGUA and b >= LIM_AGUA)


def limpa_fundo(c):
    u"""Fundo transparente por vizinhança, entrando pelas bordas, com degradê
    (cópia do `_subst5/recortar_das_folhas.py`, que já passou pela banca)."""
    w, h = c.size
    px = c.load()
    vis = [[False] * h for _ in range(w)]
    fila = deque()
    for x in range(w):
        for y in (0, h - 1):
            if papel_de(px, x, y) and not vis[x][y]:
                vis[x][y] = True
                fila.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if papel_de(px, x, y) and not vis[x][y]:
                vis[x][y] = True
                fila.append((x, y))
    while fila:
        x, y = fila.popleft()
        r, g, b, al = px[x, y]
        if al:
            claro = (min(r, g, b) - FADE_LO) / (FADE_HI - FADE_LO)
            px[x, y] = (r, g, b, int(al * (1.0 - max(0.0, min(1.0, claro)))))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not vis[nx][ny] and papel_de(px, nx, ny):
                vis[nx][ny] = True
                fila.append((nx, ny))
    return c


def aperta(c):
    a = np.asarray(c.convert(u"RGB")).astype(np.int16)
    ys, xs = np.where(a.min(axis=2) < LIM)
    if not len(xs):
        return None
    x1, x2 = max(0, xs.min() - FOLGA), min(c.width, xs.max() + 1 + FOLGA)
    y1, y2 = max(0, ys.min() - FOLGA), min(c.height, ys.max() + 1 + FOLGA)
    return c.crop((int(x1), int(y1), int(x2), int(y2)))


def tira_fantasma(c):
    a = np.asarray(c.convert(u"RGBA"))
    op = a[:, :, 3] > 40
    h, w = op.shape
    y1, y2, x1, x2 = 0, h, 0, w
    for _ in range(4):
        if y2 - y1 > 4 and op[y1, x1:x2].mean() > 0.8 and op[y1 + 1, x1:x2].mean() < 0.3:
            y1 += 1
        if y2 - y1 > 4 and op[y2 - 1, x1:x2].mean() > 0.8 and op[y2 - 2, x1:x2].mean() < 0.3:
            y2 -= 1
        if x2 - x1 > 4 and op[y1:y2, x1].mean() > 0.8 and op[y1:y2, x1 + 1].mean() < 0.3:
            x1 += 1
        if x2 - x1 > 4 and op[y1:y2, x2 - 1].mean() > 0.8 and op[y1:y2, x2 - 2].mean() < 0.3:
            x2 -= 1
    if (y1, y2, x1, x2) == (0, h, 0, w):
        return c
    return c.crop((x1, y1, x2, y2))


def so_o_desenho(c, guarda=0.09):
    u"""Fica só com as ILHAS DE TINTA densas do desenho (cópia do `_subst5`):
    o rótulo é uma mancha pequena e separada; o anel do medalhão e a caixinha
    do rótulo são retângulos/anéis OCOS (densidade abaixo de 12%) e saem."""
    a = np.array(c.convert(u"RGBA"))
    tinta = (a[:, :, 3] > 40) & (a[:, :, :3].min(axis=2) < 235)
    h, w = tinta.shape
    dono = np.zeros((h, w), dtype=np.int32)
    areas, cx, n = [0], [None], 0
    for y0 in range(h):
        for x0 in range(w):
            if not tinta[y0, x0] or dono[y0, x0]:
                continue
            n += 1
            fila = deque([(y0, x0)])
            dono[y0, x0] = n
            area = 0
            x1 = x2 = x0
            y1 = y2 = y0
            while fila:
                y, x = fila.popleft()
                area += 1
                if x < x1: x1 = x
                if x > x2: x2 = x
                if y < y1: y1 = y
                if y > y2: y2 = y
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1),
                               (1, 1), (1, -1), (-1, 1), (-1, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and tinta[ny, nx] and not dono[ny, nx]:
                        dono[ny, nx] = n
                        fila.append((ny, nx))
            areas.append(area)
            cx.append((x1, y1, x2, y2))
    if n < 2:
        return c

    def densa(i):
        x1, y1, x2, y2 = cx[i]
        return areas[i] / float(max(1, (x2 - x1 + 1) * (y2 - y1 + 1))) >= 0.12
    maior = max((i for i in range(1, n + 1) if densa(i)),
                key=lambda i: areas[i], default=None)
    if maior is None:
        return c
    fica = [i for i in range(1, n + 1)
            if areas[i] >= areas[maior] * guarda and densa(i)]
    a[:, :, 3] = np.where(np.isin(dono, fica), a[:, :, 3], 0)
    saida = Image.fromarray(a)
    bb = saida.getbbox()
    return saida.crop(bb) if bb else saida


def tira_caixas_ocas(c, minimo=0.02, interior=0.06):
    u"""Apaga a CAIXINHA DO RÓTULO (retângulo oco) que veio grudada na cena.

    ⚠️ Vista na folha de contato (18/set/2026): nas oito cenas da d31 a caixa de
       escrever ficou pendurada embaixo do desenho — e a régua de densidade do
       `so_o_desenho` não a pegou, porque a borda é grossa. A régua certa é a de
       INTERIOR: um retângulo oco tem a borda cheia e o miolo vazio; um desenho
       tem tinta por dentro. Componente grande cujo miolo (a caixa envolvente
       encolhida em 8%) tem menos de 6% de tinta é caixa, e sai."""
    a = np.array(c.convert(u"RGBA"))
    tinta = (a[:, :, 3] > 40) & (a[:, :, :3].min(axis=2) < 235)
    from scipy import ndimage as nd
    lab, n = nd.label(tinta, structure=np.ones((3, 3)))
    if n < 2:
        return c
    h, w = tinta.shape
    for i, sl in enumerate(nd.find_objects(lab), start=1):
        y1, y2, x1, x2 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        if (y2 - y1) * (x2 - x1) < minimo * h * w:
            continue
        my, mx = int((y2 - y1) * 0.08) + 2, int((x2 - x1) * 0.08) + 2
        miolo = tinta[y1 + my:y2 - my, x1 + mx:x2 - mx]
        if miolo.size and miolo.mean() < interior:
            a[:, :, 3] = np.where(lab == i, 0, a[:, :, 3])
    saida = Image.fromarray(a)
    bb = saida.getbbox()
    return saida.crop(bb) if bb else saida


def tira_risco_no_pe(c, faixa=14):
    u"""Tira o RISCO horizontal fino que sobra no pé (ou no topo) da figura: é a
    borda de cima da caixinha de escrever, que a caixa medida cortou pela
    metade. Regra: nas últimas `faixa` linhas, uma fileira com tinta em mais de
    35% da largura, tendo logo acima uma fileira quase vazia, é risco — e a
    figura passa a terminar acima dele. Medido nas cenas da d31 (18/set)."""
    a = np.asarray(c.convert(u"RGBA"))
    op = (a[:, :, 3] > 40) & (a[:, :, :3].min(axis=2) < 200)
    h, w = op.shape
    corte = None
    for y in range(h - 1, max(h - faixa, 3), -1):
        if op[y].mean() > 0.35 and op[y - 3:y - 1].mean() < 0.08:
            corte = y - 3
    if corte is not None and corte > h * 0.4:
        c = c.crop((0, 0, w, corte))
    a = np.asarray(c.convert(u"RGBA"))
    op = (a[:, :, 3] > 40) & (a[:, :, :3].min(axis=2) < 200)
    h, w = op.shape
    corte = None
    for y in range(0, min(faixa, h - 4)):
        if op[y].mean() > 0.35 and op[y + 2:y + 4].mean() < 0.08:
            corte = y + 3
    if corte is not None and corte < h * 0.6:
        c = c.crop((0, corte, w, h))
    bb = c.getbbox()
    return c.crop(bb) if bb else c


def mascara_circular(c, folga=6):
    u"""Só o miolo do medalhão: o anel impresso fica fora do círculo."""
    w, h = c.size
    r = min(w, h) / 2.0 - folga
    cx, cy = w / 2.0, h / 2.0
    a = np.array(c.convert(u"RGBA"))
    yy, xx = np.mgrid[0:h, 0:w]
    fora = (xx - cx) ** 2 + (yy - cy) ** 2 > r * r
    a[:, :, 3] = np.where(fora, 0, a[:, :, 3])
    a[:, :, :3] = np.where(fora[:, :, None], 255, a[:, :, :3])
    return Image.fromarray(a)


def main():
    if not os.path.isdir(DEST):
        os.makedirs(DEST)
    origem, feitas = {}, []
    for G in GRUPOS:
        cam = os.path.join(FOLHAS, G[u"arquivo"])
        if not os.path.exists(cam):
            print(u"  ! nao achei %s" % cam)
            continue
        base = Image.open(cam).convert(u"RGBA")
        marca = G[u"arquivo"].split(u"_")[0]
        for nome, (y1, x1, y2, x2) in G[u"caixas"]:
            cx = base.crop((x1, y1, x2, y2))
            for (ay1, ax1, ay2, ax2) in G.get(u"apaga", {}).get(nome, []):
                # a caixinha do rótulo, medida, vira papel branco antes do corte
                cx.paste((255, 255, 255, 255), (max(0, ax1 - x1), max(0, ay1 - y1),
                                                min(cx.width, ax2 - x1), min(cx.height, ay2 - y1)))
            if G.get(u"circulo"):
                cx = mascara_circular(cx)
            cx = aperta(cx)
            if cx is None:
                print(u"  ! %s: caixa vazia" % nome)
                continue
            cx = limpa_fundo(cx)
            bb = cx.getbbox()
            if bb:
                cx = cx.crop(bb)
            cx = tira_fantasma(cx)
            cx = tira_risco_no_pe(cx)
            if not G.get(u"traco"):
                cx = tira_caixas_ocas(cx)
                cx = so_o_desenho(cx)
            cx = tira_risco_no_pe(cx)
            if max(cx.size) > MAIOR:
                k = MAIOR / float(max(cx.size))
                cx = cx.resize((max(1, int(cx.width * k)), max(1, int(cx.height * k))),
                               Image.LANCZOS)
            arq = u"%s%s.png" % (PREFIXO, nome)
            cx.save(os.path.join(DEST, arq), optimize=True)
            origem[arq] = u"folha:%s — recortada da propria folha" % marca
            feitas.append((nome, cx))
            print(u"  ok %-14s %3dx%3d   (%s)" % (nome, cx.width, cx.height, marca))

    for selo, de in SELOS:
        if os.path.exists(os.path.join(DEST, selo)):
            origem[selo] = de
    with io.open(os.path.join(DEST, u"ORIGEM.json"), u"w", encoding=u"utf-8") as f:
        f.write(json.dumps(origem, indent=1, sort_keys=True, ensure_ascii=False))

    # a folha de conferência é para OLHAR, a 300 px (regra 5 da REGRA ZERO)
    larg, alt, porlin = 320, 340, 6
    linhas = (len(feitas) + porlin - 1) // porlin
    fl = Image.new(u"RGB", (larg * porlin, alt * max(1, linhas)), u"#f6f2e6")
    from PIL import ImageDraw
    dr = ImageDraw.Draw(fl)
    for i, (nome, c) in enumerate(feitas):
        d = c.copy()
        d.thumbnail((300, 300))
        x, y = (i % porlin) * larg + 10, (i // porlin) * alt + 8
        fl.paste(d, (x, y), d)
        dr.text((x, y + 312), nome, fill=(40, 40, 40))
    fl.save(u"/tmp/conferir_sinon2.png")
    print(u"\n%d figuras. folha de conferencia: /tmp/conferir_sinon2.png "
          u"(OLHAR, nao confiar)" % len(feitas))
    return 0


if __name__ == u"__main__":
    sys.exit(main())
