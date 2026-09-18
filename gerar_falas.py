# -*- coding: utf-8 -*-
u"""
============================================================
 ESQUELETO — gerador das falas da folha viva

 ⚠️ REGRA DA CASA: o `falas.json` é a VERDADE. Texto escrito aqui = voz gravada.
    Texto mudou = voz regravada (o `entregar.yml` compara o carimbo sha1). É isto
    que acaba com "a tela diz uma coisa e a voz diz outra" — e atividade sem
    `falas.json` NÃO TEM COMO SER CONFERIDA, porque mp3 não se lê.

 ⚠️ UMA FONTE SÓ. As palavras, as frases e os textos moram no bloco
    `/*DADOS-INI*/` do `index.html` e são LIDOS daqui. Nada de segunda lista
    para desencontrar: já custou caro nesta casa um relatório sair zero com a
    folha inteira respondida.

 ⚠️ TODA TELA É NARRADA, e o alto-falante entra também em CADA RESPOSTA que a
    criança toca. Regra do Marcos: *"o alto-falante nas respostas também, para
    ajudar os alunos que não sabem ler"*. Sem isso a criança que ainda soletra
    escolhe pelo tamanho da palavra e a folha vira sorteio.

 ⚠️ A DICA NUNCA DIZ A RESPOSTA. Ela manda olhar uma pista, ou faz outra
    pergunta. Responder no segundo erro não é ajudar: é tirar da criança a única
    chance de pensar de novo.

 ⚠️ PALAVRAS QUE A VOZ ERRA (medido, e o portão `_qa/falas.py` reprova):
    "complete" vira "complite" — usar "preencha". Letra solta ("som S") sai como
    o NOME da letra: ancorar num exemplo ("o som de SAPO").

 Uso:  python3 <pasta>/gerar_falas.py
 Saída: reescreve os blocos FALAS e VOZOK do index.html, o `falas.json` e o
        `voz.txt`.
============================================================
"""
from __future__ import print_function

import collections
import io
import json
import os
import re
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
CAM = os.path.join(AQUI, u"index.html")
PREFIXO = u"ec_"                     # <- o prefixo desta atividade
VOZ = u"pt-BR-AntonioNeural"

D = io.open(CAM, encoding=u"utf-8").read()


def bloco(nome):
    u"""Lê um objeto do bloco DADOS do index.html. Uma fonte só.

    ⚠️ ELE CONTA AS CHAVES, e isso foi conserto de 15/set/2026. O esqueleto
       procurava o fim do objeto por uma marca de texto (`\n});`) — e QUALQUER
       objeto que não terminasse exatamente assim fazia a leitura passar
       adiante e engolir o bloco seguinte. No primeiro caderno do 2º ano os
       vinte e três blocos falharam de uma vez, todos com o mesmo erro, e a
       mensagem do json não dizia nada sobre a causa. Contar chave por chave
       (pulando as que estão DENTRO de texto) acha o fim de qualquer objeto.
    """
    i = D.find(u"var " + nome + u" = ")
    if i < 0:
        raise SystemExit(u"nao achei o bloco `var %s` no index.html" % nome)
    i = D.index(u"{", i)
    nivel, j, dentro, escapa = 0, i, False, False
    while j < len(D):
        c = D[j]
        if dentro:
            if escapa:
                escapa = False
            elif c == u"\\":
                escapa = True
            elif c == u'"':
                dentro = False
        else:
            if c == u'"':
                dentro = True
            elif c == u"{":
                nivel += 1
            elif c == u"}":
                nivel -= 1
                if nivel == 0:
                    j += 1
                    break
        j += 1
    txt = D[i:j]
    txt = re.sub(r"/\*.*?\*/", "", txt, flags=re.S)
    txt = re.sub(r'"\s*\+\s*\n\s*"', "", txt)                 # junta "a" + "b"
    txt = re.sub(r'([\{,]\s*)"?([A-Za-zÀ-ÿ_0-9]+)"?\s*:', r'\1"\2":', txt)
    txt = re.sub(r",(\s*[\}\]])", r"\1", txt)
    return json.loads(txt)


# ⚠️⚠️ A ENTIDADE HTML TAMBÉM É MARCAÇÃO, e isto foi lição paga (15/set/2026,
#    caderno de inglês do 8º ano). O `lp` tirava as TAGS e deixava as
#    ENTIDADES, então a lista de ingredientes da pizza — escrita com `&middot;`
#    para virar o ponto que separa os itens — ia para a fila de gravação como
#    *"Oil and middot Tomato sauce and middot Some onions"*. O portão
#    `_qa/revisor.py` pegou; se não pegasse, a voz teria dito isso à criança.
_ENT = {u"&middot;": u",", u"&nbsp;": u" ", u"&amp;": u" e ", u"&mdash;": u" ",
        u"&ndash;": u" ", u"&hellip;": u" ", u"&quot;": u'"', u"&lt;": u"",
        u"&gt;": u"", u"&#39;": u"'", u"&apos;": u"'"}


