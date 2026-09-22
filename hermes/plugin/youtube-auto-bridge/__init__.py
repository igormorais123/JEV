"""Ponte do YouTube com o Jev (2026-09-21): a transcrição entra sem enchimento e com a frente.

O que Igor mais manda ao Hermes é um link de vídeo, sem pedido além do link; a ponte injetava
até 45 mil caracteres por vídeo. Agora `jev_hermes.recortes.transcricao` classifica cada parte
(substância ou enchimento) e diz a qual frente de Igor o vídeo serve. Falha para o lado de
mandar a transcrição inteira, como antes. Cópia versionada em `hermes/plugin/` do repo JEV.
"""
from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import sys
from typing import Any

logger = logging.getLogger(__name__)

JEV_RAIZ = os.getenv("JEV_HERMES_RAIZ", "/root/.hermes/integrations/jev")
if JEV_RAIZ not in sys.path:
    sys.path.insert(0, JEV_RAIZ)


def _pelo_jev(transcript: str, rotulo: str) -> tuple[str, str]:
    """(transcrição possivelmente recortada, nota). Qualquer falha devolve a original sem nota."""
    try:
        if os.getenv("JEV_YOUTUBE", "1") == "0":
            return transcript, ""
        from jev_hermes import camadas, recortes
        novo, nota, decisao = recortes.transcricao(transcript, rotulo)
        camadas.registrar("transcricao", **decisao)
        return (novo or transcript), nota
    except Exception as exc:  # noqa: BLE001
        logger.debug("youtube-auto-bridge jev: %s", exc)
        return transcript, ""

YOUTUBE_URL_RE = re.compile(
    r"https?://(?:www\.)?(?:youtube\.com/(?:watch\?[^ \n\r\t]+|shorts/[A-Za-z0-9_-]{11}[^ \n\r\t]*)|youtu\.be/[A-Za-z0-9_-]{11}[^ \n\r\t]*)",
    re.IGNORECASE,
)

HELPER = os.getenv("HERMES_YOUTUBE_HELPER", "/root/.hermes/bin/hermes-youtube-transcript")
BRIDGE = os.getenv("HERMES_YOUTUBE_PC_BRIDGE", "/root/.hermes/bridge/youtube-transcript-pc")
DEFAULT_LANGUAGE = os.getenv("HERMES_YOUTUBE_LANGUAGE", "pt,pt-BR,pt-PT,en,es")
TIMEOUT_SECONDS = int(os.getenv("HERMES_YOUTUBE_BRIDGE_TIMEOUT", "240"))
MAX_CHARS_PER_VIDEO = int(os.getenv("HERMES_YOUTUBE_MAX_CHARS_PER_VIDEO", "45000"))


def _clean_url(url: str) -> str:
    return url.rstrip(").,;]}>\"'")


def _fetch_transcript(url: str) -> dict[str, Any]:
    # A ordem pertence ao wrapper governado. Para Igor, a conta Apify
    # cadastrada e autorizada vem primeiro; as demais rotas continuam como
    # fallbacks e a falha só é devolvida após esgotá-las.
    command = [HELPER, url, "--languages", DEFAULT_LANGUAGE]
    if not os.path.exists(HELPER):
        command = [BRIDGE, url, DEFAULT_LANGUAGE.split(",")[0]]
    proc = subprocess.run(
        command,
        text=True,
        capture_output=True,
        timeout=TIMEOUT_SECONDS,
        check=False,
    )
    raw = (proc.stdout or "").strip()
    if proc.returncode != 0:
        err = (proc.stderr or raw or "unknown error").strip()
        return {"ok": False, "url": url, "error": err[:2000]}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Helper antigo/ponte podem devolver texto puro; aceite como transcrição.
        return {"ok": True, "url": url, "source": "text-output", "full_text": raw}
    if data.get("error"):
        return {"ok": False, "url": url, "error": str(data.get("error"))[:2000]}
    data["ok"] = bool(data.get("ok", True))
    data["url"] = url
    if data.get("text") and not data.get("full_text"):
        data["full_text"] = data.get("text")
    return data


def _render_transcript_block(item: dict[str, Any], index: int) -> str:
    url = item.get("url", "")
    if not item.get("ok"):
        return (
            f"## Video {index}\n"
            f"URL: {url}\n"
            f"Transcricao: falhou automaticamente.\n"
            f"Erro tecnico resumido: {item.get('error', 'erro desconhecido')}\n"
        )

    full_text = str(item.get("full_text") or item.get("text") or "").strip()
    timestamped = str(item.get("timestamped_text") or "").strip()
    transcript = timestamped or full_text
    if len(transcript) > MAX_CHARS_PER_VIDEO:
        transcript = transcript[:MAX_CHARS_PER_VIDEO] + "\n[transcricao truncada pelo pre-processador; use o link/ponte se precisar do restante]"
    transcript, nota = _pelo_jev(transcript, str(item.get("video_id") or url))
    nota = (nota + "\n\n") if nota else ""

    return (
        f"## Video {index}\n"
        f"URL: {url}\n"
        f"Video ID: {item.get('video_id', '')}\n"
        f"Fonte: {item.get('source', 'wrapper-governado')}\n"
        f"Idioma pedido: {DEFAULT_LANGUAGE}\n"
        f"Duracao: {item.get('duration', '')}\n"
        f"Segmentos: {item.get('segment_count', '')}\n\n"
        f"{nota}Transcricao:\n{transcript}\n"
    )


def _pre_gateway_dispatch(event: Any = None, **_: Any) -> dict[str, Any] | None:
    text = getattr(event, "text", "") or ""
    urls = []
    seen = set()
    for match in YOUTUBE_URL_RE.findall(text):
        url = _clean_url(match)
        if url not in seen:
            seen.add(url)
            urls.append(url)
    if not urls:
        return None

    logger.info("youtube-auto-bridge: preprocessing %d YouTube URL(s)", len(urls))
    results = []
    for url in urls[:4]:
        try:
            results.append(_fetch_transcript(url))
        except subprocess.TimeoutExpired:
            results.append({"ok": False, "url": url, "error": "timeout waiting for PC bridge"})
        except Exception as exc:
            logger.exception("youtube-auto-bridge failed for %s", url)
            results.append({"ok": False, "url": url, "error": str(exc)[:2000]})

    blocks = "\n\n".join(_render_transcript_block(item, i + 1) for i, item in enumerate(results))
    rewritten = (
        "Mensagem original do usuario:\n"
        f"{text}\n\n"
        "[Contexto automatico do Hermes]\n"
        "Foram detectados links do YouTube. O Hermes ja tentou obter/transcrever o conteudo pela cadeia governada, com a conta Apify autorizada primeiro e fallbacks por legendas oficiais, yt-dlp e egress residencial quando disponivel. "
        "Nao peça transcricao ao usuario, nao substitua conteudo ausente por inferencia e nao encerre a busca enquanto houver rota autorizada ainda nao tentada. Use o material abaixo para resumir, extrair licoes e traduzir aplicacoes para Hermes, Colmeia e INTEIA. "
        "Se algum video falhou, explique a falha objetiva e use os videos que tiverem transcricao.\n\n"
        f"{blocks}"
    )
    return {"action": "rewrite", "text": rewritten}


def register(ctx) -> None:
    ctx.register_hook("pre_gateway_dispatch", _pre_gateway_dispatch)
