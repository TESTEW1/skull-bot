"""
╔══════════════════════════════════════════════════════════════════╗
║                         💀  PINK BOT  💀                          ║
║               A Caveirinha Guardiã da DOMINUS                     ║
║                          v1.0 — Online                            ║
╚══════════════════════════════════════════════════════════════════╝

Lore rápida:
  Pink é a pequena caveira que zela pela DOMINUS. Não grita, não se
  agita, não precisa de muita atenção — mas está sempre por perto,
  observando tudo com carinho (e um bom senso de humor seco sobre o
  fato de ser feito só de osso). Um pouco sério, um pouco fofo,
  sempre presente.

Módulos:
  • Diálogo       — Pink aprende e responde a gatilhos ensinados
  • Aparições     — aparece do nada, sem ser chamado
  • Chamado       — responde quando mencionado ou quando dizem "pink"
  • Reações       — reage com emoji a palavras-chave (ossos, medo, fofura)
  • Respeitos     — sistema de "pagar respeitos" (F) com placar/memorial
  • Invocação     — força Pink a se manifestar
  • Oráculo       — profecias curtas e enigmáticas
  • Grupos        — painel com botão que cria cargo + chat + call
  • Fichas        — formulários interativos (modal + confirmação) pra
                    novos membros, Staff e parcerias (mapa, comercial,
                    DJ, clã e comunidade — cada uma é sua própria ficha)
  • Auditoria     — log total de ações do servidor num canal dedicado

⚠️  ANTES DE RODAR: procure por "TROCAR AQUI" nas configurações abaixo
    e preencha com os IDs reais do seu servidor (canais, cargos e
    categoria). Sem isso, os módulos de Grupos, Cargo Vinculado e
    Auditoria não vão funcionar.
"""

import discord
from discord.ext import commands
import asyncio
import os
import json
import random
import re
import traceback
from datetime import datetime, timezone
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

# ══════════════════════════════════════════════════════════════════
#  ⚙️  CONFIGURAÇÕES GERAIS
# ══════════════════════════════════════════════════════════════════

TOKEN = os.getenv("PINK_TOKEN") or os.getenv("TOKEN")

DIALOGO_FILE   = "pink_dialogo.json"
RESPEITOS_FILE = "pink_respeitos.json"

COOLDOWN_RESPOSTA          = 3     # segundos entre respostas automáticas por canal
CHANCE_GATILHO_SEM_CHAMADO = 0.0   # 0 = só responde gatilho quando Pink é chamado
CHANCE_APARICAO_ESPONTANEA = 0.012 # chance de aparecer do nada por mensagem
SILENCIO_MINIMO_APARICAO   = 90    # segundos de silêncio no canal antes de poder aparecer sozinho
CHANCE_REACAO_EMOJI        = 0.35  # chance de reagir com emoji a palavra-chave

# ══════════════════════════════════════════════════════════════════
#  ⚙️  CONFIGURAÇÕES — MÓDULO DE GRUPOS (painel/ticket)
# ══════════════════════════════════════════════════════════════════

CANAL_PAINEL_ID    = 0   # TROCAR AQUI — canal onde o painel/ticket fica
CARGO_PERMITIDO_ID = 0   # TROCAR AQUI — só quem tem esse cargo pode clicar
CATEGORIA_ID       = 0   # TROCAR AQUI — categoria onde os canais do grupo entram

IMAGEM_PAINEL = "https://exemplo.com/coloque_a_imagem_do_painel_aqui.png"  # TROCAR AQUI

COR_ROXO_GRUPO = 0x6C3483

GRUPOS_DATA_FILE = "pink_grupos.json"

_HEX_RE = re.compile(r'^#?[0-9A-Fa-f]{6}$')

# ══════════════════════════════════════════════════════════════════
#  ⚙️  CONFIGURAÇÕES — CARGO VINCULADO (auto-cargo ao ganhar outro)
# ══════════════════════════════════════════════════════════════════

CARGO_GATILHO_ID   = 0   # TROCAR AQUI — quando alguém recebe ESSE cargo...
CARGO_VINCULADO_ID = 0   # TROCAR AQUI — ...Pink dá esse cargo junto, automaticamente

# ══════════════════════════════════════════════════════════════════
#  ⚙️  CONFIGURAÇÕES — AUDITORIA (log total do servidor)
# ══════════════════════════════════════════════════════════════════

CANAL_AUDITORIA_ID = 0   # TROCAR AQUI — canal onde os logs de auditoria são postados

# ══════════════════════════════════════════════════════════════════
#  ⚙️  CONFIGURAÇÕES — REGISTRO (painéis de reação pra pegar cargo)
# ══════════════════════════════════════════════════════════════════
#
# Cada painel abaixo é enviado UMA ÚNICA VEZ no canal configurado —
# a primeira vez que o bot ligar com esse canal configurado e sem ter
# mandado esse painel ainda. Se você desligar e ligar o bot de novo,
# ele NÃO manda de novo (o controle fica salvo em REGISTRO_DATA_FILE).
# Reagir com o emoji dá o cargo, tirar a reação remove o cargo — igual
# ao "reaction role" clássico.
#
# Você NÃO precisa mais criar os cargos manualmente! Se um cargo abaixo
# ficar com ID "0" (ou seja, "TROCAR AQUI" não foi preenchido), Pink
# cria o cargo sozinha (com nome e cor prontos, ver CARGOS_REGISTRO_AUTO
# logo abaixo) na primeira vez que o painel daquele cargo for enviado, e
# guarda o ID gerado em CARGOS_REGISTRO_FILE pra sempre usar o mesmo
# cargo dali pra frente — não recria em cada restart.
#
# Se você preferir usar um cargo que você mesmo já criou, é só colocar
# o ID real aqui embaixo (Discord > Configurações do servidor > Cargos
# > clique direito > Copiar ID, com o modo desenvolvedor ativado) que
# Pink usa o seu cargo em vez de criar um novo.

CANAL_REGISTRO_ID = 1543317542234488942  # canal onde os painéis de registro são publicados

REGISTRO_DATA_FILE     = "pink_registro.json"
CARGOS_REGISTRO_FILE   = "pink_cargos_registro.json"  # guarda os IDs dos cargos que Pink criou sozinha

# chave do cargo -> ID do cargo no servidor. Deixe em 0 pra Pink criar o
# cargo automaticamente (recomendado); só preencha se você já tiver um
# cargo pronto que quer reaproveitar.
CARGOS_REGISTRO: dict[str, int] = {
    # Verificação
    "verificacao_menor18":   0,
    "verificacao_maior18":   0,
    # Gênero
    "genero_menina":              0,
    "genero_menino":              0,
    "genero_prefiro_nao_dizer":   0,
    # Sexualidade
    "sexualidade_hetero":             0,
    "sexualidade_lgbt":               0,
    "sexualidade_prefiro_nao_dizer":  0,
    # Aniversário
    "aniversario_janeiro":    0,
    "aniversario_fevereiro":  0,
    "aniversario_marco":      0,
    "aniversario_abril":      0,
    "aniversario_maio":       0,
    "aniversario_junho":      0,
    "aniversario_julho":      0,
    "aniversario_agosto":     0,
    "aniversario_setembro":   0,
    "aniversario_outubro":    0,
    "aniversario_novembro":   0,
    "aniversario_dezembro":   0,
    # Gravações
    "gravacoes_participa":      0,
    "gravacoes_nao_participa":  0,
    # Dispositivo
    "dispositivo_mobile":   0,
    "dispositivo_pc":       0,
    "dispositivo_console":  0,
}

# cargo_key -> (nome do cargo, cor hex) usados SÓ quando Pink precisa criar
# o cargo automaticamente (ou seja, quando o ID em CARGOS_REGISTRO acima
# está em 0 e o cargo ainda não foi criado antes). Pode editar o nome e a
# cor à vontade antes de rodar o bot pela primeira vez.
CARGOS_REGISTRO_AUTO: dict[str, tuple[str, int]] = {
    # Verificação
    "verificacao_menor18":  ("-18", 0x95A5A6),
    "verificacao_maior18":  ("+18", 0xE74C3C),
    # Gênero
    "genero_menina":               ("Gênero: Menina", 0xE91E63),
    "genero_menino":               ("Gênero: Menino", 0x3498DB),
    "genero_prefiro_nao_dizer":    ("Gênero: Prefiro Não Dizer", 0x95A5A6),
    # Sexualidade
    "sexualidade_hetero":              ("Hétero", 0x5DADE2),
    "sexualidade_lgbt":                ("LGBTQI+", 0xE056FD),
    "sexualidade_prefiro_nao_dizer":   ("Sexualidade: Prefiro Não Dizer", 0x95A5A6),
    # Aniversário
    "aniversario_janeiro":    ("Aniversário: Janeiro", 0x3498DB),
    "aniversario_fevereiro":  ("Aniversário: Fevereiro", 0xE91E63),
    "aniversario_marco":      ("Aniversário: Março", 0x2ECC71),
    "aniversario_abril":      ("Aniversário: Abril", 0xF7DC6F),
    "aniversario_maio":       ("Aniversário: Maio", 0xFF69B4),
    "aniversario_junho":      ("Aniversário: Junho", 0xF4D03F),
    "aniversario_julho":      ("Aniversário: Julho", 0xF1C40F),
    "aniversario_agosto":     ("Aniversário: Agosto", 0xE67E22),
    "aniversario_setembro":   ("Aniversário: Setembro", 0x58D68D),
    "aniversario_outubro":    ("Aniversário: Outubro", 0xD35400),
    "aniversario_novembro":   ("Aniversário: Novembro", 0xA0522D),
    "aniversario_dezembro":   ("Aniversário: Dezembro", 0xC0392B),
    # Gravações
    "gravacoes_participa":      ("Participa de Gravações", 0x2ECC71),
    "gravacoes_nao_participa":  ("Não Participa de Gravações", 0xE74C3C),
    # Dispositivo (também usado pelas opções de PC/Celular da Verificação)
    "dispositivo_mobile":   ("Mobile", 0x1ABC9C),
    "dispositivo_pc":       ("PC", 0x2ECC71),
    "dispositivo_console":  ("Console", 0x9B59B6),
}

# cada painel: chave interna, título, descrição e lista de opções
# (emoji, rótulo, chave do cargo em CARGOS_REGISTRO). Pode trocar os
# emojis à vontade — só não repita o mesmo emoji duas vezes dentro do
# MESMO painel.
PAINEIS_REGISTRO: list[dict] = [
    {
        "chave": "verificacao",
        "titulo": "🧭 Verificação",
        "descricao": "Verificação básica: idade.",
        "opcoes": [
            ("🧒", "-18", "verificacao_menor18"),
            ("🔞", "+18", "verificacao_maior18"),
        ],
    },
    {
        "chave": "genero",
        "titulo": "⚧️ Gênero",
        "descricao": "Marque como você se identifica.",
        "opcoes": [
            ("👧", "Menina", "genero_menina"),
            ("👦", "Menino", "genero_menino"),
            ("❔", "Prefiro Não Dizer", "genero_prefiro_nao_dizer"),
        ],
    },
    {
        "chave": "sexualidade",
        "titulo": "🌈 Sexualidade",
        "descricao": "Marque sua orientação, se quiser dizer.",
        "opcoes": [
            ("👫", "Hétero", "sexualidade_hetero"),
            ("🏳️‍🌈", "LGBTQI+", "sexualidade_lgbt"),
            ("❓", "Prefiro Não Dizer", "sexualidade_prefiro_nao_dizer"),
        ],
    },
    {
        "chave": "aniversario",
        "titulo": "🎂 Aniversário",
        "descricao": "Marque o mês do seu aniversário.",
        "opcoes": [
            ("🎆", "Janeiro", "aniversario_janeiro"),
            ("💘", "Fevereiro", "aniversario_fevereiro"),
            ("🍀", "Março", "aniversario_marco"),
            ("🐣", "Abril", "aniversario_abril"),
            ("🌷", "Maio", "aniversario_maio"),
            ("🌽", "Junho", "aniversario_junho"),
            ("☀️", "Julho", "aniversario_julho"),
            ("🎈", "Agosto", "aniversario_agosto"),
            ("🍃", "Setembro", "aniversario_setembro"),
            ("🎃", "Outubro", "aniversario_outubro"),
            ("🍁", "Novembro", "aniversario_novembro"),
            ("🎄", "Dezembro", "aniversario_dezembro"),
        ],
    },
    {
        "chave": "gravacoes",
        "titulo": "🎬 Gravações",
        "descricao": "Diz se você participa de gravações do servidor ou não.",
        "opcoes": [
            ("🎬", "Participa de Gravações", "gravacoes_participa"),
            ("🚫", "Não Participa de Gravações", "gravacoes_nao_participa"),
        ],
    },
    {
        "chave": "dispositivo",
        "titulo": "📡 Dispositivo",
        "descricao": "De onde você acessa o servidor.",
        "opcoes": [
            ("📱", "Mobile", "dispositivo_mobile"),
            ("💻", "Pc", "dispositivo_pc"),
            ("🎮", "Console", "dispositivo_console"),
        ],
    },
]

# ══════════════════════════════════════════════════════════════════
#  🤖  SETUP DO BOT
# ══════════════════════════════════════════════════════════════════

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True   # necessário pro on_member_update (cargo vinculado) disparar

bot = commands.Bot(command_prefix=["pk!", "Pk!", "pink ", "Pink "], intents=intents)
bot.remove_command("help")

# ══════════════════════════════════════════════════════════════════
#  💀  A PERSONA DE PINK
# ══════════════════════════════════════════════════════════════════

PINK = {
    "nome": "Pink",
    "titulo": "Pink, a Caveirinha da DOMINUS",
    "emoji": "💀",
    "cor": 0x6C3483,
}

COR_NEUTRA   = 0x6C3483
COR_OSSO     = 0xF5F0E6
COR_VERDE    = 0x00E676
COR_VERMELHO = 0xFF5252
COR_DOURADO  = 0xFFD700

FOOTER_DOMINUS = "💀 DOMINUS"


def fala(texto: str) -> str:
    """Formata uma linha de diálogo com a assinatura de Pink."""
    return f"{PINK['emoji']} **{PINK['nome']}** — {texto}"


def embed_pink(titulo: str, desc: str) -> discord.Embed:
    e = discord.Embed(title=titulo, description=desc, color=PINK["cor"], timestamp=datetime.now(timezone.utc))
    e.set_footer(text=f"{PINK['emoji']} {PINK['titulo']}")
    return e