def lp(s):
    u"""tira a marcação e deixa o texto do jeito que a voz vai dizer"""
    t = re.sub(r"<[^>]+>", " ", s or u"")
    for _e, _v in _ENT.items():
        t = t.replace(_e, _v)
    t = re.sub(r"\s+", u" ", t)
    # ⚠️ e a tag que vira espaco deixa um vao ANTES da pontuacao ("o cinema ."),
    #    que o `_qa/revisor.py` acusa — com razao: a voz faz a pausa no lugar
    #    errado. Cola a pontuacao de volta na palavra.
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)
    # ⚠️ E A VIRGULA DA PAUSA PODE ENCOSTAR NUMA QUE JA EXISTIA (15/set/2026):
    #    a frase "My dad, ___ travels a lot" virou "My dad,, travels a lot" —
    #    duas virgulas coladas, que o Edge TTS le como uma pausa estranha e
    #    longa demais. Uma so, sempre.
    t = re.sub(r",\s*,+", u",", t)
    return t.strip()


def ch(w):
    return re.sub(r"[^a-z]", "",
                  unicodedata.normalize("NFKD", w.lower())
                  .encode("ascii", "ignore").decode())


F = collections.OrderedDict()


def p(k, v):
    F[k] = v


# ---------------------------------------------------------------------------
# AS FALAS DO MOTOR — estas toda folha viva tem
# ---------------------------------------------------------------------------
p(u"capa", u"O Espelho e o Contrário. Trinta e cinco folhas sobre palavras que dizem a "
           u"mesma coisa e palavras que dizem o contrário. Escreva o seu nome ali "
           u"embaixo e toque em Começar.")
p(u"folhaPronta", u"Folha pronta! Muito bem.")
p(u"escreva", u"Escreva a palavra usando o teclado.")
p(u"ligue", u"Toque numa palavra do lado esquerdo e depois na do lado direito.")
p(u"toque_palavra", u"Primeiro toque numa palavra ali embaixo. Depois toque na "
                    u"gaveta dela.")
p(u"vozOn", u"Narração ligada!")
p(u"fim", u"Você chegou ao fim! Agora olhe em volta da sala e escolha uma coisa. "
          u"Pense numa palavra que diz como ela é. E depois, no contrário. Conte para "
          u"um colega e veja se ele acha a mesma palavra que você.")
p(u"quase", u"Quase! Tente de novo.")
p(u"cacatoque", u"Toque primeiro na primeira letra da palavra.")
p(u"pegue_lapis", u"Primeiro pegue uma canetinha ali em cima. Depois toque na palavra.")
p(u"novoCaderno", u"Caderno novo! Escreva o seu nome e toque em Começar.")

# ---------------------------------------------------------------------------
# AS FALAS DAS FOLHAS — uma seção por bloco da escada, LENDO os DADOS
#
# ⚠️ A DICA NUNCA DIZ A RESPOSTA. Ela manda olhar a figura, dizer as duas
#    palavras em voz alta, ou pôr as duas numa frase.
# ⚠️ E A VOZ NÃO DIZ "SINÔNIMO" NEM "ANTÔNIMO" ANTES DA FOLHA 35 — o conceito
#    vem por último. Até lá é "diz a mesma coisa", "palavra irmã" e "contrário".
# ---------------------------------------------------------------------------
def cq(w):
    u"""o mesmo `chaveQuadro` do app: minúscula e só as letras de a a z"""
    return re.sub(r"[^a-z]", u"", (w or u"").lower())


