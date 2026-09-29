# Duas contribuições prontas para o repositório vinilana/jev-gateway

Rascunhos de issue, em inglês porque o repositório é em inglês. Não foram enviados: enviar é ação
externa e depende do Igor. Fatos medidos em 2026-09-22 nesta máquina (Windows 11, Node 24.17, jev-gateway 0.4.1).

## 1. Windows: `jev-claude`/`jev-codex` fail with `spawn claude ENOENT`

**Title:** Launchers cannot start the client on Windows (`spawn claude ENOENT`)

**Body:**

On Windows, `claude` and `codex` installed through npm are `.cmd` shims. `runLauncher` does
`spawn(spec.client, args, { stdio: "inherit" })` without a shell, and Node's `CreateProcess` path
lookup only resolves `.exe`, so both launchers print `jev-claude: could not run claude: spawn
claude ENOENT` right after starting the router.

Workaround that works here: put the directory holding the native binary on `PATH` before delegating
(`@anthropic-ai/claude-code/bin/claude.exe`, and for Codex
`@openai/codex/node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe`).

Suggested fix in `bin/launcher.mjs`: on `win32`, resolve the client through `where.exe` (or search
`PATH` for `<client>.exe`, then `<client>.cmd`) and, when the match is a `.cmd`/`.bat`, spawn it
through `cmd.exe /d /s /c` with `windowsVerbatimArguments: true` and each argument quoted, the way
`cross-spawn` does — spawning a `.cmd` directly without a shell throws `EINVAL` since the
CVE-2024-27980 hardening. Happy to open a PR if you prefer that route.

## 2. Same request retried by the client is re-scored by Jev every time

**Title:** Cache Jev decisions by request hash: a 529 retry storm paid seven Jev calls

**Body:**

During one Claude Code turn the Anthropic API answered 529 seven times in a row; Claude Code retried
the byte-identical request each time and the gateway asked Jev again on every retry (12,920 input
tokens per call, same answer ±0.03 confidence). Log excerpt (`~/.jev-gateway/claude.log`):

```
06:24:12 passthrough low_confidence Read 0.85 status 529 jev 12920 tok
06:24:14 passthrough low_confidence Read 0.83 status 529 jev 12920 tok
06:24:17 passthrough low_confidence Read 0.86 status 529 jev 12920 tok
... (7 retries)
```

Suggestion: key the decision on a hash of `(model, messages, tools)` and reuse it for a short window
(a minute is enough for retries), or at least while the previous upstream reply for that hash was a
5xx. It also removes the extra 1–2 s of Jev latency from every retry. The dashboard could show
"decisions reused" next to "Jev calls".

## 3. (nota, não issue) O que observamos e pode interessar ao autor

- Com 103–134 ferramentas (Claude Code com MCPs), a confiança da escolha fica em 0,80–0,87 mesmo
  quando a ferramenta é óbvia (`Read`). Com o corte padrão 0,7 roteia; com 0,9 não roteia nada.
  Vale documentar que o corte depende do tamanho da lista.
- `jev-codex exec -c 'x=y' "..."` responde, mas não passa pelo gateway: o `-c` do usuário anula os
  `-c model_provider=...` injetados. O README podia avisar.