def embed_ok(titulo: str, desc: str) -> discord.Embed:
    e = discord.Embed(title=titulo, description=desc, color=COR_VERDE, timestamp=datetime.now(timezone.utc))
    e.set_footer(text="💀 Pink")
    return e


def embed_erro(desc: str) -> discord.Embed:
    e = discord.Embed(title="❌ eita...", description=desc, color=COR_VERMELHO, timestamp=datetime.now(timezone.utc))
    e.set_footer(text="💀 Pink")
    return e


# ══════════════════════════════════════════════════════════════════
#  💾  PERSISTÊNCIA
# ══════════════════════════════════════════════════════════════════

def _carregar_dialogo() -> dict:
    if os.path.exists(DIALOGO_FILE):
        try:
            with open(DIALOGO_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "respostas" not in data:
                    data = {"respostas": {}}
                return data
        except Exception:
            pass
    return {"respostas": {}}


def _salvar_dialogo(db: dict):
    with open(DIALOGO_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def _carregar_respeitos() -> dict:
    if os.path.exists(RESPEITOS_FILE):
        try:
            with open(RESPEITOS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _salvar_respeitos(data: dict):
    with open(RESPEITOS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _carregar_grupos() -> dict:
    if os.path.exists(GRUPOS_DATA_FILE):
        try:
            with open(GRUPOS_DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _salvar_grupos(data: dict):
    with open(GRUPOS_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _carregar_registro() -> dict:
    if os.path.exists(REGISTRO_DATA_FILE):
        try:
            with open(REGISTRO_DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "enviados" not in data:
                    data = {"enviados": {}}
                return data
        except Exception as e:
            # antes isso era engolido em silêncio — agora loga, pra dar pra
            # saber no console se o arquivo sumiu/corrompeu num restart
            print(f"⚠️ Registro: falha ao carregar {REGISTRO_DATA_FILE} — {e}")
    return {"enviados": {}}


def _salvar_registro(data: dict):
    with open(REGISTRO_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _carregar_cargos_registro() -> dict:
    """cargo_key -> ID do cargo que Pink criou sozinha (auto-criação)."""
    if os.path.exists(CARGOS_REGISTRO_FILE):
        try:
            with open(CARGOS_REGISTRO_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Registro: falha ao carregar {CARGOS_REGISTRO_FILE} — {e}")
    return {}


def _salvar_cargos_registro(data: dict):
    with open(CARGOS_REGISTRO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════════════
#  💬  BANCO DE FALAS — SEED (a voz de Pink: sério por fora, fofo por dentro)
# ══════════════════════════════════════════════════════════════════

_SAUDACOES = [
    "oi. 💀 (é sério, é só isso mesmo — mas fico feliz que você tenha vindo)",
    "*as órbitas vazias piscam devagar* ...oi. eu tava aqui o tempo todo 💀",
    "oi!! bom, do meu jeito de dizer 'oi com entusiasmo' 🦴💀",
]

_APARICOES = [
    "...eu tava aqui o tempo todo. vocês só não notaram 💀",
    "*um estalar de ossos ecoa baixinho* só passando por aqui 🦴",
    "silêncio é bom. mas de vez em quando eu gosto de aparecer 💀",
    "*pisca as órbitas vazias* oi. voltei 🦴💀",
]

_INVOCACOES = [
    "fui invocado. aqui estou, como sempre, sem pressa 💀",
    "*emerge devagar, sem fazer barulho* Pink responde ao chamado 🦴",
    "não precisa gritar meu nome duas vezes. eu ouço bem, mesmo sem orelhas 💀",
]

_ORACULOS = [
    "os ossos não mentem: algo bom está vindo pra você 💀✨",
    "vejo silêncio antes da tempestade... prepare-se, mas não se apavore 💀",
    "o que está enterrado, um dia volta à superfície. cuidado com o que você esconde 🦴",
    "sua sorte hoje?? nem quente, nem fria. só... constante. como eu 💀",
    "às vezes a resposta que você procura já está debaixo do seu nariz. ou do meu crânio 🦴💀",
]

_RESPEITOS_FALAS = [
    "...respeito recebido. obrigado 💀🖤",
    "F. eu sinto o peso disso, mesmo sem ter coração pra sentir 💀",
    "seu respeito foi guardado nos ossos da DOMINUS 🦴",
    "*inclina a cabeça em silêncio* ...aceito, e agradeço 💀",
]

_LIBERAR_PAINEL_PINK = [
    "tá bem... vou abrir o painel de grupos. sem pressa, mas vou 💀",
    "*estala os dedos ósseos* painel liberado 🦴",
    "ninguém precisa gritar comigo pra eu abrir isso. mas tudo bem, aqui vai 💀",
    "*abre o painel devagar, como tudo que eu faço* pronto 🦴💀",
]

_STATUS_PRESENCA = [
    "o silêncio do cemitério 💀",
    "os ossos rangerem 🦴",
    "quem precisa de um abraço 🖤",
    "a DOMINUS de longe 💀",
]

# gatilho -> lista de respostas possíveis (Pink só tem uma voz)
_RESPOSTAS_SEED = {
    "bom dia": [
        "bom dia... eu não durmo, então já estava aqui. mas fico feliz que você acordou 💀",
        "bom dia. o sol não esquenta os ossos, mas sua chegada aquece um pouco 🦴✨",
    ],
    "boa tarde": [
        "boa tarde. o dia já passou da metade, e eu continuo aqui, quietinho, observando 💀",
        "boa tarde. espero que o resto do seu dia seja tão tranquilo quanto eu 🦴",
    ],
    "boa noite": [
        "boa noite. durma bem... eu fico de guarda, não precisa se preocupar 💀🌙",
        "boa noite. os ossos também descansam, só que raramente 🦴",
    ],
    "oi": [
        "oi. 💀 (é sério, é só isso mesmo — mas gosto que você tenha vindo)",
        "oi. as órbitas vazias notaram sua chegada 🦴",
    ],
    "olá": [
        "olá. formalidade combina comigo, eu sou feito de osso, afinal 💀",
        "olá. seja bem-vindo(a), com toda a calma que eu tenho pra oferecer 🦴",
    ],
    "e ai": [
        "e aí. tudo tranquilo por aqui, como sempre 💀",
        "e aí. nada de novo debaixo da terra 🦴",
    ],
    "tudo bem": [
        "tudo bem, do jeito quieto que eu gosto. e você?? 💀",
        "tudo em paz. os ossos não reclamam muito 🦴",
    ],
    "como você está": [
        "eu sou uma caveira, então... sempre do mesmo jeito. mas obrigado por perguntar 💀🦴",
        "estável. como um bom esqueleto deve ser 💀",
    ],
    "como vai": [
        "vou bem, sem pressa nenhuma pra lugar nenhum 💀",
        "vou devagar. é o único ritmo que eu conheço 🦴",
    ],
    "salve": [
        "salve. 💀",
        "salve, viajante. os ossos recebem bem quem chega com respeito 🦴",
    ],
    "tchau": [
        "tchau. eu vou continuar aqui, se precisar 💀",
        "vá com cuidado. eu fico de olho vazio, mas de olho 🦴",
    ],
    "até mais": [
        "até mais. eu não vou a lugar nenhum mesmo 💀",
        "até logo. os ossos não se cansam de esperar 🦴",
    ],
    "falou": [
        "falou. cuide-se, tá?? 💀",
        "falou. até a próxima vez que os ossos rangerem por aqui 🦴",
    ],
    "quem é você": [
        "eu sou Pink. a caveirinha que cuida da DOMINUS. sério por fora, mas... gosto de vocês 💀🖤",
        "Pink. só isso. não preciso de mais nome do que ossos precisam de pele 🦴",
    ],
    "quem é dominus": [
        "DOMINUS é o lugar que eu guardo. e agora, também é seu 💀",
        "DOMINUS é o meu lar. e eu levo isso a sério, apesar da minha cara de brincadeira 🦴",
    ],
    "estou triste": [
        "sinto muito. vem, senta aqui do meu lado. eu não abraço direito (sem braços pra isso), mas fico com você 💀🖤",
        "tristeza pesa até nos ossos. eu fico por perto até ela passar 🦴",
    ],
    "estou com raiva": [
        "respira. eu já vi ossos quebrarem por muito menos do que isso. não vale a pena 💀",
        "deixa essa raiva descansar um pouco. ela vai esfriar, prometo 🦴",
    ],
    "estou feliz": [
        "que bom. guarda esse sorriso, ele te cai bem 💀✨",
        "felicidade é rara por aqui, e ainda assim bonita de ver 🦴",
    ],
    "obrigado": [
        "não precisa agradecer. é o que eu faço 💀",
        "de nada. os ossos não pedem retorno 🦴",
    ],
    "com medo": [
        "eu sou uma caveira e nem eu tenho medo de nada. fica comigo, vai passar 💀",
        "medo é normal. só não deixa ele te enterrar antes da hora 🦴",
    ],
    "kkkk": [
        "hehe. até osso balança quando ri 💀",
        "essa foi boa. eu não tenho bochechas, mas se tivesse, estariam doendo de rir 🦴",
    ],
}

# ══════════════════════════════════════════════════════════════════
#  🦴  PALAVRAS-CHAVE PARA REAÇÕES DE EMOJI
# ══════════════════════════════════════════════════════════════════

_PALAVRAS_OSSOS = ["osso", "ossos", "esqueleto", "caveira", "crânio", "cranio"]
_PALAVRAS_MEDO  = ["medo", "assombra", "fantasma", "arrepiante", "sombrio"]
_PALAVRAS_FOFO  = ["fofo", "fofinho", "fofa", "gracinha", "cute"]


# ══════════════════════════════════════════════════════════════════
#  💀  COG PRINCIPAL — DIÁLOGO DE PINK
# ══════════════════════════════════════════════════════════════════

class PinkCog(commands.Cog, name="Pink"):
    """A voz de Pink: diálogo, aparições, respeitos e invocações."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = _carregar_dialogo()
        self.respeitos = _carregar_respeitos()

        # mescla o seed (não sobrescreve o que já foi ensinado)
        for gatilho, respostas in _RESPOSTAS_SEED.items():
            if gatilho not in self.db["respostas"]:
                self.db["respostas"][gatilho] = list(respostas)
        _salvar_dialogo(self.db)

        self._ultimo_resp: dict[int, datetime] = {}

    # ── Helpers de diálogo ─────────────────────────────

    def _checar_gatilho(self, texto: str) -> str | None:
        texto_lower = texto.lower().strip()
        if texto_lower in self.db["respostas"]:
            return texto_lower
        melhor = None
        for gatilho in self.db["respostas"]:
            if len(gatilho) <= 3 and gatilho.replace(" ", "").isalpha():
                # gatilhos bem curtos (ex.: "oi") exigem limite de palavra,
                # senão bateriam dentro de outras palavras (ex.: "coisa", "boiada")
                encontrado = re.search(r'(?<!\w)' + re.escape(gatilho) + r'(?!\w)', texto_lower)
            else:
                encontrado = gatilho in texto_lower
            if encontrado:
                if melhor is None or len(gatilho) > len(melhor):
                    melhor = gatilho
        return melhor

    def _responder(self, gatilho: str) -> str:
        pool = self.db["respostas"].get(gatilho, [])
        return random.choice(pool) if pool else ""

    async def _reagir_emojis(self, message: discord.Message, texto_lower: str):
        if random.random() > CHANCE_REACAO_EMOJI:
            return
        try:
            if any(p in texto_lower for p in _PALAVRAS_OSSOS):
                await message.add_reaction("🦴")
            elif any(p in texto_lower for p in _PALAVRAS_MEDO):
                await message.add_reaction("👻")
            elif any(p in texto_lower for p in _PALAVRAS_FOFO):
                await message.add_reaction("🖤")
        except (discord.Forbidden, discord.HTTPException):
            pass

    # ── Evento principal ───────────────────────────────

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return

        texto_lower = message.content.lower()

        pink_chamado = (
            self.bot.user in message.mentions
            or "pink" in texto_lower
        )

        now = datetime.now(timezone.utc)
        ultimo = self._ultimo_resp.get(message.channel.id)
        em_cooldown = bool(ultimo and (now - ultimo).total_seconds() < COOLDOWN_RESPOSTA)

        # comando especial: "pink liberar painel" -> publica o painel de
        # criação de grupos (mesma ação de pk!painelgrupo). Ignora cooldown
        # de propósito, já que é uma ação administrativa, não bate-papo.
        if "liberar painel" in texto_lower and "pink" in texto_lower:
            if not message.author.guild_permissions.administrator:
                await message.reply(
                    fala("você não tem permissão pra pedir isso de mim 🚫"),
                    mention_author=False,
                )
                return
            grupos_cog = self.bot.get_cog("Grupos")
            if grupos_cog is None:
                await message.reply(
                    fala("...o módulo de grupos nem carregou direito, chama um admin 💀"),
                    mention_author=False,
                )
                return
            canal = message.guild.get_channel(CANAL_PAINEL_ID) or message.channel
            await message.channel.send(fala(random.choice(_LIBERAR_PAINEL_PINK)))
            await grupos_cog._enviar_painel(canal)
            if canal != message.channel:
                await message.channel.send(f"✅ painel publicado em {canal.mention} 💀")
            self._ultimo_resp[message.channel.id] = now
            return

        if em_cooldown:
            await self._reagir_emojis(message, texto_lower)
            return

        gatilho = self._checar_gatilho(message.content)

        # 1) Gatilho ensinado/seed bateu
        if gatilho and (pink_chamado or random.random() < CHANCE_GATILHO_SEM_CHAMADO):
            resp = self._responder(gatilho)
            if resp:
                self._ultimo_resp[message.channel.id] = now
                async with message.channel.typing():
                    await asyncio.sleep(random.uniform(0.8, 1.8))
                await message.reply(fala(resp), mention_author=False)
                await self._reagir_emojis(message, texto_lower)
                return

        # 2) Chamado genérico, sem gatilho específico
        if pink_chamado and not gatilho:
            linha = random.choice(_SAUDACOES)
            self._ultimo_resp[message.channel.id] = now
            async with message.channel.typing():
                await asyncio.sleep(random.uniform(0.5, 1.2))
            await message.reply(fala(linha), mention_author=False)
            await self._reagir_emojis(message, texto_lower)
            return

        # 3) Aparição espontânea (chance baixa, só em canal quieto)
        if not pink_chamado and not gatilho and random.random() < CHANCE_APARICAO_ESPONTANEA:
            if not ultimo or (now - ultimo).total_seconds() > SILENCIO_MINIMO_APARICAO:
                linha = random.choice(_APARICOES)
                self._ultimo_resp[message.channel.id] = now
                async with message.channel.typing():
                    await asyncio.sleep(random.uniform(0.4, 1.0))
                await message.channel.send(fala(linha))
                return

        await self._reagir_emojis(message, texto_lower)

    # ── Comandos de aprendizado (moderação) ────────────

    @commands.command(name="ensinar", aliases=["teach"])
    @commands.has_permissions(manage_messages=True)
    async def ensinar(self, ctx: commands.Context, gatilho: str, *, resposta: str):
        """Ensina uma resposta nova a Pink. Uso: pk!ensinar <gatilho> <resposta>"""
        gatilho = gatilho.lower().strip()
        lista = self.db["respostas"].setdefault(gatilho, [])
        if resposta not in lista:
            lista.append(resposta)
        _salvar_dialogo(self.db)
        await ctx.send(embed=embed_ok(
            "✅ Aprendi!!",
            f"agora Pink pode responder **{gatilho}** com:\n*{resposta}*"
        ))

    @commands.command(name="esquecer", aliases=["forget"])
    @commands.has_permissions(manage_messages=True)
    async def esquecer(self, ctx: commands.Context, gatilho: str):
        """Remove todas as respostas de um gatilho. Uso: pk!esquecer <gatilho>"""
        gatilho = gatilho.lower().strip()
        if gatilho in self.db["respostas"]:
            del self.db["respostas"][gatilho]
            _salvar_dialogo(self.db)
            await ctx.send(embed=embed_ok("🗑️ Esqueci!!", f"Pink não lembra mais de **{gatilho}** 💀"))
        else:
            await ctx.send(embed=discord.Embed(
                title="🤔 Não conheço esse gatilho",
                description=f"nenhuma resposta pra **{gatilho}** 💀",
                color=COR_DOURADO
            ))

    @commands.command(name="gatilhos", aliases=["triggers"])
    @commands.has_permissions(manage_messages=True)
    async def listar_gatilhos(self, ctx: commands.Context):
        """Lista todos os gatilhos que Pink conhece."""
        chaves = sorted(self.db["respostas"].keys())
        if not chaves:
            await ctx.send("Pink ainda não conhece nenhum gatilho. ensine com `pk!ensinar` 💀")
            return
        chunks = [chaves[i:i + 25] for i in range(0, len(chaves), 25)]
        for i, chunk in enumerate(chunks[:3]):
            desc = "\n".join(
                f"• `{c}` ({len(self.db['respostas'][c])} resp.)"
                for c in chunk
            )
            embed = discord.Embed(
                title=f"📚 Gatilhos Conhecidos — Página {i + 1}/{len(chunks)}",
                description=desc, color=COR_NEUTRA, timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text="💀 Pink • aprendizado")
            await ctx.send(embed=embed)

    @commands.command(name="resposta")
    @commands.has_permissions(manage_messages=True)
    async def ver_resposta(self, ctx: commands.Context, *, gatilho: str):
        """Mostra as respostas de um gatilho. Uso: pk!resposta <gatilho>"""
        gatilho = gatilho.lower().strip()
        lista = self.db["respostas"].get(gatilho)
        if not lista:
            await ctx.send(f"Pink não conhece o gatilho **{gatilho}** 💀")
            return
        desc = "\n".join(f"　`{i+1}.` {r}" for i, r in enumerate(lista))
        embed = discord.Embed(title=f"💬 Respostas para: {gatilho}", description=desc, color=COR_NEUTRA)
        embed.set_footer(text="💀 Pink • aprendizado")
        await ctx.send(embed=embed)

    @commands.command(name="simular")
    @commands.has_permissions(manage_messages=True)
    async def simular(self, ctx: commands.Context, *, texto: str):
        """Simula a resposta de Pink a um texto. Uso: pk!simular <texto>"""
        gatilho = self._checar_gatilho(texto)
        if not gatilho:
            await ctx.send(embed=discord.Embed(
                title="🧪 Simulação", description=f"nenhum gatilho encontrado em `{texto[:100]}` 🤔",
                color=COR_DOURADO
            ))
            return
        resp = self._responder(gatilho)
        await ctx.send(embed=embed_pink(
            "🧪 Simulação",
            f"gatilho: `{gatilho}`\nresposta: {fala(resp)}"
        ))

    # ── Comandos públicos de interação ─────────────────

    @commands.command(name="f", aliases=["respeito", "pagarrespeitos"])
    async def pagar_respeitos(self, ctx: commands.Context):
        """Pague seus respeitos a Pink. Uso: pk!f"""
        uid = str(ctx.author.id)
        self.respeitos[uid] = self.respeitos.get(uid, 0) + 1
        _salvar_respeitos(self.respeitos)
        await ctx.send(fala(random.choice(_RESPEITOS_FALAS)))

    @commands.command(name="memorial", aliases=["hall", "placar"])
    async def memorial(self, ctx: commands.Context):
        """Mostra o placar de quem mais pagou respeitos a Pink."""
        if not self.respeitos:
            await ctx.send("ninguém pagou respeitos ainda. seja o(a) primeiro(a) com `pk!f` 💀")
            return
        top = sorted(self.respeitos.items(), key=lambda x: x[1], reverse=True)[:10]
        linhas = "\n".join(f"　`{qtd}x` — <@{uid}>" for uid, qtd in top)
        embed = discord.Embed(
            title="🪦 Memorial de Respeitos",
            description=linhas,
            color=COR_NEUTRA, timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="💀 Pink • use pk!f pra prestar seus respeitos")
        await ctx.send(embed=embed)

    @commands.command(name="invocar", aliases=["chamar", "summon"])
    async def invocar(self, ctx: commands.Context):
        """Força Pink a se manifestar. Uso: pk!invocar"""
        linha = random.choice(_INVOCACOES)
        async with ctx.typing():
            await asyncio.sleep(random.uniform(0.6, 1.3))
        await ctx.send(fala(linha))

    @commands.command(name="oraculo", aliases=["oráculo", "profecia"])
    async def oraculo(self, ctx: commands.Context):
        """Pede uma profecia curta e enigmática a Pink."""
        linha = random.choice(_ORACULOS)
        async with ctx.typing():
            await asyncio.sleep(random.uniform(0.6, 1.3))
        await ctx.send(fala(linha))

    @commands.command(name="sobre", aliases=["pink"])
    async def sobre(self, ctx: commands.Context):
        """Lore e apresentação de Pink."""
        embed = discord.Embed(
            title="💀 Eu sou Pink",
            description=(
                "a caveirinha guardiã da DOMINUS 💀\n\n"
                "não falo muito, não me agito, não preciso de holofote. "
                "só fico por perto, cuidando das coisas do meu jeito quieto.\n\n"
                "sério por fora, um pouco fofo por dentro — mas isso fica entre nós.\n\n"
                "use `pk!help` pra ver tudo que eu sei fazer."
            ),
            color=COR_NEUTRA, timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="💀 Pink Bot v1.0")
        await ctx.send(embed=embed)


# ══════════════════════════════════════════════════════════════════
#  🛡️  MÓDULO DE GRUPOS — painel com botão, cria cargo + chat + call
# ══════════════════════════════════════════════════════════════════

class CriarGrupoModal(discord.ui.Modal, title="Criar Grupo"):
    nome_grupo = discord.ui.TextInput(
        label="Nome do grupo (resumido)",
        placeholder="Ex.: Squad Duo",
        max_length=50,
    )
    cor_cargo = discord.ui.TextInput(
        label="Cor do cargo (hex)",
        placeholder="Ex.: 6C3483 ou #6C3483",
        max_length=7,
    )
    nome_chat = discord.ui.TextInput(
        label="Nome do chat (texto)",
        placeholder="Ex.: chat-squad-duo",
        max_length=50,
    )
    nome_call = discord.ui.TextInput(
        label="Nome da call (voz)",
        placeholder="Ex.: Call Squad Duo",
        max_length=50,
    )

    def __init__(self, cog: "GruposCog"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        guild = interaction.guild

        cor_bruta = self.cor_cargo.value.strip()
        if not _HEX_RE.match(cor_bruta):
            await interaction.followup.send(
                "❌ cor inválida!! use um hexadecimal tipo `6C3483` ou `#6C3483`.", ephemeral=True
            )
            return
        cor_int = int(cor_bruta.lstrip("#"), 16)

        categoria = guild.get_channel(CATEGORIA_ID)
        if not isinstance(categoria, discord.CategoryChannel):
            await interaction.followup.send(
                "❌ não encontrei a categoria configurada, avisa um admin 💀", ephemeral=True
            )
            return

        try:
            cargo = await guild.create_role(
                name=self.nome_grupo.value.strip(),
                colour=discord.Colour(cor_int),
                mentionable=True,
                reason=f"Grupo criado por {interaction.user} ({interaction.user.id})",
            )
        except discord.Forbidden:
            await interaction.followup.send("❌ não tenho permissão pra criar cargos.", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            cargo: discord.PermissionOverwrite(
                view_channel=True, connect=True, speak=True,
                send_messages=True, read_message_history=True,
            ),
        }
        if guild.me:
            overwrites[guild.me] = discord.PermissionOverwrite(view_channel=True, manage_channels=True)

        try:
            canal_texto = await guild.create_text_channel(
                name=self.nome_chat.value.strip(),
                category=categoria,
                overwrites=overwrites,
                reason=f"Grupo '{self.nome_grupo.value}' — dono: {interaction.user}",
            )
            canal_voz = await guild.create_voice_channel(
                name=self.nome_call.value.strip(),
                category=categoria,
                overwrites=overwrites,
                reason=f"Grupo '{self.nome_grupo.value}' — dono: {interaction.user}",
            )
        except discord.Forbidden:
            await cargo.delete(reason="Falha ao criar canais, revertendo cargo")
            await interaction.followup.send("❌ não tenho permissão pra criar canais.", ephemeral=True)
            return

        await interaction.user.add_roles(cargo, reason="Criador do grupo")

        self.cog.data[str(cargo.id)] = {
            "nome": self.nome_grupo.value.strip(),
            "owner_id": interaction.user.id,
            "canal_texto_id": canal_texto.id,
            "canal_voz_id": canal_voz.id,
        }
        _salvar_grupos(self.cog.data)

        embed = discord.Embed(
            title="✅ Grupo criado!!",
            description=(
                f"**Grupo:** {self.nome_grupo.value.strip()}\n"
                f"**Cargo:** {cargo.mention}\n"
                f"**Chat:** {canal_texto.mention}\n"
                f"**Call:** {canal_voz.mention}\n\n"
                f"pra quem mais você quer dar esse cargo?? escolhe no menu abaixo "
                f"(ou usa `pk!addmembro @pessoa` quando quiser, depois)!!"
            ),
            color=COR_ROXO_GRUPO,
        )
        view = AdicionarMembrosView(self.cog, cargo.id, interaction.user.id)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)


class AdicionarMembrosView(discord.ui.View):
    """Aparece logo depois que o grupo é criado, deixando o dono escolher
    direto na hora quem mais vai entrar, sem precisar digitar pk!addmembro."""

    def __init__(self, cog: "GruposCog", cargo_id: int, owner_id: int):
        super().__init__(timeout=600)  # 10 min pra escolher, depois o menu para de funcionar
        self.cog = cog
        self.cargo_id = cargo_id
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "só quem criou esse grupo pode adicionar membros por aqui!! 🚫", ephemeral=True
            )
            return False
        return True

    @discord.ui.select(
        cls=discord.ui.UserSelect,
        placeholder="escolha quem mais vai entrar no grupo...",
        min_values=1, max_values=25,
    )
    async def selecionar_membros(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        cargo = interaction.guild.get_role(self.cargo_id)
        if cargo is None:
            await interaction.response.send_message("❌ o cargo desse grupo não existe mais.", ephemeral=True)
            return

        adicionados, ja_tinham = [], []
        for membro in select.values:
            if not isinstance(membro, discord.Member):
                continue
            if cargo in membro.roles:
                ja_tinham.append(membro.mention)
                continue
            await membro.add_roles(cargo, reason=f"Adicionado por {interaction.user} pelo painel de grupo")
            adicionados.append(membro.mention)

        partes = []
        if adicionados:
            partes.append("✅ adicionado(s): " + ", ".join(adicionados))
        if ja_tinham:
            partes.append("ℹ️ já estavam no grupo: " + ", ".join(ja_tinham))
        await interaction.response.send_message("\n".join(partes) or "ninguém foi adicionado.", ephemeral=True)


class PainelGrupoView(discord.ui.View):
    def __init__(self, cog: "GruposCog"):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="Criar Grupo", emoji="💀",
        style=discord.ButtonStyle.primary, custom_id="grupos:criar_grupo",
    )
    async def criar_grupo(self, interaction: discord.Interaction, button: discord.ui.Button):
        cargo_permitido = interaction.guild.get_role(CARGO_PERMITIDO_ID)
        membro = interaction.user
        if cargo_permitido is None or cargo_permitido not in membro.roles:
            await interaction.response.send_message(
                "🚫 você não tem permissão pra criar um grupo!!", ephemeral=True
            )
            return
        await interaction.response.send_modal(CriarGrupoModal(self.cog))


class GruposCog(commands.Cog, name="Grupos"):
    """Painel de criação de grupos: cargo próprio + chat + call."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data = _carregar_grupos()
        self._painel_verificado = False
        bot.add_view(PainelGrupoView(self))  # registra a view como persistente (sobrevive a restart)

    def _grupos_do_dono(self, user_id: int):
        return [rid for rid, info in self.data.items() if info["owner_id"] == user_id]

    def _montar_embed_painel(self) -> discord.Embed:
        embed = discord.Embed(
            title="💀 Criar Grupo",
            description=(
                "clique no botão abaixo pra criar seu próprio grupo!!\n\n"
                "você vai poder escolher o nome, a cor do cargo, o nome do chat "
                "e o nome da call — tudo criado na hora, só pra você e quem você adicionar."
            ),
            color=COR_ROXO_GRUPO,
        )
        embed.set_image(url=IMAGEM_PAINEL)
        return embed

    async def _enviar_painel(self, canal: discord.abc.Messageable):
        await canal.send(embed=self._montar_embed_painel(), view=PainelGrupoView(self))

    @commands.Cog.listener()
    async def on_ready(self):
        if self._painel_verificado:
            return
        self._painel_verificado = True

        canal = self.bot.get_channel(CANAL_PAINEL_ID)
        if canal is None:
            return

        ja_existe = False
        try:
            async for msg in canal.history(limit=50):
                if msg.author.id == self.bot.user.id and msg.embeds and msg.embeds[0].title == "💀 Criar Grupo":
                    ja_existe = True
                    break
        except discord.Forbidden:
            return

        if not ja_existe:
            await self._enviar_painel(canal)

    @commands.command(name="painelgrupo")
    @commands.has_permissions(administrator=True)
    async def painel_grupo(self, ctx: commands.Context):
        """Publica o painel de criação de grupos no canal configurado. Uso: pk!painelgrupo"""
        canal = ctx.guild.get_channel(CANAL_PAINEL_ID) or ctx.channel
        await ctx.send(fala(random.choice(_LIBERAR_PAINEL_PINK)))
        await self._enviar_painel(canal)
        if canal != ctx.channel:
            await ctx.send(f"✅ painel publicado em {canal.mention}!!")

    @commands.command(name="addmembro", aliases=["addmember"])
    async def add_membro(self, ctx: commands.Context, membro: discord.Member, *, nome_grupo: str = None):
        """Adiciona alguém ao seu grupo. Uso: pk!addmembro @pessoa [nome do grupo]"""
        grupos = self._grupos_do_dono(ctx.author.id)
        if not grupos:
            await ctx.send("você não é dono(a) de nenhum grupo!! 🚫")
            return

        if nome_grupo:
            rid = next((r for r in grupos if self.data[r]["nome"].lower() == nome_grupo.lower()), None)
            if not rid:
                await ctx.send(f"não encontrei um grupo seu chamado **{nome_grupo}**!!")
                return
        elif len(grupos) == 1:
            rid = grupos[0]
        else:
            nomes = ", ".join(f"**{self.data[r]['nome']}**" for r in grupos)
            await ctx.send(f"você tem mais de um grupo!! especifique qual: {nomes}")
            return

        cargo = ctx.guild.get_role(int(rid))
        if cargo is None:
            await ctx.send("❌ o cargo desse grupo não existe mais.")
            return

        await membro.add_roles(cargo, reason=f"Adicionado por {ctx.author} ao grupo")
        await ctx.send(f"✅ {membro.mention} agora faz parte do grupo **{self.data[rid]['nome']}**!!")

    @commands.command(name="removermembro", aliases=["remmembro"])
    async def rem_membro(self, ctx: commands.Context, membro: discord.Member, *, nome_grupo: str = None):
        """Remove alguém do seu grupo. Uso: pk!removermembro @pessoa [nome do grupo]"""
        grupos = self._grupos_do_dono(ctx.author.id)
        if not grupos:
            await ctx.send("você não é dono(a) de nenhum grupo!! 🚫")
            return

        if nome_grupo:
            rid = next((r for r in grupos if self.data[r]["nome"].lower() == nome_grupo.lower()), None)
            if not rid:
                await ctx.send(f"não encontrei um grupo seu chamado **{nome_grupo}**!!")
                return
        elif len(grupos) == 1:
            rid = grupos[0]
        else:
            nomes = ", ".join(f"**{self.data[r]['nome']}**" for r in grupos)
            await ctx.send(f"você tem mais de um grupo!! especifique qual: {nomes}")
            return

        cargo = ctx.guild.get_role(int(rid))
        if cargo is None:
            await ctx.send("❌ o cargo desse grupo não existe mais.")
            return

        await membro.remove_roles(cargo, reason=f"Removido por {ctx.author} do grupo")
        await ctx.send(f"✅ {membro.mention} foi removido(a) do grupo **{self.data[rid]['nome']}**!!")

    @commands.command(name="encerrargrupo", aliases=["deletargrupo"])
    async def encerrar_grupo(self, ctx: commands.Context, *, nome_grupo: str = None):
        """Encerra seu grupo: apaga o cargo e os canais. Uso: pk!encerrargrupo [nome do grupo]"""
        grupos = self._grupos_do_dono(ctx.author.id)
        is_admin = ctx.author.guild_permissions.administrator
        if not grupos and not is_admin:
            await ctx.send("você não é dono(a) de nenhum grupo!! 🚫")
            return

        alvo_grupos = grupos if grupos else list(self.data.keys())
        if nome_grupo:
            rid = next((r for r in alvo_grupos if self.data[r]["nome"].lower() == nome_grupo.lower()), None)
            if not rid:
                await ctx.send(f"não encontrei o grupo **{nome_grupo}**!!")
                return
        elif len(alvo_grupos) == 1:
            rid = alvo_grupos[0]
        else:
            nomes = ", ".join(f"**{self.data[r]['nome']}**" for r in alvo_grupos)
            await ctx.send(f"especifique qual grupo encerrar: {nomes}")
            return

        info = self.data.pop(rid)
        _salvar_grupos(self.data)

        cargo = ctx.guild.get_role(int(rid))
        canal_texto = ctx.guild.get_channel(info["canal_texto_id"])
        canal_voz = ctx.guild.get_channel(info["canal_voz_id"])

        for obj in (cargo, canal_texto, canal_voz):
            if obj is not None:
                try:
                    await obj.delete(reason=f"Grupo encerrado por {ctx.author}")
                except discord.Forbidden:
                    pass

        await ctx.send(f"🗑️ grupo **{info['nome']}** encerrado!! cargo e canais removidos.")


# ══════════════════════════════════════════════════════════════════
#  🔗  MÓDULO DE CARGO VINCULADO — dá um 2º cargo automaticamente
# ══════════════════════════════════════════════════════════════════

class CargoVinculadoCog(commands.Cog, name="CargoVinculado"):
    """Dá um cargo extra automaticamente quando alguém recebe outro cargo específico."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        cargos_antes = {r.id for r in before.roles}
        cargos_depois = {r.id for r in after.roles}
        cargos_ganhos = cargos_depois - cargos_antes

        if CARGO_GATILHO_ID not in cargos_ganhos:
            return

        if CARGO_VINCULADO_ID in cargos_depois:
            return

        cargo_vinculado = after.guild.get_role(CARGO_VINCULADO_ID)
        if cargo_vinculado is None:
            print(f"⚠️ CargoVinculado: cargo {CARGO_VINCULADO_ID} não existe no servidor {after.guild.id}")
            return

        try:
            await after.add_roles(
                cargo_vinculado,
                reason=f"Cargo vinculado automático (ganhou o cargo {CARGO_GATILHO_ID})",
            )
        except discord.Forbidden:
            print(f"⚠️ CargoVinculado: sem permissão pra dar o cargo {CARGO_VINCULADO_ID} em {after.guild.id}")
        except discord.HTTPException as e:
            print(f"⚠️ CargoVinculado: erro ao adicionar cargo vinculado — {e}")


# ══════════════════════════════════════════════════════════════════
#  📋  MÓDULO DE FICHAS — formulário interativo (modal + confirmação)
# ══════════════════════════════════════════════════════════════════
#
# Como funciona:
#   1) o comando (pk!novomembro, pk!staff, pk!parceria <tipo>) manda um
#      cartão com um botão "📝 Preencher Ficha";
#   2) clicar abre um Modal com até 5 campos (limite do Discord por
#      modal!); se a ficha tem mais perguntas, ao enviar esse modal o
#      bot abre automaticamente o próximo, até acabar as perguntas;
#   3) no final, o bot manda uma prévia com tudo que foi respondido e
#      3 botões: ✅ Confirmar e Enviar / ✏️ Editar / ❌ Cancelar;
#   4) só quando a pessoa confirma é que a ficha preenchida é postada
#      no canal.
#
# NOTA (timeouts): as views usadas nesse fluxo têm timeout=None de
# propósito, pra que preencher uma ficha longa não expire enquanto a
# pessoa digita. Só o botão inicial do painel de Grupos (registrado
# com bot.add_view() e custom_id fixo) sobrevive de fato a um restart
# do bot; as views de ficha carregam dados parciais em memória e por
# isso não são persistentes entre reinícios.

COR_FICHA_MEMBRO     = 0xB39DDB
COR_FICHA_STAFF      = 0x4A235A
COR_FICHA_MAPA       = 0x2ECC71
COR_FICHA_COMERCIAL  = 0x3498DB
COR_FICHA_DJ         = 0x9B59B6
COR_FICHA_CLA        = COR_ROXO_GRUPO
COR_FICHA_COMUNIDADE = 0x1ABC9C

# form_key -> {titulo, cor, intro_launcher, encerramento, campos}
FORM_TEMPLATES: dict[str, dict] = {

    "novomembro": {
        "titulo": "Ficha — Novos Membros",
        "cor": COR_FICHA_MEMBRO,
        "intro_launcher": "clique no botão abaixo pra preencher sua ficha de entrada na DOMINUS 💀",
        "encerramento": "💀🖤 Seus ossos agora fazem parte da DOMINUS.\nSeja muito bem-vindo(a)! 🦴",
        "campos": [
            {"chave": "apelido", "label": "💀 Apelido no servidor DOMINUS", "estilo": "curto", "max": 32, "obrigatorio": True},
            {"chave": "nome", "label": "👤 Nome", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "idade", "label": "🎂 Idade", "estilo": "curto", "max": 3, "obrigatorio": True},
            {"chave": "roblox", "label": "🎮 Usuário Roblox", "estilo": "curto", "max": 40, "obrigatorio": True},
            {"chave": "discord_user", "label": "💬 Usuário Discord", "estilo": "curto", "max": 40, "obrigatorio": True},
            {"chave": "idioma", "label": "🌎 Idioma", "estilo": "curto", "max": 30, "obrigatorio": True},
            {"chave": "comunidade_anterior", "label": "❓ Já foi de algum clã/comunidade?", "estilo": "curto", "max": 100, "obrigatorio": False, "placeholder": "Não / Sim, qual"},
            {"chave": "indicacao", "label": "🤝 Alguém te recomendou? Quem?", "estilo": "curto", "max": 100, "obrigatorio": False, "placeholder": "Não / Sim, quem"},
            {"chave": "motivo", "label": "🦴 Por que quer entrar na DOMINUS?", "estilo": "longo", "max": 500, "obrigatorio": True},
        ],
    },

    "staff": {
        "titulo": "Ficha — Candidatura a Staff",
        "cor": COR_FICHA_STAFF,
        "intro_launcher": "clique no botão abaixo pra se candidatar à Staff da DOMINUS 🛡️💀",
        "encerramento": "🖤💀 Obrigado pelo interesse em fazer parte da Staff DOMINUS!\nSua ficha será avaliada pela nossa equipe.",
        "campos": [
            {"chave": "nome", "label": "👤 Nome", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "apelido", "label": "💀 Apelido no servidor", "estilo": "curto", "max": 32, "obrigatorio": True},
            {"chave": "idade", "label": "🎂 Idade", "estilo": "curto", "max": 3, "obrigatorio": True},
            {"chave": "discord_user", "label": "💬 Usuário Discord", "estilo": "curto", "max": 40, "obrigatorio": True},
            {"chave": "roblox", "label": "🎮 Usuário Roblox", "estilo": "curto", "max": 40, "obrigatorio": True},
            {"chave": "idioma", "label": "🌎 Idioma", "estilo": "curto", "max": 30, "obrigatorio": True},
            {"chave": "qual_staff", "label": "🛡️ Qual Staff deseja entrar?", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "staff_anterior", "label": "📋 Já foi Staff? Onde?", "estilo": "curto", "max": 100, "obrigatorio": False, "placeholder": "Não / Sim, onde"},
            {"chave": "disponibilidade", "label": "⏰ Disponibilidade", "estilo": "curto", "max": 100, "obrigatorio": True},
            {"chave": "motivo", "label": "🤝 Por que quer ser Staff na DOMINUS?", "estilo": "longo", "max": 500, "obrigatorio": True},
            {"chave": "funcoes", "label": "⚔️ Quais funções sabe desempenhar?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "conflitos", "label": "🧠 Como lidaria com conflitos?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "porque_voce", "label": "💀 Por que deveríamos escolher você?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "info_extra", "label": "📝 Informações adicionais", "estilo": "longo", "max": 300, "obrigatorio": False},
        ],
    },

    "parceria_mapa": {
        "titulo": "Parceria de Mapa",
        "cor": COR_FICHA_MAPA,
        "intro_launcher": "clique no botão abaixo pra propor sua parceria de mapa com a DOMINUS 🎮💀",
        "encerramento": "💀🦴 Obrigado pelo interesse em fazer parceria com a DOMINUS!\nSua proposta será analisada pela nossa equipe.",
        "campos": [
            {"chave": "nome_mapa", "label": "🎮 Nome do mapa", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "responsavel", "label": "👤 Responsável", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "representante1", "label": "👥 Representante 1", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "representante2", "label": "👥 Representante 2", "estilo": "curto", "max": 60, "obrigatorio": False},
            {"chave": "discord_reps", "label": "💬 Discord dos representantes", "estilo": "curto", "max": 100, "obrigatorio": True},
            {"chave": "link", "label": "🔗 Link do mapa", "estilo": "curto", "max": 200, "obrigatorio": True},
            {"chave": "grupo", "label": "🏷️ Grupo/Comunidade", "estilo": "curto", "max": 100, "obrigatorio": False},
            {"chave": "membros", "label": "👥 Quantidade de membros", "estilo": "curto", "max": 20, "obrigatorio": True},
            {"chave": "divulgacao", "label": "📢 Onde será divulgado?", "estilo": "curto", "max": 150, "obrigatorio": True},
            {"chave": "objetivo", "label": "🤝 O que busca com a parceria?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "oferece", "label": "💀 O que o mapa oferece à DOMINUS?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "info_extra", "label": "📝 Informações adicionais", "estilo": "longo", "max": 300, "obrigatorio": False},
        ],
    },

    "parceria_comercial": {
        "titulo": "Parceria Comercial",
        "cor": COR_FICHA_COMERCIAL,
        "intro_launcher": "clique no botão abaixo pra propor sua parceria comercial com a DOMINUS 💼💀",
        "encerramento": "💀🦴 Obrigado pelo interesse em fazer parceria com a DOMINUS!\nSua proposta será analisada pela nossa equipe.",
        "campos": [
            {"chave": "nome_empresa", "label": "🏢 Nome da empresa/projeto", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "responsavel", "label": "👤 Responsável", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "representante1", "label": "👥 Representante 1", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "representante2", "label": "👥 Representante 2", "estilo": "curto", "max": 60, "obrigatorio": False},
            {"chave": "discord_reps", "label": "💬 Discord dos representantes", "estilo": "curto", "max": 100, "obrigatorio": True},
            {"chave": "link", "label": "🔗 Link", "estilo": "curto", "max": 200, "obrigatorio": False},
            {"chave": "redes", "label": "📱 Redes sociais", "estilo": "curto", "max": 150, "obrigatorio": False},
            {"chave": "area", "label": "💼 Área de atuação", "estilo": "curto", "max": 100, "obrigatorio": True},
            {"chave": "divulgacao", "label": "📢 Onde será divulgado?", "estilo": "curto", "max": 150, "obrigatorio": True},
            {"chave": "tipo_parceria", "label": "🤝 Tipo de parceria desejada", "estilo": "curto", "max": 150, "obrigatorio": True},
            {"chave": "oferece", "label": "📦 O que oferece à DOMINUS?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "espera", "label": "💀 O que espera da DOMINUS?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "info_extra", "label": "📝 Informações adicionais", "estilo": "longo", "max": 300, "obrigatorio": False},
        ],
    },

    "parceria_dj": {
        "titulo": "Parceria DJ",
        "cor": COR_FICHA_DJ,
        "intro_launcher": "clique no botão abaixo pra propor sua parceria de DJ com a DOMINUS 🎧💀",
        "encerramento": "💀🦴 Obrigado pelo interesse em fazer parceria com a DOMINUS!\nSua proposta será analisada pela nossa equipe.",
        "campos": [
            {"chave": "nome_artistico", "label": "🎧 Nome artístico", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "responsavel", "label": "👤 Responsável", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "representante1", "label": "👥 Representante 1", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "representante2", "label": "👥 Representante 2", "estilo": "curto", "max": 60, "obrigatorio": False},
            {"chave": "discord_reps", "label": "💬 Discord dos representantes", "estilo": "curto", "max": 100, "obrigatorio": True},
            {"chave": "estilo_musical", "label": "🎶 Estilo musical", "estilo": "curto", "max": 100, "obrigatorio": True},
            {"chave": "perfil", "label": "🔗 Perfil/Canal", "estilo": "curto", "max": 200, "obrigatorio": False},
            {"chave": "redes", "label": "📱 Redes sociais", "estilo": "curto", "max": 150, "obrigatorio": False},
            {"chave": "onde_apresenta", "label": "🎤 Onde costuma se apresentar?", "estilo": "curto", "max": 150, "obrigatorio": True},
            {"chave": "divulgacao", "label": "📢 Onde será divulgado?", "estilo": "curto", "max": 150, "obrigatorio": True},
            {"chave": "objetivo", "label": "🤝 O que busca com a parceria?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "oferece", "label": "💀 O que oferece à DOMINUS?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "espera", "label": "🦴 O que espera da DOMINUS?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "info_extra", "label": "📝 Informações adicionais", "estilo": "longo", "max": 300, "obrigatorio": False},
        ],
    },

    "parceria_cla": {
        "titulo": "Parceria de Clã",
        "cor": COR_FICHA_CLA,
        "intro_launcher": "clique no botão abaixo pra propor a parceria do seu clã com a DOMINUS 🏷️💀",
        "encerramento": "💀🦴 Obrigado pelo interesse em fazer parceria com a DOMINUS!\nSua proposta será analisada pela nossa equipe.",
        "campos": [
            {"chave": "nome_cla", "label": "🏷️ Nome do clã", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "dono", "label": "👑 Dono(a)/Líder", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "representante1", "label": "👥 Representante 1", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "representante2", "label": "👥 Representante 2", "estilo": "curto", "max": 60, "obrigatorio": False},
            {"chave": "discord_reps", "label": "💬 Discord dos representantes", "estilo": "curto", "max": 100, "obrigatorio": True},
            {"chave": "convite", "label": "🔗 Convite do servidor", "estilo": "curto", "max": 200, "obrigatorio": True},
            {"chave": "membros", "label": "👥 Quantidade de membros", "estilo": "curto", "max": 20, "obrigatorio": True},
            {"chave": "atividade", "label": "🎮 Atividade principal", "estilo": "curto", "max": 100, "obrigatorio": True},
            {"chave": "divulgacao", "label": "📢 Onde será divulgado?", "estilo": "curto", "max": 150, "obrigatorio": True},
            {"chave": "objetivo", "label": "🤝 O que busca com a parceria?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "oferece", "label": "💀 O que seu clã oferece à DOMINUS?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "espera", "label": "🦴 O que espera da DOMINUS?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "info_extra", "label": "📝 Informações adicionais", "estilo": "longo", "max": 300, "obrigatorio": False},
        ],
    },

    "parceria_comunidade": {
        "titulo": "Parceria de Comunidade",
        "cor": COR_FICHA_COMUNIDADE,
        "intro_launcher": "clique no botão abaixo pra propor a parceria da sua comunidade com a DOMINUS 🌐💀",
        "encerramento": "💀🦴 Obrigado pelo interesse em fazer parceria com a DOMINUS!\nSerá um prazer conhecer sua comunidade e analisar a proposta.",
        "campos": [
            {"chave": "nome_comunidade", "label": "🏷️ Nome da comunidade", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "admin", "label": "👑 Administrador(a)/Fundador(a)", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "representante1", "label": "👥 Representante 1", "estilo": "curto", "max": 60, "obrigatorio": True},
            {"chave": "representante2", "label": "👥 Representante 2", "estilo": "curto", "max": 60, "obrigatorio": False},
            {"chave": "discord_reps", "label": "💬 Discord dos representantes", "estilo": "curto", "max": 100, "obrigatorio": True},
            {"chave": "convite", "label": "🔗 Convite/Link da comunidade", "estilo": "curto", "max": 200, "obrigatorio": True},
            {"chave": "membros", "label": "👥 Quantidade de membros", "estilo": "curto", "max": 20, "obrigatorio": True},
            {"chave": "foco", "label": "🎯 Foco/atividade da comunidade", "estilo": "curto", "max": 100, "obrigatorio": True},
            {"chave": "divulgacao", "label": "📢 Onde será divulgado?", "estilo": "curto", "max": 150, "obrigatorio": True},
            {"chave": "objetivo", "label": "🤝 O que busca com a parceria?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "oferece", "label": "💀 O que sua comunidade oferece à DOMINUS?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "espera", "label": "🦴 O que espera da DOMINUS?", "estilo": "longo", "max": 400, "obrigatorio": True},
            {"chave": "info_extra", "label": "📝 Informações adicionais", "estilo": "longo", "max": 300, "obrigatorio": False},
        ],
    },
}

_TIPOS_PARCERIA_KEYS = {
    "mapa": "parceria_mapa",
    "comercial": "parceria_comercial",
    "dj": "parceria_dj",
    "cla": "parceria_cla",
    "comunidade": "parceria_comunidade",
}


def _normalizar(texto: str) -> str:
    """minúsculas, sem espaço nas pontas e sem acentos (clã -> cla)."""
    import unicodedata
    texto = texto.lower().strip()
    return "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )


def _total_etapas(form_key: str) -> int:
    """Quantos modais (etapas) essa ficha precisa, respeitando o limite de 5 campos por modal."""
    total_campos = len(FORM_TEMPLATES[form_key]["campos"])
    return (total_campos + 4) // 5


def _campos_da_etapa(form_key: str, etapa: int) -> list[dict]:
    campos = FORM_TEMPLATES[form_key]["campos"]
    inicio = etapa * 5
    return campos[inicio:inicio + 5]


class FichaModalStep(discord.ui.Modal):
    """Um modal com até 5 campos de uma ficha. Se sobrarem mais perguntas,
    ao enviar este modal o próximo é aberto automaticamente (encadeado)."""

    def __init__(self, cog: "FichasCog", form_key: str, etapa: int, respostas: dict):
        template = FORM_TEMPLATES[form_key]
        total = _total_etapas(form_key)
        titulo = template["titulo"]
        if total > 1:
            titulo = f"{titulo} ({etapa + 1}/{total})"
        super().__init__(title=titulo[:45])

        self.cog = cog
        self.form_key = form_key
        self.etapa = etapa
        self.total_etapas = total
        self.respostas = dict(respostas)
        self.campos = _campos_da_etapa(form_key, etapa)
        self._inputs: dict[str, discord.ui.TextInput] = {}

        for campo in self.campos:
            valor_anterior = self.respostas.get(campo["chave"], "")
            entrada = discord.ui.TextInput(
                label=campo["label"][:45],
                style=discord.TextStyle.paragraph if campo["estilo"] == "longo" else discord.TextStyle.short,
                required=campo.get("obrigatorio", True),
                max_length=campo.get("max", 300),
                placeholder=campo.get("placeholder"),
                default=valor_anterior or None,
            )
            self._inputs[campo["chave"]] = entrada
            self.add_item(entrada)

    async def on_submit(self, interaction: discord.Interaction):
        for campo in self.campos:
            self.respostas[campo["chave"]] = self._inputs[campo["chave"]].value.strip()

        proxima_etapa = self.etapa + 1
        if proxima_etapa < self.total_etapas:
            # o Discord NÃO permite abrir um modal direto de dentro do
            # on_submit de outro modal (erro 50035). Por isso mandamos um
            # botão-ponte: ele é uma interação de BOTÃO, e essa sim pode
            # abrir o próximo modal.
            template = FORM_TEMPLATES[self.form_key]
            embed = discord.Embed(
                title=f"📝 {template['titulo']} — etapa {self.etapa + 1}/{self.total_etapas} concluída!!",
                description="clique no botão abaixo pra continuar preenchendo sua ficha!!",
                color=template["cor"],
            )
            view = ContinuarFichaView(self.cog, self.form_key, proxima_etapa, self.respostas, interaction.user.id)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            return

        embed = self.cog._embed_preview(self.form_key, self.respostas)
        view = ConfirmarFichaView(self.cog, self.form_key, self.respostas, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        traceback.print_exception(type(error), error, error.__traceback__)
        mensagem = "❌ deu ruim ao processar sua ficha, tenta de novo!!"
        if interaction.response.is_done():
            await interaction.followup.send(mensagem, ephemeral=True)
        else:
            await interaction.response.send_message(mensagem, ephemeral=True)


class ContinuarFichaView(discord.ui.View):
    """Botão-ponte entre uma etapa e a próxima do modal encadeado."""

    def __init__(self, cog: "FichasCog", form_key: str, proxima_etapa: int, respostas: dict, autor_id: int):
        super().__init__(timeout=None)
        self.cog = cog
        self.form_key = form_key
        self.proxima_etapa = proxima_etapa
        self.respostas = respostas
        self.autor_id = autor_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.autor_id:
            await interaction.response.send_message("essa ficha não é sua!! 🚫", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Continuar Ficha", emoji="➡️", style=discord.ButtonStyle.primary)
    async def continuar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            FichaModalStep(self.cog, self.form_key, self.proxima_etapa, self.respostas)
        )
        self.stop()


class ConfirmarFichaView(discord.ui.View):
    """Prévia da ficha preenchida, com botões pra confirmar, editar ou cancelar."""

    def __init__(self, cog: "FichasCog", form_key: str, respostas: dict, autor_id: int):
        super().__init__(timeout=None)
        self.cog = cog
        self.form_key = form_key
        self.respostas = respostas
        self.autor_id = autor_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.autor_id:
            await interaction.response.send_message("essa ficha não é sua!! 🚫", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Confirmar e Enviar", emoji="✅", style=discord.ButtonStyle.success)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed_final = self.cog._embed_final(self.form_key, self.respostas, interaction.user)
        await interaction.channel.send(embed=embed_final)
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            content="✅ ficha enviada com sucesso, obrigado(a)!!", embed=None, view=self
        )
        self.stop()

    @discord.ui.button(label="Editar", emoji="✏️", style=discord.ButtonStyle.secondary)
    async def editar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            FichaModalStep(self.cog, self.form_key, 0, self.respostas)
        )
        self.stop()

    @discord.ui.button(label="Cancelar", emoji="❌", style=discord.ButtonStyle.danger)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="❌ ficha cancelada.", embed=None, view=self)
        self.stop()


class IniciarFichaView(discord.ui.View):
    """Cartão inicial com o botão que abre a primeira etapa do formulário."""

    def __init__(self, cog: "FichasCog", form_key: str):
        super().__init__(timeout=None)
        self.cog = cog
        self.form_key = form_key

    @discord.ui.button(label="Preencher Ficha", emoji="📝", style=discord.ButtonStyle.primary)
    async def preencher(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(FichaModalStep(self.cog, self.form_key, 0, {}))


class FichasCog(commands.Cog, name="Fichas"):
    """Fichas de inscrição interativas: novos membros, candidatura a Staff e parcerias."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _embed_lancamento(self, form_key: str) -> discord.Embed:
        template = FORM_TEMPLATES[form_key]
        total = _total_etapas(form_key)
        desc = template["intro_launcher"]
        if total > 1:
            desc += f"\n\n*a ficha tem {len(template['campos'])} perguntas, divididas em {total} etapas rápidas.*"
        embed = discord.Embed(
            title=f"💀 {template['titulo']}",
            description=desc,
            color=template["cor"],
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_footer(text=FOOTER_DOMINUS)
        return embed

    def _montar_embed_respostas(self, form_key: str, respostas: dict, titulo_prefixo: str = None) -> discord.Embed:
        template = FORM_TEMPLATES[form_key]
        linhas = ["💀 DOMINUS 💀"]
        for campo in template["campos"]:
            valor = (respostas.get(campo["chave"]) or "").strip()
            if not valor:
                valor = "*não informado*"
            linhas.append(f"{campo['label']}\n{valor}")
        if template.get("encerramento"):
            linhas.append(template["encerramento"])

        titulo = template["titulo"]
        if titulo_prefixo:
            titulo = f"{titulo_prefixo} — {titulo}"

        embed = discord.Embed(
            title=f"💀 {titulo}",
            description="\n\n".join(linhas),
            color=template["cor"],
            timestamp=datetime.now(timezone.utc),
        )
        return embed

    def _embed_preview(self, form_key: str, respostas: dict) -> discord.Embed:
        embed = self._montar_embed_respostas(form_key, respostas, titulo_prefixo="🔎 Confira sua ficha")
        embed.set_footer(text="revise as respostas!! confirme, edite ou cancele abaixo.")
        return embed

    def _embed_final(self, form_key: str, respostas: dict, autor: discord.abc.User) -> discord.Embed:
        embed = self._montar_embed_respostas(form_key, respostas)
        embed.set_footer(text=f"{FOOTER_DOMINUS} • enviado por {autor.display_name}")
        return embed

    @commands.command(name="novomembro", aliases=["ficha", "newmember"])
    async def novo_membro(self, ctx: commands.Context):
        """Abre a ficha interativa de novos membros. Uso: pk!novomembro"""
        await ctx.send(embed=self._embed_lancamento("novomembro"), view=IniciarFichaView(self, "novomembro"))

    @commands.command(name="staff", aliases=["candidaturastaff", "recrutamento"])
    async def staff_form(self, ctx: commands.Context):
        """Abre a ficha interativa de candidatura a Staff. Uso: pk!staff"""
        await ctx.send(embed=self._embed_lancamento("staff"), view=IniciarFichaView(self, "staff"))

    @commands.command(name="parceria", aliases=["parcerias"])
    async def parceria(self, ctx: commands.Context, tipo: str = None):
        """Abre a ficha interativa de parceria. Uso: pk!parceria <mapa|comercial|dj|cla|comunidade>"""
        if tipo is None:
            embed = discord.Embed(
                title="🤝 Parcerias DOMINUS",
                description=(
                    "escolha o tipo de parceria que você quer propor!!\n\n"
                    "`pk!parceria mapa` — parceria de mapa\n"
                    "`pk!parceria comercial` — parceria comercial\n"
                    "`pk!parceria dj` — parceria com DJ\n"
                    "`pk!parceria cla` — parceria de clã\n"
                    "`pk!parceria comunidade` — parceria de comunidade"
                ),
                color=COR_ROXO_GRUPO, timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=FOOTER_DOMINUS)
            await ctx.send(embed=embed)
            return

        chave = _normalizar(tipo)
        form_key = _TIPOS_PARCERIA_KEYS.get(chave)
        if not form_key:
            await ctx.send(embed=embed_erro("tipo de parceria inválido!! use `mapa`, `comercial`, `dj`, `cla` ou `comunidade`!!"))
            return
        await ctx.send(embed=self._embed_lancamento(form_key), view=IniciarFichaView(self, form_key))

    @commands.command(name="fichas")
    async def listar_fichas(self, ctx: commands.Context):
        """Lista todas as fichas disponíveis."""
        embed = discord.Embed(
            title="📋 Fichas Disponíveis",
            description=(
                "todas as fichas abrem um formulário interativo: preencha, confira a prévia "
                "e só então confirme o envio!!\n\n"
                "`pk!novomembro` — ficha de novos membros\n"
                "`pk!staff` — candidatura a Staff\n"
                "`pk!parceria mapa` — parceria de mapa\n"
                "`pk!parceria comercial` — parceria comercial\n"
                "`pk!parceria dj` — parceria com DJ\n"
                "`pk!parceria cla` — parceria de clã\n"
                "`pk!parceria comunidade` — parceria de comunidade"
            ),
            color=COR_NEUTRA, timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=FOOTER_DOMINUS)
        await ctx.send(embed=embed)


# ══════════════════════════════════════════════════════════════════
#  🕵️  MÓDULO DE AUDITORIA — log total do servidor
# ══════════════════════════════════════════════════════════════════
#
# Tudo que o Discord permite descobrir é logado no canal CANAL_AUDITORIA_ID:
# criação/edição/exclusão de canais e cargos, mensagens apagadas/editadas,
# entrada/saída/expulsão/ban de membros, apelido e cargos de membros mudando,
# quem entrou/saiu/foi movido de call, mute/deafen por moderação, e mudanças
# nas configurações do servidor.
#
# DE PROPÓSITO NÃO logamos apenas a REORDENAÇÃO de cargos — se um cargo
# mudar de posição e mais nada, o evento é ignorado. Qualquer outra
# mudança no cargo continua sendo logada normalmente.
#
# LIMITAÇÃO DO DISCORD: pra saber quem apagou/editou algo, o bot consulta
# o Audit Log do servidor (exige a permissão "Ver Registro de Auditoria").
# Se essa permissão não existir, o campo "responsável" fica em branco —
# isso é uma limitação da API do Discord, não do bot.

COR_LOG_CANAL      = 0x3498DB
COR_LOG_CARGO      = 0x9B59B6
COR_LOG_MSG_DEL    = 0xE74C3C
COR_LOG_MSG_EDIT   = 0xF1C40F
COR_LOG_VOZ        = 0x1ABC9C
COR_LOG_MEMBRO_IN  = 0x2ECC71
COR_LOG_MEMBRO_OUT = 0xE74C3C
COR_LOG_SERVIDOR   = 0x95A5A6

JANELA_AUDIT_LOG = 6  # segundos: até quanto tempo atrás aceitamos uma entrada do audit log como "a causa" do evento


async def _achar_responsavel(guild: discord.Guild, action: "discord.AuditLogAction", target_id: int | None = None, janela: int = JANELA_AUDIT_LOG):
    """Procura no Audit Log do servidor quem foi o responsável por uma ação recente."""
    me = guild.me
    if me is None or not me.guild_permissions.view_audit_log:
        return None
    try:
        agora = datetime.now(timezone.utc)
        async for entry in guild.audit_logs(action=action, limit=8):
            if (agora - entry.created_at).total_seconds() > janela:
                break
            if target_id is not None:
                alvo = getattr(entry.target, "id", None)
                if alvo != target_id:
                    continue
            return entry.user
    except (discord.Forbidden, discord.HTTPException):
        return None
    return None


class AuditoriaCog(commands.Cog, name="Auditoria"):
    """Log total de ações do servidor, postado em CANAL_AUDITORIA_ID."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._posicoes_pendentes: dict[int, dict[int, str]] = defaultdict(dict)
        self._posicoes_task: dict[int, asyncio.Task] = {}

    async def _log(self, guild: discord.Guild, embed: discord.Embed):
        if guild is None:
            return
        canal = guild.get_channel(CANAL_AUDITORIA_ID)
        if canal is None:
            return
        embed.set_footer(text="💀 Pink • Auditoria")
        embed.timestamp = datetime.now(timezone.utc)
        try:
            await canal.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.guild is None or message.author is None:
            return
        if message.author.id == self.bot.user.id:
            return

        responsavel = await _achar_responsavel(
            message.guild, discord.AuditLogAction.message_delete, target_id=message.author.id
        )

        embed = discord.Embed(title="🗑️ Mensagem apagada", color=COR_LOG_MSG_DEL)
        embed.add_field(name="Autor", value=f"{message.author.mention} (`{message.author}`)", inline=False)
        embed.add_field(name="Canal", value=message.channel.mention if hasattr(message.channel, "mention") else str(message.channel), inline=False)
        conteudo = message.content.strip() if message.content else ""
        if not conteudo and message.attachments:
            conteudo = f"*(sem texto — {len(message.attachments)} anexo(s))*"
        elif not conteudo:
            conteudo = "*(sem texto — provavelmente só embed/sticker)*"
        embed.add_field(name="Conteúdo", value=conteudo[:1000], inline=False)
        if responsavel and responsavel.id != message.author.id:
            embed.add_field(name="Apagada por", value=f"{responsavel.mention} (moderação)", inline=False)
        else:
            embed.add_field(name="Apagada por", value="provavelmente pelo(a) próprio(a) autor(a) *(ou não identificado)*", inline=False)
        await self._log(message.guild, embed)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: list[discord.Message]):
        if not messages:
            return
        guild = messages[0].guild
        canal = messages[0].channel
        if guild is None:
            return
        responsavel = await _achar_responsavel(guild, discord.AuditLogAction.message_bulk_delete, target_id=canal.id)
        embed = discord.Embed(
            title="🗑️🗑️ Mensagens apagadas em massa",
            description=f"**{len(messages)}** mensagens apagadas em {canal.mention if hasattr(canal, 'mention') else canal}",
            color=COR_LOG_MSG_DEL,
        )
        if responsavel:
            embed.add_field(name="Apagadas por", value=responsavel.mention, inline=False)
        await self._log(guild, embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.guild is None or before.author.bot:
            return
        if before.content == after.content:
            return

        embed = discord.Embed(title="✏️ Mensagem editada", color=COR_LOG_MSG_EDIT)
        embed.add_field(name="Autor", value=f"{before.author.mention} (`{before.author}`)", inline=False)
        embed.add_field(name="Canal", value=before.channel.mention, inline=False)
        embed.add_field(name="Antes", value=(before.content.strip()[:1000] or "*vazio*"), inline=False)
        embed.add_field(name="Depois", value=(after.content.strip()[:1000] or "*vazio*"), inline=False)
        embed.add_field(name="Link", value=f"[ir até a mensagem]({after.jump_url})", inline=False)
        await self._log(before.guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        responsavel = await _achar_responsavel(channel.guild, discord.AuditLogAction.channel_create, target_id=channel.id)
        embed = discord.Embed(
            title="📁 Canal criado",
            description=f"**{channel.name}** (`{channel.type}`)\nID: `{channel.id}`",
            color=COR_LOG_CANAL,
        )
        if responsavel:
            embed.add_field(name="Criado por", value=responsavel.mention, inline=False)
        await self._log(channel.guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        responsavel = await _achar_responsavel(channel.guild, discord.AuditLogAction.channel_delete, target_id=channel.id)
        embed = discord.Embed(
            title="🗑️ Canal apagado",
            description=f"**{channel.name}** (`{channel.type}`)\nID: `{channel.id}`",
            color=COR_LOG_CANAL,
        )
        if responsavel:
            embed.add_field(name="Apagado por", value=responsavel.mention, inline=False)
        await self._log(channel.guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        mudancas = []
        if before.name != after.name:
            mudancas.append(f"**Nome:** `{before.name}` → `{after.name}`")
        if getattr(before, "topic", None) != getattr(after, "topic", None):
            mudancas.append("**Tópico alterado**")
        if getattr(before, "nsfw", None) != getattr(after, "nsfw", None):
            mudancas.append(f"**NSFW:** `{before.nsfw}` → `{after.nsfw}`")
        if getattr(before, "slowmode_delay", None) != getattr(after, "slowmode_delay", None):
            mudancas.append(f"**Slowmode:** `{before.slowmode_delay}s` → `{after.slowmode_delay}s`")
        if getattr(before, "bitrate", None) != getattr(after, "bitrate", None):
            mudancas.append(f"**Bitrate:** `{before.bitrate}` → `{after.bitrate}`")
        if getattr(before, "user_limit", None) != getattr(after, "user_limit", None):
            mudancas.append(f"**Limite de usuários:** `{before.user_limit}` → `{after.user_limit}`")
        if getattr(before, "category", None) != getattr(after, "category", None):
            cat_antes = before.category.name if getattr(before, "category", None) else "Nenhuma"
            cat_depois = after.category.name if getattr(after, "category", None) else "Nenhuma"
            mudancas.append(f"**Categoria:** `{cat_antes}` → `{cat_depois}`")
        if before.overwrites != after.overwrites:
            mudancas.append("**Permissões do canal foram alteradas**")

        mudou_posicao = getattr(before, "position", None) != getattr(after, "position", None)

        if not mudancas:
            if mudou_posicao:
                self._agendar_log_posicao(after)
            return

        responsavel = await _achar_responsavel(after.guild, discord.AuditLogAction.channel_update, target_id=after.id)
        embed = discord.Embed(
            title="🔧 Canal atualizado",
            description=f"{after.mention if hasattr(after, 'mention') else after.name}\n\n" + "\n".join(mudancas),
            color=COR_LOG_CANAL,
        )
        if responsavel:
            embed.add_field(name="Alterado por", value=responsavel.mention, inline=False)
        await self._log(after.guild, embed)

    def _agendar_log_posicao(self, channel: discord.abc.GuildChannel):
        guild = channel.guild
        self._posicoes_pendentes[guild.id][channel.id] = channel.name

        task_antiga = self._posicoes_task.get(guild.id)
        if task_antiga and not task_antiga.done():
            task_antiga.cancel()
        self._posicoes_task[guild.id] = asyncio.create_task(self._flush_posicoes(guild))

    async def _flush_posicoes(self, guild: discord.Guild):
        try:
            await asyncio.sleep(2.0)
        except asyncio.CancelledError:
            return

        pendentes = self._posicoes_pendentes.pop(guild.id, {})
        self._posicoes_task.pop(guild.id, None)
        if not pendentes:
            return

        responsavel = await _achar_responsavel(guild, discord.AuditLogAction.channel_update)
        nomes = ", ".join(f"`{nome}`" for nome in pendentes.values())
        embed = discord.Embed(
            title="↕️ Canais reordenados",
            description=f"canais que mudaram de posição na lista: {nomes}",
            color=COR_LOG_CANAL,
        )
        if responsavel:
            embed.add_field(name="Provavelmente movido por", value=responsavel.mention, inline=False)
        else:
            embed.add_field(
                name="Responsável",
                value="não identificado *(o Discord nem sempre registra reordenação de canal no Audit Log)*",
                inline=False,
            )
        await self._log(guild, embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        responsavel = await _achar_responsavel(role.guild, discord.AuditLogAction.role_create, target_id=role.id)
        embed = discord.Embed(
            title="🎭 Cargo criado",
            description=f"{role.mention} (`{role.name}`)\nID: `{role.id}`",
            color=COR_LOG_CARGO,
        )
        if responsavel:
            embed.add_field(name="Criado por", value=responsavel.mention, inline=False)
        await self._log(role.guild, embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        responsavel = await _achar_responsavel(role.guild, discord.AuditLogAction.role_delete, target_id=role.id)
        embed = discord.Embed(
            title="🗑️ Cargo apagado",
            description=f"**{role.name}**\nID: `{role.id}`",
            color=COR_LOG_CARGO,
        )
        if responsavel:
            embed.add_field(name="Apagado por", value=responsavel.mention, inline=False)
        await self._log(role.guild, embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        mudancas = []
        if before.name != after.name:
            mudancas.append(f"**Nome:** `{before.name}` → `{after.name}`")
        if before.colour != after.colour:
            mudancas.append(f"**Cor:** `{before.colour}` → `{after.colour}`")
        if before.hoist != after.hoist:
            mudancas.append(f"**Exibir separado:** `{before.hoist}` → `{after.hoist}`")
        if before.mentionable != after.mentionable:
            mudancas.append(f"**Mencionável:** `{before.mentionable}` → `{after.mentionable}`")
        if before.permissions != after.permissions:
            antes_perms = {p for p, v in before.permissions if v}
            depois_perms = {p for p, v in after.permissions if v}
            ganhas = depois_perms - antes_perms
            perdidas = antes_perms - depois_perms
            if ganhas:
                mudancas.append(f"**Permissões adicionadas:** {', '.join(sorted(ganhas))}")
            if perdidas:
                mudancas.append(f"**Permissões removidas:** {', '.join(sorted(perdidas))}")

        if not mudancas:
            return  # só a posição mudou (ou nada mudou) — ignorado de propósito

        responsavel = await _achar_responsavel(after.guild, discord.AuditLogAction.role_update, target_id=after.id)
        embed = discord.Embed(
            title="🔧 Cargo atualizado",
            description=f"{after.mention}\n\n" + "\n".join(mudancas),
            color=COR_LOG_CARGO,
        )
        if responsavel:
            embed.add_field(name="Alterado por", value=responsavel.mention, inline=False)
        await self._log(after.guild, embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        guild = member.guild

        if before.channel != after.channel:
            if before.channel is None and after.channel is not None:
                embed = discord.Embed(
                    title="🔊 Entrou em uma call",
                    description=f"{member.mention} entrou em {after.channel.mention}",
                    color=COR_LOG_VOZ,
                )
                await self._log(guild, embed)
            elif before.channel is not None and after.channel is None:
                embed = discord.Embed(
                    title="🔇 Saiu de uma call",
                    description=f"{member.mention} saiu de {before.channel.mention}",
                    color=COR_LOG_VOZ,
                )
                await self._log(guild, embed)
            elif before.channel is not None and after.channel is not None:
                responsavel = await _achar_responsavel(guild, discord.AuditLogAction.member_move, target_id=None)
                embed = discord.Embed(
                    title="🔀 Mudou de call",
                    description=f"{member.mention}: {before.channel.mention} → {after.channel.mention}",
                    color=COR_LOG_VOZ,
                )
                if responsavel and responsavel.id != member.id:
                    embed.add_field(name="Movido por", value=responsavel.mention, inline=False)
                await self._log(guild, embed)

        if before.mute != after.mute or before.deaf != after.deaf:
            responsavel = await _achar_responsavel(guild, discord.AuditLogAction.member_update, target_id=member.id)
            partes = []
            if before.mute != after.mute:
                partes.append(f"**Mutado (servidor):** `{before.mute}` → `{after.mute}`")
            if before.deaf != after.deaf:
                partes.append(f"**Ensurdecido (servidor):** `{before.deaf}` → `{after.deaf}`")
            embed = discord.Embed(
                title="🎙️ Voz — mute/deafen alterado",
                description=f"{member.mention}\n\n" + "\n".join(partes),
                color=COR_LOG_VOZ,
            )
            if responsavel:
                embed.add_field(name="Alterado por", value=responsavel.mention, inline=False)
            await self._log(guild, embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        criada_em = int(member.created_at.timestamp())
        embed = discord.Embed(
            title="📥 Membro entrou",
            description=(
                f"{member.mention} (`{member}`)\nID: `{member.id}`\n"
                f"Conta criada: <t:{criada_em}:R>"
            ),
            color=COR_LOG_MEMBRO_IN,
        )
        await self._log(member.guild, embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        responsavel = await _achar_responsavel(member.guild, discord.AuditLogAction.kick, target_id=member.id)
        if responsavel:
            embed = discord.Embed(
                title="👢 Membro expulso (kick)",
                description=f"{member.mention} (`{member}`)\nID: `{member.id}`",
                color=COR_LOG_MEMBRO_OUT,
            )
            embed.add_field(name="Expulso por", value=responsavel.mention, inline=False)
        else:
            embed = discord.Embed(
                title="📤 Membro saiu",
                description=f"{member.mention} (`{member}`)\nID: `{member.id}`",
                color=COR_LOG_MEMBRO_OUT,
            )
        await self._log(member.guild, embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.abc.User):
        responsavel = await _achar_responsavel(guild, discord.AuditLogAction.ban, target_id=user.id)
        embed = discord.Embed(
            title="🔨 Membro banido",
            description=f"{user.mention} (`{user}`)\nID: `{user.id}`",
            color=COR_LOG_MEMBRO_OUT,
        )
        if responsavel:
            embed.add_field(name="Banido por", value=responsavel.mention, inline=False)
        await self._log(guild, embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.abc.User):
        responsavel = await _achar_responsavel(guild, discord.AuditLogAction.unban, target_id=user.id)
        embed = discord.Embed(
            title="🕊️ Membro desbanido",
            description=f"{user.mention} (`{user}`)\nID: `{user.id}`",
            color=COR_LOG_MEMBRO_IN,
        )
        if responsavel:
            embed.add_field(name="Desbanido por", value=responsavel.mention, inline=False)
        await self._log(guild, embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        guild = after.guild

        if before.nick != after.nick:
            responsavel = await _achar_responsavel(guild, discord.AuditLogAction.member_update, target_id=after.id)
            embed = discord.Embed(
                title="✏️ Apelido alterado",
                description=(
                    f"{after.mention}\n**Antes:** `{before.nick or before.name}`\n"
                    f"**Depois:** `{after.nick or after.name}`"
                ),
                color=COR_LOG_MEMBRO_IN,
            )
            if responsavel and responsavel.id != after.id:
                embed.add_field(name="Alterado por", value=responsavel.mention, inline=False)
            await self._log(guild, embed)

        cargos_antes = set(before.roles)
        cargos_depois = set(after.roles)
        ganhos = cargos_depois - cargos_antes
        perdidos = cargos_antes - cargos_depois
        if ganhos or perdidos:
            responsavel = await _achar_responsavel(guild, discord.AuditLogAction.member_role_update, target_id=after.id)
            partes = []
            if ganhos:
                partes.append("**Ganhou:** " + ", ".join(r.mention for r in ganhos))
            if perdidos:
                partes.append("**Perdeu:** " + ", ".join(r.mention for r in perdidos))
            embed = discord.Embed(
                title="🎭 Cargos do membro alterados",
                description=f"{after.mention}\n\n" + "\n".join(partes),
                color=COR_LOG_CARGO,
            )
            if responsavel:
                embed.add_field(name="Alterado por", value=responsavel.mention, inline=False)
            await self._log(guild, embed)

        antes_timeout = getattr(before, "timed_out_until", None) or getattr(before, "communication_disabled_until", None)
        depois_timeout = getattr(after, "timed_out_until", None) or getattr(after, "communication_disabled_until", None)
        if antes_timeout != depois_timeout:
            responsavel = await _achar_responsavel(guild, discord.AuditLogAction.member_update, target_id=after.id)
            if depois_timeout:
                desc = f"{after.mention} recebeu timeout até <t:{int(depois_timeout.timestamp())}:F>"
                titulo = "⏳ Timeout aplicado"
            else:
                desc = f"{after.mention} teve o timeout removido"
                titulo = "⏳ Timeout removido"
            embed = discord.Embed(title=titulo, description=desc, color=COR_LOG_MEMBRO_OUT)
            if responsavel:
                embed.add_field(name="Aplicado por", value=responsavel.mention, inline=False)
            await self._log(guild, embed)

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        mudancas = []
        if before.name != after.name:
            mudancas.append(f"**Nome do servidor:** `{before.name}` → `{after.name}`")
        if before.icon != after.icon:
            mudancas.append("**Ícone do servidor foi alterado**")
        if before.verification_level != after.verification_level:
            mudancas.append(f"**Nível de verificação:** `{before.verification_level}` → `{after.verification_level}`")
        if before.vanity_url_code != after.vanity_url_code:
            mudancas.append(f"**Link personalizado:** `{before.vanity_url_code}` → `{after.vanity_url_code}`")

        if not mudancas:
            return

        responsavel = await _achar_responsavel(after, discord.AuditLogAction.guild_update)
        embed = discord.Embed(
            title="⚙️ Configurações do servidor alteradas",
            description="\n".join(mudancas),
            color=COR_LOG_SERVIDOR,
        )
        if responsavel:
            embed.add_field(name="Alterado por", value=responsavel.mention, inline=False)
        await self._log(after, embed)


# ══════════════════════════════════════════════════════════════════
#  📥  MÓDULO DE REGISTRO — painéis de reação pra pegar cargo
# ══════════════════════════════════════════════════════════════════
#
# Como funciona:
#   1) quando o bot liga, ele confere REGISTRO_DATA_FILE pra ver quais
#      painéis (de PAINEIS_REGISTRO) já foram enviados no canal
#      CANAL_REGISTRO_ID;
#   2) antes de mandar os painéis que faltam, Pink garante que todo
#      cargo usado neles existe: se o ID em CARGOS_REGISTRO estiver em
#      0 e o cargo ainda não tiver sido criado por ela antes (ver
#      CARGOS_REGISTRO_FILE), ela cria o cargo sozinha (nome e cor
#      vêm de CARGOS_REGISTRO_AUTO) e guarda o ID gerado;
#   3) manda só os painéis que faltam, na ordem em que estão na lista,
#      e guarda o ID de cada mensagem enviada em REGISTRO_DATA_FILE;
#   4) a partir daí, reagir com o emoji de uma opção dá o cargo
#      correspondente; tirar a reação remove o cargo;
#   5) se você desligar e ligar o bot de novo, ele não manda os
#      painéis nem recria os cargos outra vez — só o que ainda não
#      tiver sido feito (por exemplo, se você adicionar um painel novo
#      na lista depois).
#
# Isso é feito olhando os arquivos de dados (REGISTRO_DATA_FILE), não o
# histórico do canal — então mesmo que alguém apague o painel do
# Discord sem querer, o bot não vai reenviar sozinho. Se você editar
# um painel já enviado (mudar as opções dele em PAINEIS_REGISTRO, por
# exemplo), o bot também NÃO manda uma mensagem nova — ele mantém a
# mesma mensagem e só atualiza o embed/as reações dela quando você
# rodar `pk!recriarcargosregistro`, exatamente pra evitar reenviar
# tudo de novo quando o bot é atualizado.
#
# TRAVA DE SEGURANÇA (patch): além de confiar em REGISTRO_DATA_FILE,
# antes de mandar QUALQUER painel a gente confere o histórico real do
# canal por um embed com o mesmo título. Isso cobre o caso de o arquivo
# de dados ter voltado vazio (host com disco efêmero, restart, arquivo
# corrompido) — em vez de reenviar duplicado, Pink recupera o
# message_id da mensagem que já existe e volta a rastreá-la.

class RegistroCog(commands.Cog, name="Registro"):
    """Painéis de reação (reaction role) enviados uma única vez por painel."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data = _carregar_registro()
        self.cargos_criados = _carregar_cargos_registro()  # cargo_key -> ID criado por Pink
        self._checado = False  # evita reprocessar em reconexões dentro do mesmo processo

    # ── Helpers ─────────────────────────────────────────

    def _painel_por_chave(self, chave: str) -> dict | None:
        return next((p for p in PAINEIS_REGISTRO if p["chave"] == chave), None)

    def _achar_painel_por_mensagem(self, message_id: int):
        for chave, info in self.data["enviados"].items():
            if info.get("message_id") == message_id:
                return chave, self._painel_por_chave(chave)
        return None, None

    def _resolver_cargo_id(self, cargo_key: str) -> int:
        """ID a usar pro cargo: manual (CARGOS_REGISTRO) tem prioridade;
        senão usa o ID que Pink já criou sozinha antes; senão é 0 (ainda
        não existe)."""
        manual = CARGOS_REGISTRO.get(cargo_key, 0)
        if manual:
            return manual
        return self.cargos_criados.get(cargo_key, 0)

    async def _garantir_cargos(self, guild: discord.Guild):
        """Cria automaticamente qualquer cargo de registro que ainda não
        exista (ID 0 em CARGOS_REGISTRO e nunca criado por Pink antes)."""
        for painel in PAINEIS_REGISTRO:
            for _emoji, _label, cargo_key in painel["opcoes"]:
                if self._resolver_cargo_id(cargo_key):
                    continue  # já tem ID manual, ou Pink já criou esse antes

                nome, cor = CARGOS_REGISTRO_AUTO.get(cargo_key, (cargo_key, COR_NEUTRA))

                # o mesmo cargo pode ser referenciado por mais de um painel
                # (ex.: "dispositivo_pc" aparece em Verificação e Dispositivo)
                # — sem essa checagem, o loop tentaria criar duas vezes.
                if cargo_key in self.cargos_criados:
                    continue

                try:
                    cargo = await guild.create_role(
                        name=nome,
                        colour=discord.Colour(cor),
                        reason="Pink: criação automática de cargo do módulo de Registro",
                    )
                except discord.Forbidden:
                    print(f"⚠️ Registro: sem permissão pra criar o cargo '{nome}' ({cargo_key})")
                    continue
                except discord.HTTPException as e:
                    print(f"⚠️ Registro: erro ao criar o cargo '{nome}' ({cargo_key}) — {e}")
                    continue

                self.cargos_criados[cargo_key] = cargo.id
                _salvar_cargos_registro(self.cargos_criados)
                await asyncio.sleep(0.3)  # respiro entre criações, evita rate limit

    def _montar_embed_painel(self, guild: discord.Guild, painel: dict) -> discord.Embed:
        linhas = []
        for emoji, label, cargo_key in painel["opcoes"]:
            cargo_id = self._resolver_cargo_id(cargo_key)
            cargo = guild.get_role(cargo_id) if cargo_id else None
            alvo = cargo.mention if cargo else f"`{label}` *(cargo não configurado)*"
            linhas.append(f"{emoji} {alvo}")

        embed = discord.Embed(
            title=painel["titulo"],
            description=f"{painel['descricao']}\n\n" + "\n".join(linhas),
            color=COR_NEUTRA,
        )
        embed.set_footer(text="👽 Reaja pra pegar o cargo • tire a reação pra perder")
        return embed

    async def _enviar_painel(self, canal: discord.abc.Messageable, painel: dict) -> discord.Message:
        embed = self._montar_embed_painel(canal.guild, painel)
        mensagem = await canal.send(embed=embed)
        for emoji, _label, _cargo_key in painel["opcoes"]:
            try:
                await mensagem.add_reaction(emoji)
            except (discord.Forbidden, discord.HTTPException):
                pass
        return mensagem

    async def _sincronizar_reacoes(self, mensagem: discord.Message, painel: dict):
        """Ajusta as reações de uma mensagem já enviada pra bater com as
        opções atuais do painel: tira reações de opções que não existem
        mais e adiciona as que faltam. Não reenvia a mensagem."""
        emojis_atuais = {emoji for emoji, _label, _cargo_key in painel["opcoes"]}

        # tenta usar a mensagem já com as reações carregadas; se não tiver
        # vindo populada (ex.: mensagem antiga buscada agora), busca de novo
        emojis_existentes = {str(r.emoji) for r in mensagem.reactions}

        for emoji_str in emojis_existentes - emojis_atuais:
            try:
                await mensagem.clear_reaction(emoji_str)
            except (discord.Forbidden, discord.HTTPException) as e:
                print(f"⚠️ Registro: não consegui remover a reação '{emoji_str}' — {e}")

        for emoji, _label, _cargo_key in painel["opcoes"]:
            if emoji not in emojis_existentes:
                try:
                    await mensagem.add_reaction(emoji)
                except (discord.Forbidden, discord.HTTPException) as e:
                    print(f"⚠️ Registro: não consegui adicionar a reação '{emoji}' — {e}")
                await asyncio.sleep(0.3)

    async def _achar_painel_no_historico(self, canal: discord.abc.Messageable, titulo_painel: str) -> discord.Message | None:
        """Trava de segurança: procura no histórico do canal por uma
        mensagem nossa com esse título de embed, mesmo que
        REGISTRO_DATA_FILE não saiba dela (ex.: arquivo voltou vazio
        depois de um restart num host com disco efêmero)."""
        try:
            async for msg in canal.history(limit=100):
                if msg.author.id == self.bot.user.id and msg.embeds and msg.embeds[0].title == titulo_painel:
                    return msg
        except discord.Forbidden:
            pass
        return None

    async def _enviar_paineis_pendentes(self, canal: discord.abc.Messageable) -> int:
        """Manda só os painéis que ainda não foram enviados nesse canal. Retorna quantos mandou."""
        await self._garantir_cargos(canal.guild)

        enviados_agora = 0
        for painel in PAINEIS_REGISTRO:
            if painel["chave"] in self.data["enviados"]:
                continue  # já foi enviado uma vez — não manda de novo

            # confere o canal antes de mandar, por segurança extra
            existente = await self._achar_painel_no_historico(canal, painel["titulo"])
            if existente is not None:
                self.data["enviados"][painel["chave"]] = {
                    "canal_id": canal.id,
                    "message_id": existente.id,
                }
                _salvar_registro(self.data)
                print(f"ℹ️ Registro: painel '{painel['chave']}' já existia no canal — recuperado do histórico, não reenviado.")
                continue

            mensagem = await self._enviar_painel(canal, painel)
            self.data["enviados"][painel["chave"]] = {
                "canal_id": canal.id,
                "message_id": mensagem.id,
            }
            _salvar_registro(self.data)
            enviados_agora += 1
            await asyncio.sleep(0.5)  # respiro entre painéis, evita rate limit
        return enviados_agora

    # ── Evento: manda os painéis que faltam quando o bot liga ─────

    @commands.Cog.listener()
    async def on_ready(self):
        if self._checado:
            return
        self._checado = True

        if not CANAL_REGISTRO_ID:
            return
        canal = self.bot.get_channel(CANAL_REGISTRO_ID)
        if canal is None:
            print(f"⚠️ Registro: não encontrei o canal {CANAL_REGISTRO_ID}")
            return

        try:
            await self._enviar_paineis_pendentes(canal)
        except discord.Forbidden:
            print(f"⚠️ Registro: sem permissão pra mandar mensagens/reações em {canal.id}")

    # ── Reações -> cargo ────────────────────────────────

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.member is None or payload.member.bot:
            return
        _chave, painel = self._achar_painel_por_mensagem(payload.message_id)
        if painel is None:
            return

        emoji_str = str(payload.emoji)
        opcao = next((o for o in painel["opcoes"] if o[0] == emoji_str), None)
        if opcao is None:
            return

        _emoji, _label, cargo_key = opcao
        cargo_id = self._resolver_cargo_id(cargo_key)
        if not cargo_id:
            return
        cargo = payload.member.guild.get_role(cargo_id)
        if cargo is None:
            print(f"⚠️ Registro: cargo '{cargo_key}' ({cargo_id}) não existe no servidor {payload.guild_id}")
            return

        try:
            await payload.member.add_roles(cargo, reason=f"Registro: reagiu em '{_label}'")
        except (discord.Forbidden, discord.HTTPException) as e:
            print(f"⚠️ Registro: não consegui dar o cargo '{cargo_key}' — {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        # em remoções o Discord não manda o objeto Member completo, só o user_id
        if payload.user_id == self.bot.user.id:
            return
        _chave, painel = self._achar_painel_por_mensagem(payload.message_id)
        if painel is None:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return
        membro = guild.get_member(payload.user_id)
        if membro is None:
            return

        emoji_str = str(payload.emoji)
        opcao = next((o for o in painel["opcoes"] if o[0] == emoji_str), None)
        if opcao is None:
            return

        _emoji, _label, cargo_key = opcao
        cargo_id = self._resolver_cargo_id(cargo_key)
        if not cargo_id:
            return
        cargo = guild.get_role(cargo_id)
        if cargo is None:
            return

        try:
            await membro.remove_roles(cargo, reason=f"Registro: tirou a reação de '{_label}'")
        except (discord.Forbidden, discord.HTTPException) as e:
            print(f"⚠️ Registro: não consegui remover o cargo '{cargo_key}' — {e}")

    # ── Comando manual (admin) — só manda o que ainda falta ───────

    @commands.command(name="painelregistro")
    @commands.has_permissions(administrator=True)
    async def painel_registro(self, ctx: commands.Context):
        """Manda manualmente os painéis de registro que ainda não foram enviados
        (e cria os cargos que faltarem). Uso: pk!painelregistro"""
        if not CANAL_REGISTRO_ID:
            await ctx.send(embed=embed_erro("CANAL_REGISTRO_ID não está configurado no código."))
            return
        canal = ctx.guild.get_channel(CANAL_REGISTRO_ID)
        if canal is None:
            await ctx.send(embed=embed_erro("não encontrei o canal de registro configurado."))
            return

        qtd = await self._enviar_paineis_pendentes(canal)
        if qtd == 0:
            await ctx.send(fala("todos os painéis de registro já foram enviados nesse canal antes. 💀"))
        else:
            await ctx.send(embed=embed_ok("✅ Painéis publicados!!", f"{qtd} painel(is) de registro enviado(s) em {canal.mention}."))

    @commands.command(name="recriarcargosregistro", aliases=["fixcargos"])
    @commands.has_permissions(administrator=True)
    async def recriar_cargos(self, ctx: commands.Context):
        """Cria (ou verifica) os cargos de registro, atualiza os embeds dos
        painéis já enviados e sincroniza as reações deles com as opções
        atuais (remove reação de opção removida, adiciona a que faltar).
        NÃO manda painel novo nem reenvia mensagem — só ajusta o que já
        está lá. Use se algum painel ainda mostrar 'cargo não configurado'
        ou se você mudou as opções de um painel no código.
        Uso: pk!recriarcargosregistro"""
        await self._garantir_cargos(ctx.guild)

        atualizados = 0
        for chave, info in list(self.data["enviados"].items()):
            painel = self._painel_por_chave(chave)
            if painel is None:
                continue
            canal = ctx.guild.get_channel(info.get("canal_id"))
            if canal is None:
                continue
            try:
                mensagem = await canal.fetch_message(info["message_id"])
                await mensagem.edit(embed=self._montar_embed_painel(ctx.guild, painel))
                await self._sincronizar_reacoes(mensagem, painel)
                atualizados += 1
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                continue

        await ctx.send(embed=embed_ok(
            "✅ Cargos verificados!!",
            f"cargos criados/confirmados e {atualizados} painel(is) atualizado(s) (embed + reações) com as opções certas."
        ))


# ══════════════════════════════════════════════════════════════════
#  📋  COMANDOS GERAIS (fora do cog)
# ══════════════════════════════════════════════════════════════════

@bot.command(name="help", aliases=["ajuda", "h"])
async def pink_help(ctx: commands.Context):
    embed = discord.Embed(
        title="💀 Pink Bot — Ajuda",
        description="oi. eu sou Pink, a caveirinha da DOMINUS. aqui tá tudo que eu sei fazer 🦴",
        color=COR_NEUTRA, timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(
        name="💬 Diálogo",
        inline=False,
        value=(
            "converse comigo, me mencione ou diga \"pink\" que eu respondo!!\n"
            "às vezes eu apareço sozinho, do nada 👀"
        )
    )
    embed.add_field(
        name="🪦 Respeitos",
        inline=False,
        value=(
            "`pk!f` — pague seus respeitos a Pink\n"
            "`pk!memorial` — vê o placar de quem mais prestou respeitos"
        )
    )
    embed.add_field(
        name="💀 Invocações",
        inline=False,
        value=(
            "`pk!invocar` — força Pink a se manifestar\n"
            "`pk!oraculo` — pede uma profecia curta e enigmática\n"
            "`pk!sobre` — lore e apresentação de Pink"
        )
    )
    embed.add_field(
        name="🛡️ Grupos",
        inline=False,
        value=(
            "clique no botão do painel de grupos pra criar seu cargo + chat + call\n"
            "`pk!painelgrupo` — publica o painel (admin)\n"
            "fale **\"pink liberar painel\"** no chat — mesma coisa, só que dita por Pink (admin)\n"
            "`pk!addmembro @pessoa` — adiciona alguém no seu grupo\n"
            "`pk!removermembro @pessoa` — remove alguém do seu grupo\n"
            "`pk!encerrargrupo` — apaga seu grupo (cargo + canais)"
        )
    )
    embed.add_field(
        name="📋 Fichas",
        inline=False,
        value=(
            "`pk!novomembro` — ficha de novos membros\n"
            "`pk!staff` — candidatura a Staff\n"
            "`pk!parceria <mapa|comercial|dj|cla|comunidade>` — fichas de parceria\n"
            "`pk!fichas` — lista todas as fichas disponíveis\n"
            "*(formulário interativo: preenche, confere e confirma antes de enviar!!)*"
        )
    )
    embed.add_field(
        name="📥 Registro",
        inline=False,
        value=(
            "painéis de reação (verificação, gênero, sexualidade, aniversário, "
            "gravações, dispositivo) publicados automaticamente e só uma vez!!\n"
            "os cargos são criados automaticamente por Pink na primeira vez.\n"
            "reaja pra pegar o cargo, tire a reação pra perder.\n"
            "`pk!painelregistro` — manda manualmente os painéis que faltam (admin)\n"
            "`pk!recriarcargosregistro` — cria/verifica os cargos e sincroniza embed + reações dos painéis já enviados (admin)"
        )
    )
    embed.add_field(
        name="🕵️ Auditoria",
        inline=False,
        value=(
            "log automático e total do servidor, postado no canal de auditoria!!\n"
            "canais, cargos, mensagens apagadas/editadas, entradas/saídas/kicks/bans, "
            "call e mudanças no servidor — tudo, exceto reordenação de cargos.\n"
            "*(não precisa de comando, é automático!!)*"
        )
    )
    embed.add_field(
        name="📚 Aprendizado (moderação)",
        inline=False,
        value=(
            "`pk!ensinar <gatilho> <resposta>` — ensina uma resposta nova\n"
            "`pk!esquecer <gatilho>` — remove um gatilho\n"
            "`pk!gatilhos` — lista tudo que Pink sabe\n"
            "`pk!resposta <gatilho>` — vê as respostas de um gatilho\n"
            "`pk!simular <texto>` — testa o que Pink responderia"
        )
    )
    embed.set_footer(text="💀 Pink Bot • prefixo: pk! ou pink ")
    await ctx.send(embed=embed)


@bot.command(name="ping")
async def ping(ctx: commands.Context):
    latencia = round(bot.latency * 1000)
    cor = COR_VERDE if latencia < 100 else (COR_DOURADO if latencia < 200 else COR_VERMELHO)
    await ctx.send(embed=discord.Embed(
        title="🏓 Pong!!", description=f"latência: `{latencia}ms` 💀", color=cor
    ))


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(fala("você não tem permissão pra pedir isso de mim 🚫"))
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(embed=embed_erro(f"faltou informação!! uso correto: `{ctx.prefix}{ctx.command} {ctx.command.signature}`"))
        return
    raise error


# ══════════════════════════════════════════════════════════════════
#  🔁  ROTAÇÃO DE PRESENÇA
# ══════════════════════════════════════════════════════════════════

async def _rotacionar_presenca():
    await bot.wait_until_ready()
    while not bot.is_closed():
        texto = random.choice(_STATUS_PRESENCA)
        try:
            await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=texto))
        except Exception:
            pass
        await asyncio.sleep(900)  # troca a cada 15 minutos


# ══════════════════════════════════════════════════════════════════
#  💀  EVENTOS GLOBAIS
# ══════════════════════════════════════════════════════════════════

_presenca_task_iniciada = False


@bot.event
async def on_ready():
    global _presenca_task_iniciada
    print(f"\n{'═'*54}")
    print("  💀  PINK BOT — ONLINE")
    print(f"  Logado como: {bot.user} ({bot.user.id})")
    print(f"  Servidores: {len(bot.guilds)}")
    print("  A caveirinha da DOMINUS está de guarda 🦴")
    print(f"{'═'*54}\n")

    if not _presenca_task_iniciada:
        bot.loop.create_task(_rotacionar_presenca())
        _presenca_task_iniciada = True


# ══════════════════════════════════════════════════════════════════
#  🚀  INICIALIZAÇÃO
# ══════════════════════════════════════════════════════════════════

async def _main():
    async with bot:
        await bot.add_cog(PinkCog(bot))
        await bot.add_cog(GruposCog(bot))
        await bot.add_cog(CargoVinculadoCog(bot))
        await bot.add_cog(FichasCog(bot))
        await bot.add_cog(AuditoriaCog(bot))
        await bot.add_cog(RegistroCog(bot))
        if not TOKEN:
            print("❌ ERRO: token não encontrado! Crie um .env com PINK_TOKEN=seu_token")
            return
        await bot.start(TOKEN)


if __name__ == "__main__":
    import asyncio as _asyncio
    _asyncio.run(_main())