ENUN = [
 u"Olhe as duas figuras. A primeira tem um nome. Escolha a palavra que diz o contrário para a segunda.",
 u"Toque numa figura da esquerda e depois na figura que mostra o contrário dela.",
 u"Mais cinco pares. Repare bem no desenho antes de ligar.",
 u"A primeira cena tem um nome. Escreva nas casinhas o nome da segunda: é o contrário. Toque nas casinhas ou digite.",
 u"Agora sem a cena: só a figura. Escreva o contrário.",
 u"Leia as duas palavras de cada peça. Elas dizem a mesma coisa, ou dizem o contrário? Leve a peça para a gaveta certa.",
 u"Leia a palavra grande. Das três embaixo, qual diz a mesma coisa que ela? Cuidado: uma delas diz o contrário.",
 u"Mais seis palavras. Se ficar em dúvida, ponha as duas numa frase e veja se ela continua igual.",
 u"Toque numa palavra da esquerda e depois na irmã dela, a que diz a mesma coisa.",
 u"Uma palavra pode ter mais de uma irmã. Marque todas as que dizem a mesma coisa e depois toque em Conferir.",
 u"As casinhas dizem quantas letras tem a palavra irmã. Leia a pista e escreva.",
 u"As duas gavetas de novo, com pares novos. Diga as duas palavras em voz alta antes de escolher.",
 u"Os pares mais difíceis. Pense: eu poderia trocar uma pela outra na frase?",
 u"Leia a frase. Troque a palavra destacada pelo contrário dela e veja a frase nova aparecer.",
 u"Agora a frase tem um buraco. Preencha com o contrário da palavra que já está nela.",
 u"Sem opções desta vez: escreva o contrário que falta na frase.",
 u"A Cíntia é exagerada: diz tudo duas vezes, com palavras irmãs. Preencha a fala dela.",
 u"O Leo é o contrário da Cíntia: discorda de tudo. Preencha a resposta dele com o contrário.",
 u"A coluna da esquerda tem números. Para cada palavra da direita, toque no número da irmã dela.",
 u"Ache na grade o contrário de cada palavra da lista: toque na primeira letra e depois na última.",
 u"Agora ache a palavra irmã, a que diz a mesma coisa. Primeira letra, depois a última.",
 u"Toque numa pista, escute e escreva o contrário na cruzadinha.",
 u"Agora a palavra está dentro da frase. Escreva o contrário da palavra em letra grande.",
 u"Cada carta de baixo tem uma irmã em cima. Puxe a carta até o par dela, ou toque numa e depois na outra.",
 u"Pegue uma canetinha e pinte as palavras irmãs com a mesma cor. A legenda diz de quem é cada cor.",
 u"Leia a frase. Uma das palavras é o contrário da palavra destacada, e ela ganhou um pedacinho a mais na frente. Qual é?",
 u"O pedacinho é IN ou IM? Puxe o certo até a frente da palavra, ou toque nele. Diga a palavra inteira em voz alta.",
 u"Mais seis. Repare na primeira letra da palavra: quando é IM e quando é IN? Tem um segredo aí.",
 u"Agora escreva a palavra inteira, com o pedacinho na frente.",
 u"Você já usou o pedacinho quatro folhas seguidas. Agora diga a regra que você descobriu.",
 u"Leia o texto e toque nas palavras que são os contrários de dia, alto, quente e cedo. Depois confira.",
 u"Agora toque nas palavras que dizem a mesma coisa que bonita, casa, feliz e cachorro. Depois confira.",
 u"A frase foi reescrita com o contrário da palavra destacada. Qual das duas ficou certa?",
 u"Pense no seu melhor amigo ou amiga. Escreva uma palavra que diga como ele é, e depois o contrário dela.",
 u"Você já sabe tudo isto. Agora os dois nomes: leve cada par de palavras para a linha dele."]
assert len(ENUN) == 35, len(ENUN)
for _i, _t in enumerate(ENUN):
    p(u"p%denun" % (_i + 1), _t)

ELOGIO = [u"Isso mesmo!", u"Muito bem!", u"Você acertou!", u"Boa!", u"Exatamente!", u"É isso aí!"]
DICAS_C = [u"Olhe de novo as duas figuras: o que mudou de uma para a outra?",
           u"Diga a palavra em voz alta e pense: o que é o contrário disso?",
           u"Pense no oposto, no avesso, no que é totalmente diferente."]
DICAS_S = [u"Ponha as duas palavras numa frase. A frase continua dizendo a mesma coisa?",
           u"Palavra irmã é a que você pode trocar sem mudar o sentido.",
           u"Uma das opções diz o contrário. Não é essa."]


def elogio(n):
    return ELOGIO[n % len(ELOGIO)]


def dicaC(n):
    return DICAS_C[n % len(DICAS_C)]


def dicaS(n):
    return DICAS_S[n % len(DICAS_S)]


ITENS = bloco(u"ITENS")


def pote(pi):
    v = ITENS[u"p%d" % pi]
    return v[0] if v and isinstance(v[0], list) else v


def palavras(*ws):
    u"""a fala de cada palavra que a criança toca — o alto-falante da opção"""
    for _w in ws:
        if _w:
            _t = lp(_w)
            _t = _t[0].upper() + _t[1:]
            p(u"pal_" + cq(_w), _t if _t[-1:] in u".!?" else _t + u".")


# --- 1: duas figuras, uma palavra (D37) --------------------------------------
PARF = bloco(u"PARF")
for _n, _k in enumerate(pote(1)):
    _P = PARF[_k]
    p(u"par_" + _k, _P[u"pal"].capitalize() + u". E a outra? " + _P[u"raiz"].capitalize() + u"…")
    p(u"certo1_" + _k, elogio(_n) + u" " + _P[u"pal"].capitalize() + u", e " + _P[u"raiz"].capitalize() + u" " + _P[u"r"].lower() + u".")
    p(u"dica1_" + _k, dicaC(_n))
    palavras(*_P[u"ops"])

# --- 2 e 3: ligue cada figura ao contrário (D11 e D06) -------------------------
LIGF = bloco(u"LIGF")
for _pi in (2, 3):
    for _n, _k in enumerate(pote(_pi)):
        _L = LIGF[_k]
        p(u"lgf_" + _k + u"_e", _L[u"pe"].capitalize() + u".")
        p(u"lgf_" + _k + u"_d", _L[u"pd"].capitalize() + u".")
        p(u"certo%d_%s" % (_pi, _k), elogio(_n) + u" " + _L[u"pe"].capitalize() + u" e " + _L[u"pd"].lower() + u" são contrários.")
        p(u"dica%d_%s" % (_pi, _k), u"Olhe a figura de " + _L[u"pe"].lower() + u". Qual desenho mostra exatamente o oposto?")

