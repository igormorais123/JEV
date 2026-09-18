# Fontes e revisões — triagem JEV

Coleta: 18/09/2026. As 18 cópias foram obtidas por Git, sem instalar dependências ou executar código dos projetos. O manifesto registra o commit completo. Links abaixo fixam essa revisão; páginas oficiais externas podem mudar.

[Documento de análise](../docs/TRIAGEM-JEV-HELENA.md) · [Manifesto](sources-manifest.json)

## Documentação externa consultada

- [Modelos e limites TypeSafe](https://docs.typesafe.ai/models)
- [Contrato da API TypeSafe](https://docs.typesafe.ai/api)
- [Perguntas paralelas](https://docs.typesafe.ai/cookbooks/parallel_questions)
- [Jev 1.13 no OpenRouter](https://openrouter.ai/typesafe/jev-1.13/)
- [Alias atual no OpenRouter](https://openrouter.ai/~typesafe/jev-latest/)

A rota OpenRouter Decisions foi identificada no código do Jev CLI, não validada por requisição autenticada. A tentativa de abrir uma página específica de referência Decisions não retornou conteúdo utilizável. Nenhuma cobrança foi testada.

## Catálogo por revisão

### Nasrallah-AL/jev-cli

- Repositório: [Nasrallah-AL/jev-cli](https://github.com/Nasrallah-AL/jev-cli)
- Revisão: `02ca80177aaef0b30a897959207f99df1e0c8446`
- Data do commit: `2026-09-18T17:27:48+03:00`
- Cópia local: `research/sources/jev-cli/`
- Estrutura na raiz: `.claude-plugin`, `.editorconfig`, `.env.example`, `.github`, `.gitignore`, `.npmignore`, `.nvmrc`, `CHANGELOG.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `LICENSE`, `NOTICE`, `README.md`, `SECURITY.md`, `biome.json`, `docs`, `package-lock.json`, `package.json`, `plugin`, `scripts`, `src`, `test`, `tsconfig.build.json`, `tsconfig.json`, `vitest.config.ts`.
- Arquivos/pastas de entrada:
  - [README.md](https://github.com/Nasrallah-AL/jev-cli/blob/02ca80177aaef0b30a897959207f99df1e0c8446/README.md)
  - [docs/config.md](https://github.com/Nasrallah-AL/jev-cli/blob/02ca80177aaef0b30a897959207f99df1e0c8446/docs/config.md)
  - [docs/verify.md](https://github.com/Nasrallah-AL/jev-cli/blob/02ca80177aaef0b30a897959207f99df1e0c8446/docs/verify.md)
  - [docs/classify.md](https://github.com/Nasrallah-AL/jev-cli/blob/02ca80177aaef0b30a897959207f99df1e0c8446/docs/classify.md)
  - [docs/route.md](https://github.com/Nasrallah-AL/jev-cli/blob/02ca80177aaef0b30a897959207f99df1e0c8446/docs/route.md)
  - [docs/batch.md](https://github.com/Nasrallah-AL/jev-cli/blob/02ca80177aaef0b30a897959207f99df1e0c8446/docs/batch.md)
  - [src/provider.ts](https://github.com/Nasrallah-AL/jev-cli/blob/02ca80177aaef0b30a897959207f99df1e0c8446/src/provider.ts)
  - [test](https://github.com/Nasrallah-AL/jev-cli/tree/02ca80177aaef0b30a897959207f99df1e0c8446/test)

### superagents-lab/jev-search

- Repositório: [superagents-lab/jev-search](https://github.com/superagents-lab/jev-search)
- Revisão: `f7e2d4b9f342b882726e49dd668fdc8336571eef`
- Data do commit: `2026-09-19T00:41:40+08:00`
- Cópia local: `research/sources/jev-search/`
- Estrutura na raiz: `.dev.vars.example`, `.env.example`, `.github`, `.gitignore`, `CONTRIBUTING.md`, `LICENSE`, `README.md`, `SECURITY.md`, `components.json`, `design-context.md`, `package.json`, `pnpm-lock.yaml`, `public`, `src`, `test`, `tsconfig.json`, `tsr.config.json`, `vite.config.ts`, `vitest.config.ts`, `worker-configuration.d.ts`, `wrangler.jsonc`.
- Arquivos/pastas de entrada:
  - [README.md](https://github.com/superagents-lab/jev-search/blob/f7e2d4b9f342b882726e49dd668fdc8336571eef/README.md)
  - [src/lib/typesafe.ts](https://github.com/superagents-lab/jev-search/blob/f7e2d4b9f342b882726e49dd668fdc8336571eef/src/lib/typesafe.ts)
  - [src/lib/pipeline.ts](https://github.com/superagents-lab/jev-search/blob/f7e2d4b9f342b882726e49dd668fdc8336571eef/src/lib/pipeline.ts)
  - [src/lib/rank.ts](https://github.com/superagents-lab/jev-search/blob/f7e2d4b9f342b882726e49dd668fdc8336571eef/src/lib/rank.ts)
  - [src/lib/merge.ts](https://github.com/superagents-lab/jev-search/blob/f7e2d4b9f342b882726e49dd668fdc8336571eef/src/lib/merge.ts)
  - [test](https://github.com/superagents-lab/jev-search/tree/f7e2d4b9f342b882726e49dd668fdc8336571eef/test)

### FirasSX914/Janus

- Repositório: [FirasSX914/Janus](https://github.com/FirasSX914/Janus)
- Revisão: `9cb66c488cf884e5997356a0de45f75aa3148774`
- Data do commit: `2026-09-18T15:54:36+02:00`
- Cópia local: `research/sources/Janus/`
- Estrutura na raiz: `.claude-plugin`, `.gitattributes`, `.github`, `.gitignore`, `CLAUDE.md`, `LICENSE`, `README.md`, `RESEARCH.md`, `data`, `docs`, `experiments`, `pyproject.toml`, `results`, `skills`, `src`, `tests`.
- Arquivos/pastas de entrada:
  - [README.md](https://github.com/FirasSX914/Janus/blob/9cb66c488cf884e5997356a0de45f75aa3148774/README.md)
  - [RESEARCH.md](https://github.com/FirasSX914/Janus/blob/9cb66c488cf884e5997356a0de45f75aa3148774/RESEARCH.md)
  - [results](https://github.com/FirasSX914/Janus/tree/9cb66c488cf884e5997356a0de45f75aa3148774/results)
  - [src/janus/measure.py](https://github.com/FirasSX914/Janus/blob/9cb66c488cf884e5997356a0de45f75aa3148774/src/janus/measure.py)
  - [src/janus/sweep.py](https://github.com/FirasSX914/Janus/blob/9cb66c488cf884e5997356a0de45f75aa3148774/src/janus/sweep.py)
  - [src/janus/providers/typesafe.py](https://github.com/FirasSX914/Janus/blob/9cb66c488cf884e5997356a0de45f75aa3148774/src/janus/providers/typesafe.py)

### DevMortimer/pi-warden

- Repositório: [DevMortimer/pi-warden](https://github.com/DevMortimer/pi-warden)
- Revisão: `84a3bc9aa6c2807b608df42bc77a951d9531d70b`
- Data do commit: `2026-09-18T23:44:23+08:00`
- Cópia local: `research/sources/pi-warden/`
- Estrutura na raiz: `.github`, `.gitignore`, `CHANGELOG.md`, `CONTRIBUTING.md`, `LICENSE`, `README.md`, `docs`, `eval`, `examples`, `extensions`, `package-lock.json`, `package.json`, `scripts`, `src`, `tests`, `tsconfig.build.json`, `tsconfig.json`.
- Arquivos/pastas de entrada:
  - [README.md](https://github.com/DevMortimer/pi-warden/blob/84a3bc9aa6c2807b608df42bc77a951d9531d70b/README.md)
  - [docs/guards.md](https://github.com/DevMortimer/pi-warden/blob/84a3bc9aa6c2807b608df42bc77a951d9531d70b/docs/guards.md)
  - [src/guard.ts](https://github.com/DevMortimer/pi-warden/blob/84a3bc9aa6c2807b608df42bc77a951d9531d70b/src/guard.ts)
  - [src/done.ts](https://github.com/DevMortimer/pi-warden/blob/84a3bc9aa6c2807b608df42bc77a951d9531d70b/src/done.ts)
  - [src/stuck.ts](https://github.com/DevMortimer/pi-warden/blob/84a3bc9aa6c2807b608df42bc77a951d9531d70b/src/stuck.ts)
  - [eval/reports](https://github.com/DevMortimer/pi-warden/tree/84a3bc9aa6c2807b608df42bc77a951d9531d70b/eval/reports)

### browser-use/jev-ultrafast

- Repositório: [browser-use/jev-ultrafast](https://github.com/browser-use/jev-ultrafast)
- Revisão: `1231850a0bf1a0c0341fe408ef1668dbbfdfac46`
- Data do commit: `2026-09-18T09:28:35-07:00`
- Cópia local: `research/sources/jev-ultrafast/`
- Estrutura na raiz: `.env.example`, `.gitignore`, `AGENTS.md`, `LICENSE`, `README.md`, `docs`, `examples`, `jev_ultrafast`, `pyproject.toml`, `scripts`, `tests`, `uv.lock`.
- Arquivos/pastas de entrada:
  - [README.md](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/README.md)
  - [docs/performance.md](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/docs/performance.md)
  - [jev_ultrafast/agent.py](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/jev_ultrafast/agent.py)
  - [jev_ultrafast/model.py](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/jev_ultrafast/model.py)
  - [jev_ultrafast/snapshot.js](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/jev_ultrafast/snapshot.js)
  - [examples](https://github.com/browser-use/jev-ultrafast/tree/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/examples)

### abhixhek/jevcal

- Repositório: [abhixhek/jevcal](https://github.com/abhixhek/jevcal)
- Revisão: `ae8f3144d69c9cb0e5e0a2c17f70b9d14714cb9f`
- Data do commit: `2026-09-18T12:58:35+05:30`
- Cópia local: `research/sources/jevcal/`
- Estrutura na raiz: `.github`, `.gitignore`, `LICENSE`, `README.md`, `docs`, `examples`, `pyproject.toml`, `scripts`, `src`, `tests`.
- Arquivos/pastas de entrada:
  - [README.md](https://github.com/abhixhek/jevcal/blob/ae8f3144d69c9cb0e5e0a2c17f70b9d14714cb9f/README.md)
  - [src/jevcal/compile.py](https://github.com/abhixhek/jevcal/blob/ae8f3144d69c9cb0e5e0a2c17f70b9d14714cb9f/src/jevcal/compile.py)
  - [src/jevcal/metrics.py](https://github.com/abhixhek/jevcal/blob/ae8f3144d69c9cb0e5e0a2c17f70b9d14714cb9f/src/jevcal/metrics.py)
  - [src/jevcal/providers/typesafe.py](https://github.com/abhixhek/jevcal/blob/ae8f3144d69c9cb0e5e0a2c17f70b9d14714cb9f/src/jevcal/providers/typesafe.py)
  - [src/jevcal/providers/llm.py](https://github.com/abhixhek/jevcal/blob/ae8f3144d69c9cb0e5e0a2c17f70b9d14714cb9f/src/jevcal/providers/llm.py)
  - [examples](https://github.com/abhixhek/jevcal/tree/ae8f3144d69c9cb0e5e0a2c17f70b9d14714cb9f/examples)

### anessbelbati/jev-rerank-bench

- Repositório: [anessbelbati/jev-rerank-bench](https://github.com/anessbelbati/jev-rerank-bench)
- Revisão: `cd9a35b22aeb4187334f7018a0ee1960a7470586`
- Data do commit: `2026-09-17T02:01:15+01:00`
- Cópia local: `research/sources/jev-rerank-bench/`
- Estrutura na raiz: `.env.example`, `.gitignore`, `LICENSE`, `README.md`, `batching.py`, `blog.py`, `cache`, `candidates`, `coldstart.py`, `common.py`, `data`, `determinism.py`, `docs`, `eval.py`, `network.py`, `nevir_eval.py`, `pyproject.toml`, `rerankers`, `results`, `rlcd_check.py`, `rlcd_runner.py`, `run.py`, `scripts`, `significance.py`, `uv.lock`.
- Arquivos/pastas de entrada:
  - [README.md](https://github.com/anessbelbati/jev-rerank-bench/blob/cd9a35b22aeb4187334f7018a0ee1960a7470586/README.md)
  - [results/summary.md](https://github.com/anessbelbati/jev-rerank-bench/blob/cd9a35b22aeb4187334f7018a0ee1960a7470586/results/summary.md)
  - [rerankers/jev.py](https://github.com/anessbelbati/jev-rerank-bench/blob/cd9a35b22aeb4187334f7018a0ee1960a7470586/rerankers/jev.py)
  - [eval.py](https://github.com/anessbelbati/jev-rerank-bench/blob/cd9a35b22aeb4187334f7018a0ee1960a7470586/eval.py)
  - [significance.py](https://github.com/anessbelbati/jev-rerank-bench/blob/cd9a35b22aeb4187334f7018a0ee1960a7470586/significance.py)
  - [cache](https://github.com/anessbelbati/jev-rerank-bench/tree/cd9a35b22aeb4187334f7018a0ee1960a7470586/cache)

### typesafe-ai/system-one-adapter-python

- Repositório: [typesafe-ai/system-one-adapter-python](https://github.com/typesafe-ai/system-one-adapter-python)
- Revisão: `adffc2eab300a4fa3c0e92252d4ffd6ceaa53700`
- Data do commit: `2026-09-18T10:47:43Z`
- Cópia local: `research/sources/system-one-adapter-python/`
- Estrutura na raiz: `.github`, `.gitignore`, `.python-version`, `LICENSE`, `README.md`, `docs`, `pyproject.toml`, `pyrefly.toml`, `src`, `tests`, `uv.lock`.
- Arquivos/pastas de entrada:
  - [README.md](https://github.com/typesafe-ai/system-one-adapter-python/blob/adffc2eab300a4fa3c0e92252d4ffd6ceaa53700/README.md)
  - [src/system_one_adapter/providers/openai.py](https://github.com/typesafe-ai/system-one-adapter-python/blob/adffc2eab300a4fa3c0e92252d4ffd6ceaa53700/src/system_one_adapter/providers/openai.py)
  - [tests](https://github.com/typesafe-ai/system-one-adapter-python/tree/adffc2eab300a4fa3c0e92252d4ffd6ceaa53700/tests)

### devagrawal09/jev-review

- Repositório: [devagrawal09/jev-review](https://github.com/devagrawal09/jev-review)
- Revisão: `31f89602797fb7bea007f8a480bf368bf564954e`
- Data do commit: `2026-09-17T05:59:22+05:30`
- Cópia local: `research/sources/jev-review/`
- Estrutura na raiz: `.env.example`, `.gitignore`, `LICENSE`, `README.md`, `docs`, `package-lock.json`, `package.json`, `scripts`, `src`, `tsconfig.json`.
- Arquivos/pastas de entrada:
  - [README.md](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/README.md)
  - [src/review/judgments.ts](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts)
  - [src/review/codebase-judgments.ts](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/codebase-judgments.ts)
  - [src/domain](https://github.com/devagrawal09/jev-review/tree/31f89602797fb7bea007f8a480bf368bf564954e/src/domain)
  - [scripts/check-dependencies.ts](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/scripts/check-dependencies.ts)

### sufianetaouil/every

- Repositório: [sufianetaouil/every](https://github.com/sufianetaouil/every)
- Revisão: `aaa72d582a831420dfd23a788e3bc948c798c248`
- Data do commit: `2026-09-17T07:02:19+01:00`
- Cópia local: `research/sources/every/`
- Estrutura na raiz: `.gitignore`, `LICENSE`, `README.md`, `every`, `examples`, `pyproject.toml`, `reference`, `tests`.
- Arquivos/pastas de entrada:
  - [README.md](https://github.com/sufianetaouil/every/blob/aaa72d582a831420dfd23a788e3bc948c798c248/README.md)
  - [every/judge.py](https://github.com/sufianetaouil/every/blob/aaa72d582a831420dfd23a788e3bc948c798c248/every/judge.py)
  - [every/classify.py](https://github.com/sufianetaouil/every/blob/aaa72d582a831420dfd23a788e3bc948c798c248/every/classify.py)
  - [every/extract.py](https://github.com/sufianetaouil/every/blob/aaa72d582a831420dfd23a788e3bc948c798c248/every/extract.py)
  - [every/cache.py](https://github.com/sufianetaouil/every/blob/aaa72d582a831420dfd23a788e3bc948c798c248/every/cache.py)
  - [examples/recorded](https://github.com/sufianetaouil/every/tree/aaa72d582a831420dfd23a788e3bc948c798c248/examples/recorded)

### AbdelStark/heist-one

- Repositório: [AbdelStark/heist-one](https://github.com/AbdelStark/heist-one)
- Revisão: `632c9a55a1e5eb2cbf0b9f87db575f0b5eb36e8c`
- Data do commit: `2026-09-17T16:39:00+02:00`
- Cópia local: `research/sources/heist-one/`
- Estrutura na raiz: `.env.example`, `.github`, `.gitignore`, `.markdownlint-cli2.jsonc`, `.nvmrc`, `AGENTS.md`, `CHANGELOG.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `LICENSE`, `PRD.md`, `README.md`, `SECURITY.md`, `SPEC.md`, `apps`, `biome.json`, `docs`, `package.json`, `packages`, `playwright.config.ts`, `pnpm-lock.yaml`, `pnpm-workspace.yaml`, `scripts`, `tests`, `tsconfig.base.json`, `tsconfig.scripts.json`, `vitest.config.ts`.
- Arquivos/pastas de entrada:
  - [README.md](https://github.com/AbdelStark/heist-one/blob/632c9a55a1e5eb2cbf0b9f87db575f0b5eb36e8c/README.md)
  - [SPEC.md](https://github.com/AbdelStark/heist-one/blob/632c9a55a1e5eb2cbf0b9f87db575f0b5eb36e8c/SPEC.md)
  - [docs/LIVE-JEV-VERIFICATION.md](https://github.com/AbdelStark/heist-one/blob/632c9a55a1e5eb2cbf0b9f87db575f0b5eb36e8c/docs/LIVE-JEV-VERIFICATION.md)
  - [packages/game](https://github.com/AbdelStark/heist-one/tree/632c9a55a1e5eb2cbf0b9f87db575f0b5eb36e8c/packages/game)
  - [apps](https://github.com/AbdelStark/heist-one/tree/632c9a55a1e5eb2cbf0b9f87db575f0b5eb36e8c/apps)

### TheoLeeCJ/openjev

- Repositório: [TheoLeeCJ/openjev](https://github.com/TheoLeeCJ/openjev)
- Revisão: `b9cb32537e78be65f19abfcb1de8fc504b627d84`
- Data do commit: `2026-09-18T23:33:38+08:00`
- Cópia local: `research/sources/openjev/`
- Estrutura na raiz: `.gitignore`, `AGENTS.md`, `LICENSE`, `README.md`, `THIRD_PARTY.md`, `assets`, `benchmarks`, `demo`, `docs`, `examples`, `manifests`, `pyproject.toml`, `requirements.txt`, `results`, `src`, `tests`, `webgpu-demo`.
- Arquivos/pastas de entrada:
  - [README.md](https://github.com/TheoLeeCJ/openjev/blob/b9cb32537e78be65f19abfcb1de8fc504b627d84/README.md)
  - [docs/REPRODUCE.md](https://github.com/TheoLeeCJ/openjev/blob/b9cb32537e78be65f19abfcb1de8fc504b627d84/docs/REPRODUCE.md)
  - [benchmarks](https://github.com/TheoLeeCJ/openjev/tree/b9cb32537e78be65f19abfcb1de8fc504b627d84/benchmarks)
  - [results/raw](https://github.com/TheoLeeCJ/openjev/tree/b9cb32537e78be65f19abfcb1de8fc504b627d84/results/raw)
  - [webgpu-demo](https://github.com/TheoLeeCJ/openjev/tree/b9cb32537e78be65f19abfcb1de8fc504b627d84/webgpu-demo)

### AbdelStark/awesome-typesafe

- Repositório: [AbdelStark/awesome-typesafe](https://github.com/AbdelStark/awesome-typesafe)
- Revisão: `c2d5cf9d851e445fd50ae51fcae09bca5718e7c7`
- Data do commit: `2026-09-18T20:08:08+02:00`
- Cópia local: `research/sources/awesome-typesafe/`
- Estrutura na raiz: `.editorconfig`, `.github`, `.gitignore`, `.lycheeignore`, `.markdownlint-cli2.jsonc`, `404.html`, `CONTRIBUTING.md`, `LICENSE`, `README.md`, `_config.yml`, `_layouts`, `assets`, `index.md`, `scripts`.
- Arquivos/pastas de entrada:
  - [README.md](https://github.com/AbdelStark/awesome-typesafe/blob/c2d5cf9d851e445fd50ae51fcae09bca5718e7c7/README.md)

### typesafe-ai/skills

- Repositório: [typesafe-ai/skills](https://github.com/typesafe-ai/skills)
- Revisão: `65a39f393687675ce170e6094757de20370365b9`
- Data do commit: `2026-09-12T05:42:05Z`
- Cópia local: `research/sources/skills/`
- Estrutura na raiz: `.claude-plugin`, `LICENSE`, `README.md`, `skills`.
- Arquivos/pastas de entrada:
  - [README.md](https://github.com/typesafe-ai/skills/blob/65a39f393687675ce170e6094757de20370365b9/README.md)
  - [skills/typesafe-ai/SKILL.md](https://github.com/typesafe-ai/skills/blob/65a39f393687675ce170e6094757de20370365b9/skills/typesafe-ai/SKILL.md)

### Anil-matcha/awesome-jev-by-typesafe

- Repositório: [Anil-matcha/awesome-jev-by-typesafe](https://github.com/Anil-matcha/awesome-jev-by-typesafe)
- Revisão: `e0cd00b863841aaa2e7b6748b67704c6d39a566b`
- Data do commit: `2026-09-18T23:59:43+05:30`
- Cópia local: `research/sources/awesome-jev-by-typesafe/`
- Estrutura na raiz: `.gitignore`, `LICENSE`, `README.md`, `docs`, `examples`, `images`, `tests`.
- Arquivos/pastas de entrada:
  - [README.md](https://github.com/Anil-matcha/awesome-jev-by-typesafe/blob/e0cd00b863841aaa2e7b6748b67704c6d39a566b/README.md)
  - [examples](https://github.com/Anil-matcha/awesome-jev-by-typesafe/tree/e0cd00b863841aaa2e7b6748b67704c6d39a566b/examples)

### redrossa/pi-model-router

- Repositório: [redrossa/pi-model-router](https://github.com/redrossa/pi-model-router)
- Revisão: `31d8fc2441d5af458928040afbcc384314a34289`
- Data do commit: `2026-09-17T19:57:36-05:00`
- Cópia local: `research/sources/pi-model-router/`
- Estrutura na raiz: `.env.example`, `.gitignore`, `AGENTS.md`, `LICENSE`, `README.md`, `config`, `examples`, `package-lock.json`, `package.json`, `src`, `test`, `tsconfig.json`.
- Arquivos/pastas de entrada:
  - [README.md](https://github.com/redrossa/pi-model-router/blob/31d8fc2441d5af458928040afbcc384314a34289/README.md)
  - [src/jev.ts](https://github.com/redrossa/pi-model-router/blob/31d8fc2441d5af458928040afbcc384314a34289/src/jev.ts)
  - [src/router.ts](https://github.com/redrossa/pi-model-router/blob/31d8fc2441d5af458928040afbcc384314a34289/src/router.ts)
  - [src/context.ts](https://github.com/redrossa/pi-model-router/blob/31d8fc2441d5af458928040afbcc384314a34289/src/context.ts)
  - [src/extension.ts](https://github.com/redrossa/pi-model-router/blob/31d8fc2441d5af458928040afbcc384314a34289/src/extension.ts)
  - [config/default-criteria.json](https://github.com/redrossa/pi-model-router/blob/31d8fc2441d5af458928040afbcc384314a34289/config/default-criteria.json)

### hellogumbo/should-ai-kill-us-all

- Repositório: [hellogumbo/should-ai-kill-us-all](https://github.com/hellogumbo/should-ai-kill-us-all)
- Revisão: `6b6b55cbe05ec24c844db3a691e3521f65eae258`
- Data do commit: `2026-09-17T20:54:46-04:00`
- Cópia local: `research/sources/should-ai-kill-us-all/`
- Estrutura na raiz: `.claude`, `.dev.vars.example`, `.github`, `.gitignore`, `LICENSE`, `README.md`, `functions`, `package.json`, `public`, `scripts`, `wrangler.toml`.
- Arquivos/pastas de entrada:
  - [README.md](https://github.com/hellogumbo/should-ai-kill-us-all/blob/6b6b55cbe05ec24c844db3a691e3521f65eae258/README.md)
  - [functions/api/verdict.js](https://github.com/hellogumbo/should-ai-kill-us-all/blob/6b6b55cbe05ec24c844db3a691e3521f65eae258/functions/api/verdict.js)

### Infrawrench/Jeeves

- Repositório: [Infrawrench/Jeeves](https://github.com/Infrawrench/Jeeves)
- Revisão: `65bc21494e18fa7c2beca180c545eed6bc3ce4ce`
- Data do commit: `2026-09-18T16:35:24+01:00`
- Cópia local: `research/sources/Jeeves/`
- Estrutura na raiz: `.dockerignore`, `.env.example`, `.github`, `.gitignore`, `Cargo.lock`, `Cargo.toml`, `Dockerfile`, `LICENSE`, `README.md`, `build.rs`, `compose.yaml`, `deploy`, `examples`, `migrations`, `scripts`, `src`.
- Arquivos/pastas de entrada:
  - [README.md](https://github.com/Infrawrench/Jeeves/blob/65bc21494e18fa7c2beca180c545eed6bc3ce4ce/README.md)
  - [src/typesafe/client.rs](https://github.com/Infrawrench/Jeeves/blob/65bc21494e18fa7c2beca180c545eed6bc3ce4ce/src/typesafe/client.rs)
  - [src/gemini.rs](https://github.com/Infrawrench/Jeeves/blob/65bc21494e18fa7c2beca180c545eed6bc3ce4ce/src/gemini.rs)
  - [src/message_actions](https://github.com/Infrawrench/Jeeves/tree/65bc21494e18fa7c2beca180c545eed6bc3ce4ce/src/message_actions)
  - [src/moderation](https://github.com/Infrawrench/Jeeves/tree/65bc21494e18fa7c2beca180c545eed6bc3ce4ce/src/moderation)
  - [src/twitch](https://github.com/Infrawrench/Jeeves/tree/65bc21494e18fa7c2beca180c545eed6bc3ce4ce/src/twitch)

## Enquadramento da análise

Persona solicitada: skill local Helena Strategos Inteia, em `C:/Users/igorm/.claude/skills/helena/SKILL.md`, com protocolo POLARIS e revisão por contra-hipóteses. Usada como estrutura analítica; nenhum experimento ou resultado foi simulado para compor a decisão.

Inspeção estática de trechos centrais e documentação, não auditoria de cada linha. Métricas de autores permanecem resultados publicados por eles. Contagens de arquivos de teste no manifesto são inventário por nome/caminho, não cobertura e não execução; testes embutidos em arquivos podem não entrar nessa contagem.
