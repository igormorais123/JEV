"""Comparador determinístico da tarefa de triagem.

Congelado junto com planning/preregistro-E1-triagem.md, antes de qualquer chamada ao Jev.
É de propósito simples: se uma regra assim resolve a tarefa, o modelo não precisa ser comprado.
"""
import re
import unicodedata

CLASSES = ['cancelar', 'rastrear', 'trocar', 'cobranca', 'informacao']

# Ordem de prioridade declarada: a primeira classe com gatilho vence.
PRIORIDADE = ['cancelar', 'cobranca', 'trocar', 'rastrear']

GATILHOS = {
    'cancelar': [r'cancel', r'encerrar (a )?(assinatura|contrato|servico)', r'desistir'],
    'cobranca': [r'segunda via', r'boleto', r'estorno', r'reembols', r'dinheiro de volta',
                 r'parcel', r'cobrad[oa]', r'cobranca', r'comprovante de pagamento', r'nota fiscal',
                 r'pagamento'],
    'trocar': [r'troca', r'trocar', r'devolv', r'substitu', r'consert', r'reparo', r'garantia'],
    'rastrear': [r'rastre', r'onde esta', r'codigo de rastreio', r'entrega', r'entregador',
                 r'prazo', r'chegou', r'saiu para entrega', r'encomenda', r'pacote'],
}

PERGUNTA = re.compile(r'\?|^(qual|quais|quando|quanto|como|onde|vocês|voces)\b', re.I)


def normalizar(texto):
    sem_acento = ''.join(c for c in unicodedata.normalize('NFD', texto)
                         if unicodedata.category(c) != 'Mn')
    return sem_acento.lower()


def classificar(texto):
    alvo = normalizar(texto)
    for classe in PRIORIDADE:
        for padrao in GATILHOS[classe]:
            if re.search(padrao, alvo):
                return classe
    return 'informacao'