# --- 4 e 5: escreva o contrário da cena (D31 e D11) ---------------------------
ESCF = bloco(u"ESCF")
for _pi in (4, 5):
    for _n, _k in enumerate(pote(_pi)):
        _X = ESCF[_k]
        p(u"esf_" + _k, _X[u"pal"].capitalize() + u". E o contrário?")
        p(u"certo%d_%s" % (_pi, _k), elogio(_n) + u" " + _X[u"pal"].capitalize() + u" e " + _X[u"w"].lower() + u".")
        p(u"dica%d_%s" % (_pi, _k), u"Olhe a segunda figura e diga em voz alta o que ela mostra. Escreva essa palavra.")

# --- 6, 12 e 13: as duas gavetas --------------------------------------------
GAV = bloco(u"GAV")
for _gk, _G in GAV.items():
    for _C in _G[u"cols"]:
        p(u"gav_%s_%s" % (_gk, _C[u"k"]), u"Gaveta das palavras que dizem a mesma coisa." if _C[u"k"] == u"s"
          else u"Gaveta das palavras que dizem o contrário.")
for _pi, _gk in ((6, u"gA"), (12, u"gB"), (13, u"gC")):
    for _n, _k in enumerate(pote(_pi)):
        _X = GAV[_gk][u"pal"][_k]
        _a, _b = [_s.strip() for _s in _X[u"p"].split(u"·")]
        p(u"diz2_%s_%s" % (_gk, _k), _a.capitalize() + u", " + _b + u".")
        p(u"certo%d_%s" % (_pi, _k), elogio(_n) + u" " + _a.capitalize() + u" e " + _b +
          (u" dizem a mesma coisa." if _X[u"c"] == u"s" else u" dizem o contrário."))
        p(u"dica%d_%s" % (_pi, _k), u"Diga as duas palavras: " + _a + u", " + _b + u". Uma coisa pode ser as duas ao mesmo tempo?")

# --- 7 e 8: qual diz a mesma coisa? (D25) -----------------------------------
ESC3 = bloco(u"ESC3")
for _pi in (7, 8):
    for _n, _k in enumerate(pote(_pi)):
        _X = ESC3[_k]
        palavras(_X[u"p"], *_X[u"ops"])
        p(u"certo%d_%s" % (_pi, _k), elogio(_n) + u" " + _X[u"p"].capitalize() + u" e " + _X[u"r"] + u" dizem a mesma coisa.")
        p(u"dica%d_%s" % (_pi, _k), dicaS(_n))

# --- 9: ligue as palavras irmãs (D24) ----------------------------------------
LIGS = bloco(u"LIGS")
for _n, _k in enumerate(pote(9)):
    _L = LIGS[_k]
    palavras(_L[u"a"], _L[u"b"])
    p(u"certo9_" + _k, elogio(_n) + u" " + _L[u"a"].capitalize() + u" e " + _L[u"b"] + u" são irmãs.")
    p(u"dica9_" + _k, u"Pense em " + _L[u"a"] + u". Qual palavra da direita quer dizer a mesma coisa?")

# --- 10: marque todas as irmãs (D18) ----------------------------------------
MARQ = bloco(u"MARQ")
for _n, _k in enumerate(pote(10)):
    _M = MARQ[_k]
    palavras(_M[u"p"], *[_q[u"t"] for _q in _M[u"pecas"]])
    _ok = [_q[u"t"] for _q in _M[u"pecas"] if _q[u"ok"]]
    p(u"certo10_" + _k, elogio(_n) + u" " + _M[u"p"].capitalize() + u" tem " + str(len(_ok)) + u" irmãs: " + u", ".join(_ok) + u".")
    p(u"dica10_" + _k, u"Tem mais de uma irmã. E cuidado: uma das palavras diz o contrário de " + _M[u"p"].lower() + u".")

# --- 11: escreva na grade de casinhas (D22) ---------------------------------
GRADE = bloco(u"GRADE")
for _n, _k in enumerate(pote(11)):
    _G = GRADE[_k]
    palavras(_G[u"p"])
    p(u"grd_" + _k, re.sub(r"\s+", u" ", _G[u"p"].capitalize() + u". " +
      _G[u"d"].replace(u"_ N D _ R", u"alguma coisa, N, D, alguma coisa, R")) + u".")
    p(u"certo11_" + _k, elogio(_n) + u" " + _G[u"p"].capitalize() + u" e " + _G[u"w"].lower() + u" dizem a mesma coisa.")
    p(u"dica11_" + _k, u"Conte as casinhas: a palavra tem " + str(len(_G[u"w"])) + u" letras. Diga " + _G[u"p"] + u" de outro jeito.")

