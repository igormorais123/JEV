"""Mascara segredo antes de o pedido sair desta máquina.

O roteador manda o texto do pedido para um provedor externo. Pedido de trabalho carrega chave
colada, token de CI, URL assinada e senha — e a regra da casa é que segredo não é exibido, não
é registrado e não sai daqui. Um classificador de esforço não precisa de nenhum deles: trocar
por um rótulo não muda a classificação e elimina o vazamento.

A redação é por forma, não por lista de chaves conhecidas: qualquer coisa com cara de
credencial vira `[segredo]`, mesmo que seja falso positivo.
"""
import re

PADROES = [
    # Prefixos de provedores conhecidos.
    re.compile(r'\b(?:sk|pk|rk)-[A-Za-z0-9_\-]{16,}'),
    re.compile(r'\bsk_[A-Za-z0-9]{16,}'),
    re.compile(r'\b(?:ghp|gho|ghu|ghs|ghr|github_pat)_[A-Za-z0-9_]{16,}'),
    re.compile(r'\bAIza[A-Za-z0-9_\-]{20,}'),
    re.compile(r'\bxox[baprs]-[A-Za-z0-9\-]{10,}'),
    re.compile(r'\bpplx-[A-Za-z0-9]{16,}'),
    re.compile(r'\bapify_api_[A-Za-z0-9]{16,}'),
    re.compile(r'\bBSA[_A-Za-z0-9]{16,}'),
    # JSON Web Token.
    re.compile(r'\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}'),
    # Atribuição explícita de segredo em texto ou em .env.
    re.compile(r'(?i)\b([A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|SENHA|PASSWD)[A-Z0-9_]*)\s*[:=]\s*'
               r'["\']?[^\s"\',;]{8,}'),
    re.compile(r'(?i)\b(?:authorization|bearer)\s*:?\s+[A-Za-z0-9_\-\.]{20,}'),
    # Credencial embutida em URL.
    re.compile(r'\b[a-z][a-z0-9+.\-]*://[^\s/@]+:[^\s/@]+@'),
    # Credencial que se anuncia no próprio valor, como `zep-...-secret-2026-...`. Exige
    # separador e tamanho para não engolir a palavra "secret" escrita no meio de uma frase.
    re.compile(r'(?i)\b(?=[A-Za-z0-9_\-]*[_\-])[A-Za-z0-9_\-]*'
               r'(?:secret|token|apikey|api_key|passwd|senha)[A-Za-z0-9_\-]*\b(?<=[A-Za-z0-9_\-]{16})'),
]

# Corrida de caracteres de base64/hex que não é palavra de língua nenhuma.
GRANDE = re.compile(r'\b(?=[A-Za-z0-9_\-]*[0-9])(?=[A-Za-z0-9_\-]*[A-Za-z])[A-Za-z0-9_\-]{32,}\b')

ROTULO = '[segredo]'


def limpar(texto):
    """Devolve (texto mascarado, quantas ocorrências foram mascaradas)."""
    if not texto:
        return texto, 0
    total = 0
    for padrao in PADROES:
        texto, n = padrao.subn(
            lambda m: (m.group(1) + '=' + ROTULO) if m.groups() and m.group(1) else ROTULO, texto)
        total += n
    texto, n = GRANDE.subn(ROTULO, texto)
    return texto, total + n