# --- 14, 15 e 16: o contrário dentro da frase -------------------------------
FRASE = bloco(u"FRASE")
for _pi in (14, 15, 16):
    for _n, _k in enumerate(pote(_pi)):
        _F = FRASE[_k]
        p(u"fra_" + _k, lp(_F[u"f"]).replace(u"___", u"lacuna"))
        if _pi == 16:
            p(u"certo%d_%s" % (_pi, _k), elogio(_n) + u" " + lp(_F[u"f"]).replace(u"___", _F[u"w"].lower()))
            p(u"dica%d_%s" % (_pi, _k), _F[u"d"] + u". Diga a frase inteira em voz alta.")
        else:
            palavras(*_F[u"ops"])
            p(u"certo%d_%s" % (_pi, _k), elogio(_n) + u" " + _F[u"nova"])
            p(u"dica%d_%s" % (_pi, _k), dicaC(_n + _pi))

# --- 17 e 18: a Cíntia e o Leo (D38) -----------------------------------------
CINTIA = bloco(u"CINTIA")
for _n, _k in enumerate(pote(17)):
    _C = CINTIA[_k]
    palavras(*_C[u"ops"])
    p(u"cin_" + _k, u"Cíntia diz: " + lp(_C[u"f"]).replace(u"___", u"lacuna"))
    p(u"certo17_" + _k, elogio(_n) + u" " + lp(_C[u"f"]).replace(u"___", _C[u"r"]))
    p(u"dica17_" + _k, u"A Cíntia repete com uma palavra irmã, que diz a mesma coisa. Qual das três é irmã?")
LEO = bloco(u"LEO")
for _n, _k in enumerate(pote(18)):
    _L = LEO[_k]
    palavras(*_L[u"ops"])
    p(u"leo_" + _k, u"Cíntia diz: " + lp(_L[u"c"]) + u" E o Leo responde: " + lp(_L[u"l"]).replace(u"___", u"lacuna"))
    p(u"certo18_" + _k, elogio(_n) + u" " + lp(_L[u"l"]).replace(u"___", _L[u"r"]))
    p(u"dica18_" + _k, u"O Leo discorda: ele diz o contrário do que a Cíntia disse. Qual é o contrário?")

# --- 19: numere os pares (D21) -----------------------------------------------
NUM = bloco(u"NUM")
for _n in range(1, 6):
    p(u"num_%d" % _n, u"Número %d." % _n)
for _n, _k in enumerate(pote(19)):
    _P = NUM[_k]
    palavras(_P[u"a"], _P[u"b"])
    p(u"certo19_" + _k, elogio(_n) + u" " + _P[u"b"].capitalize() + u" é irmã de " + _P[u"a"] + u", que está no número " + str(_n + 1) + u".")
    p(u"dica19_" + _k, u"Leia a coluna da esquerda de novo. Qual palavra quer dizer " + _P[u"b"] + u"?")

# --- 20 e 21: os dois caças ----------------------------------------------------
for _pi, _nome, _rot in ((20, u"CACA", u"O contrário de "), (21, u"CACA2", u"A palavra irmã de ")):
    _C = bloco(_nome)
    for _n, _k in enumerate(pote(_pi)):
        _P = _C[u"pal"][_k]
        p(u"cp_" + _k, _rot + _P[u"pista"] + u".")
        p(u"certo%d_%s" % (_pi, _k), elogio(_n) + u" " + _P[u"p"].capitalize() + u".")
        p(u"dica%d_%s" % (_pi, _k), u"Pense na palavra e procure a primeira letra dela na grade. Siga para o lado.")

# --- 22 e 23: as duas cruzadinhas --------------------------------------------
for _pi, _nome in ((22, u"CRZD"), (23, u"CRZD2")):
    _C = bloco(_nome)
    for _n, _k in enumerate(pote(_pi)):
        _P = _C[_k]
        p(u"crz_" + _k, _P[u"d"] + (u"" if _P[u"d"].endswith((u".", u"!")) else u"."))
        p(u"certo%d_%s" % (_pi, _k), elogio(_n) + u" " + _P[u"p"].capitalize() + u".")
        p(u"dica%d_%s" % (_pi, _k), u"Diga a palavra da pista em voz alta e pense no contrário dela. Conte as casinhas.")

# --- 24: arraste a carta até o par (D40) -------------------------------------
PARES = bloco(u"PARES")
for _n, _k in enumerate(pote(24)):
    _P = PARES[_k]
    palavras(_P[u"a"], _P[u"b"])
    p(u"certo24_" + _k, elogio(_n) + u" " + _P[u"a"].capitalize() + u" e " + _P[u"b"] + u" são um par.")
    p(u"dica24_" + _k, u"Pense em " + _P[u"a"] + u". Qual carta de cima quer dizer a mesma coisa?")

# --- 25: pinte da mesma cor (D19) --------------------------------------------
PINT = bloco(u"PINT")
for _C in PINT[u"cores"]:
    p(u"lapis_" + _C[u"k"], u"Canetinha " + _C[u"n"] + u": para as irmãs de " + _C[u"de"].lower() + u".")
for _n, _k in enumerate(pote(25)):
    _P = PINT[u"pal"][_k]
    _de = [_c for _c in PINT[u"cores"] if _c[u"k"] == _P[u"c"]][0]
    palavras(_P[u"p"])
    p(u"certo25_" + _k, elogio(_n) + u" " + _P[u"p"].capitalize() + u" é irmã de " + _de[u"de"].lower() + u".")
    p(u"dica25_" + _k, u"Leia a legenda: de quem é a irmã " + _P[u"p"] + u"? Pegue a canetinha dessa palavra.")

# --- 26 a 30: o pedacinho in-/im- (bloco declarado do currículo) --------------
PREF1 = bloco(u"PREF1")
for _n, _k in enumerate(pote(26)):
    _X = PREF1[_k]
    palavras(*_X[u"ops"])
    p(u"pf1_" + _k, lp(_X[u"f"]).replace(u"___", u"lacuna"))
    p(u"certo26_" + _k, elogio(_n) + u" " + _X[u"r"].capitalize() + u": é " + _X[u"raiz"] + u" com um pedacinho na frente, e vira o contrário.")
    p(u"dica26_" + _k, u"Procure a palavra " + _X[u"raiz"] + u" escondida dentro de uma das três. Com um pedacinho a mais na frente.")
p(u"pre_in", u"In.")
p(u"pre_im", u"Im.")
for _pi, _nome in ((27, u"PREF2"), (28, u"PREF3")):
    _D = bloco(_nome)
    for _n, _k in enumerate(pote(_pi)):
        _X = _D[_k]
        palavras(_X[u"raiz"])
        p(u"certo%d_%s" % (_pi, _k), elogio(_n) + u" " + (_X[u"pre"] + _X[u"raiz"]).capitalize() + u", o contrário de " + _X[u"raiz"] + u".")
        p(u"dica%d_%s" % (_pi, _k), u"Diga as duas: in" + _X[u"raiz"] + u", im" + _X[u"raiz"] + u". Qual soa como uma palavra de verdade? Olhe a primeira letra de " + _X[u"raiz"] + u".")
PREF4 = bloco(u"PREF4")
for _n, _k in enumerate(pote(29)):
    _X = PREF4[_k]
    p(u"pf4_" + _k, _X[u"d"] + u".")
    p(u"certo29_" + _k, elogio(_n) + u" " + _X[u"w"].capitalize() + u".")
    p(u"dica29_" + _k, u"Escreva o pedacinho primeiro, IN ou IM, e depois a palavra inteira.")
REGRA = bloco(u"REGRA")
for _n, _k in enumerate(pote(30)):
    _X = REGRA[_k]
    palavras(*_X[u"ops"])
    p(u"reg_" + _k, lp(_X[u"f"]).replace(u"___", u"lacuna"))
    p(u"certo30_" + _k, elogio(_n) + u" " + lp(_X[u"f"]).replace(u"___", _X[u"r"]))
    p(u"dica30_" + _k, u"Lembre das palavras que você escreveu: impossível, impaciente, infeliz, incapaz. Olhe a letra depois do pedacinho.")

# --- 31 e 32: ache no texto --------------------------------------------------
TXT = bloco(u"TXT")
for _pi, _tk in ((31, u"tx1"), (32, u"tx2")):
    _T = TXT[_tk]
    _nw = 0
    for _lin in _T[u"linhas"]:
        for _w in _lin:
            p(u"tx%d_%d" % (_pi, _nw), _w)
            _nw += 1
    p(u"certo%d_t" % _pi, u"Muito bem! Você achou todas.")
    p(u"dica%d_t" % _pi, u"Leia linha por linha. São " + str(len(_T[u"ok"])) + u" palavras. Toque em cada uma e depois confira.")

# --- 33: reescreva com o contrário (D05) -------------------------------------
REESC = bloco(u"REESC")
for _n, _k in enumerate(pote(33)):
    _R = REESC[_k]
    palavras(_R[u"certa"], _R[u"outra"])
    p(u"ree_" + _k, lp(_R[u"f"]))
    p(u"certo33_" + _k, elogio(_n) + u" " + _R[u"certa"])
    p(u"dica33_" + _k, u"Olhe a palavra destacada e pense no contrário dela. Só uma das frases usa esse contrário.")

# --- 34: escreva sobre o seu amigo (D27) --------------------------------------
PROD = bloco(u"PROD")
for _n, _k in enumerate(pote(34)):
    _X = PROD[_k]
    p(u"prd_" + _k, u"Escreva " + _X[u"q"] + u".")
    p(u"certo34_" + _k, u"Essa vale! A palavra é sua.")
    p(u"dica34_" + _k, u"Pense numa palavra que caiba no pedido. Vale mais de uma.")

# --- 35: o cartaz dos dois nomes ----------------------------------------------
CART = bloco(u"CART")
for _L in CART[u"linhas"]:
    p(u"cart_" + _L[u"k"], _L[u"t"].capitalize() + u": palavras que " + _L[u"d"] + u". Por exemplo, " + _L[u"e"].replace(u"·", u"e") + u".")
for _n, _k in enumerate(pote(35)):
    _X = CART[u"exem"][_k]
    p(u"ex_" + _k, _X[u"p"].replace(u"·", u"e") + u".")
    p(u"certo35_" + _k, elogio(_n) + u" " + _X[u"p"].replace(u"·", u"e").capitalize() + (u" são sinônimos." if _X[u"c"] == u"s" else u" são antônimos."))
    p(u"dica35_" + _k, u"Diga as duas palavras. Elas dizem a mesma coisa, ou o contrário?")


# ==============================================================================
#  AS SÍLABAS FALADAS — e este bloco é obrigatório em caderno que fale sílaba
#
#  ⚠️⚠️ POR QUE NÃO DÁ PARA SINTETIZAR A SÍLABA SOLTA (e a casa já pagou por
#     isto DUAS vezes — set/2026 e 16/set/2026, as duas o Marcos ouvindo):
#     a voz não lê SOM, lê PALAVRA. Entregue "SA" a ela e ela soletra "esse-á";
#     "VA" vira "vê-á"; "ÇÃ" ela nem tenta, porque ç não começa palavra em
#     português. Escrever a sílaba "como se fala" conserta UM caso e nunca
#     fecha a família.
#
#  O QUE FUNCIONA é o contrário: gravar a PALAVRA INTEIRA — que a voz pronuncia
#  certo, porque é palavra de verdade — alinhar letra a letra com o
#  `ctc-forced-aligner` e CORTAR a sílaba de dentro dela. Quem faz isso é o
#  `_padrao/silabas_voz.py`, dentro do `entregar.yml`, lendo o `silabas.json`
#  que sai daqui. O portão é o `_qa/silabas.py`.
#
#  COMO SE USA: para cada palavra do caderno, uma linha
#      _reg(u"CAVALO", [u"CA", u"VA", u"LO"])
#  e, no app, a sílaba fala por `falarSilaba(null, 0, "VA")` — nunca por
#  `falar("sil_va")`. Caderno que não fala sílaba não escreve nada: o
#  `silabas.json` sai com `"palavras": {}` e o `entregar.yml` nem baixa o
#  alinhador por ele.
#
#  ⚠️ NÃO HÁ FALA DE RESERVA POR SÍLABA. Faltando o recorte, o app diz a
#     PALAVRA INTEIRA. Uma reserva sintetizada seria o defeito voltando pela
#     porta dos fundos — e calado, que é pior.
# ==============================================================================
_SIL_DE = {}          # palavra -> [sílabas, NA ORDEM da palavra]
_MAPA_SIL = {}        # sílaba  -> [palavra, posição]
_RECUSADAS = []


def _reg(palavra, silabas):
    u"""⚠️ A LISTA TEM DE ESTAR NA ORDEM DA PALAVRA. O alinhador corta pelos
    limites das letras: ["RO","CAR"] para CARRO faz sair "ro" onde devia sair
    "car" — e a criança ouve o pedaço errado, sem erro nenhum na tela. Folha de
    ORDENAR guarda as sílabas EMBARALHADAS: passe-as por `_ordena` antes.
    ⚠️ E ganha sempre a partição MAIS FINA: "PIPO"+"CA" fecha PIPOCA sem ser
    separação silábica, e sobrescrevendo PI-PO-CA deixaria a sílaba PI muda."""
    silabas = list(silabas)
    if u"".join(silabas).upper() != palavra.upper():
        _RECUSADAS.append((palavra, silabas))
        return
    velha = _SIL_DE.get(palavra.lower())
    if velha and len(velha) >= len(silabas):
        return
    _SIL_DE[palavra.lower()] = silabas


def _ordena(palavra, embaralhadas):
    u"""as mesmas sílabas na ORDEM em que formam a palavra — sem inventar
    nenhuma: encaixa da esquerda para a direita e desiste se não fechar."""
    resto, saida, alvo = list(embaralhadas), [], palavra.upper()
    while alvo:
        for _i, _sb in enumerate(resto):
            if alvo.startswith(_sb.upper()):
                saida.append(_sb)
                alvo = alvo[len(_sb):]
                resto.pop(_i)
                break
        else:
            return None
    return saida if not resto else None


def _achaSilaba(s):
    u"""a palavra de onde a sílaba será recortada. Ganha a MAIS CURTA: menos
    letras na gravação, menos lugar para o alinhador errar."""
    cand = [_w for _w in sorted(_SIL_DE) if s in _SIL_DE[_w]]
    if not cand:
        return None
    _w = min(cand, key=lambda w: (len(_SIL_DE[w]), len(w), w))
    return [_w, _SIL_DE[_w].index(s)]


def _mapeia(soltas):
    u"""monta o SILMAP das sílabas que o app fala sozinhas, e DEVOLVE as órfãs.
    ⚠️ Sílaba órfã não é erro — o app diz a palavra inteira — mas tem de sair
    IMPRESSA, senão aquele botão emudece sem ninguém saber. Distratora que não
    mora em palavra nenhuma do caderno pede uma PALAVRA-CARREGADORA: uma
    palavra de verdade, curta, registrada só para ser gravada e cortada."""
    orfas = []
    for _s in sorted(set(soltas)):
        _achou = _achaSilaba(_s)
        if _achou:
            _MAPA_SIL[_s] = _achou
        else:
            orfas.append(_s)
    # e a PALAVRA INTEIRA de cada uma precisa existir como fala: é dela que o
    # recorte sai, e é ela que o app diz quando o recorte falta.
    for _w in sorted(_SIL_DE):
        p(u"pal_" + ch(_w), _w.upper() + u".")
    return orfas


_ORFAS = _mapeia([])          # <- passe aqui TODA sílaba que o app fala sozinha


# ---------------------------------------------------------------------------
# A SAÍDA
# ---------------------------------------------------------------------------
def chave(s):
    u"""O nome do mp3 sai do TEXTO, não da chave da fala — assim duas chaves que
    dizem a mesma frase gravam um arquivo só."""
    s = re.sub(r"\s+", u" ", s or u"").strip().lower()
    hh = 5381
    for c in s:
        hh = ((hh * 33) ^ ord(c)) & 0xFFFFFFFF
    d, out = hh, u""
    if d == 0:
        return u"0"
    while d:
        out = u"0123456789abcdefghijklmnopqrstuvwxyz"[d % 36] + out
        d //= 36
    return out


falas, vistos = [], {}
for k in sorted(F.keys()):
    txt = F[k]
    if not txt:
        continue
    c = chave(txt)
    if c in vistos:
        continue
    vistos[c] = 1
    falas.append({u"id": PREFIXO + c, u"texto": txt, u"voz": VOZ})

html = io.open(CAM, encoding=u"utf-8").read()
blocoF = (u"/*FALAS-INI*/\nvar FALAS = "
          + json.dumps(F, ensure_ascii=False, indent=1, sort_keys=True) + u";\n/*FALAS-FIM*/")
blocoV = (u"/*VOZOK-INI*/var VOZOK = "
          + json.dumps(dict((c, 1) for c in vistos), ensure_ascii=False) + u";/*VOZOK-FIM*/")
novo = re.sub(r"/\*FALAS-INI\*/.*?/\*FALAS-FIM\*/", lambda m: blocoF, html, flags=re.S)
novo = re.sub(r"/\*VOZOK-INI\*/.*?/\*VOZOK-FIM\*/", lambda m: blocoV, novo, flags=re.S)

# ⭐ o `silabas.json` é o que o `entregar.yml` lê para cortar cada sílaba de
#    dentro do mp3 da palavra inteira, e o `SILMAP` é o que o app usa para saber
#    de qual palavra veio cada pedaço. Uma fonte só para os dois.
io.open(os.path.join(AQUI, u"silabas.json"), u"w", encoding=u"utf-8").write(
    json.dumps({u"prefixo": PREFIXO, u"voz": VOZ,
                u"palavras": dict((w, _SIL_DE[w]) for w in sorted(_SIL_DE))},
               ensure_ascii=False, indent=1))
blocoS = (u"/*SILMAP-INI*/var SILMAP = "
          + json.dumps(_MAPA_SIL, ensure_ascii=False, sort_keys=True) + u";/*SILMAP-FIM*/")
novo = re.sub(r"/\*SILMAP-INI\*/.*?/\*SILMAP-FIM\*/", lambda m: blocoS, novo, flags=re.S)
io.open(CAM, u"w", encoding=u"utf-8").write(novo)
io.open(os.path.join(AQUI, u"falas.json"), u"w", encoding=u"utf-8").write(
    json.dumps(falas, ensure_ascii=False, indent=1))
io.open(os.path.join(AQUI, u"voz.txt"), u"w", encoding=u"utf-8").write(VOZ + u"\n")
print(u"FALAS: %d chaves; falas.json: %d fala(s) para gravar; "
      u"silabas: %d palavra(s) para recortar, %d silaba(s) no mapa"
      % (len(F), len(falas), len(_SIL_DE), len(_MAPA_SIL)))
if _ORFAS:
    print(u"   \u26a0\ufe0f %d silaba(s) SEM palavra de origem (o app dira a palavra "
          u"inteira): %s" % (len(_ORFAS), u", ".join(_ORFAS)))
if _RECUSADAS:
    print(u"   \u26a0\ufe0f %d lista(s) recusada(s) por nao formarem a palavra: %s"
          % (len(_RECUSADAS), u", ".join(
              u"%s=%s" % (w, u"-".join(sl)) for w, sl in _RECUSADAS[:8])))
