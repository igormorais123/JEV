# E15 — limites e implantação assistida do JEV

Registro anterior às chamadas desta rodada, 2026-09-19. Autor: Codex.

## Perguntas e decisões congeladas

1. H1: a falha de diluição do R11 é causada por truncamento do cliente. Reproduzir
   offline a perda da mensagem e comparar, em chamadas reais, preservação integral
   versus truncamento legado. Se o payload perde a mensagem, o resultado não mede
   compreensão de contexto. Caracteres e tokens serão registrados separadamente.
2. H2: classificação de falhas e seleção de contexto podem auxiliar o Codex com
   escolhas fechadas. Usar evidências públicas do próprio código/testes, registrando
   origem e hash, mais contrastes sintéticos claramente identificados. Separar as
   duas populações. Nenhum resultado sintético será chamado de tráfego de produção.
3. H3: contrato inválido, orçamento, segredo ou excesso de entrada causam abstenção,
   sem truncamento silencioso nem autorização de ação. Testar offline antes da rede.
4. H4: confiança >=0,95 permite aceitar classificações não críticas nesta amostra.
   Congelar o corte antes da execução; reportar erro seletivo, cobertura e Wilson 95%.
   Não reajustar o corte no teste. Só habilitar sugestão assistida se houver ao menos
   90% de acerto, nenhum erro aceito e contrato válido em todos os casos. Sem dados
   suficientes, manter experimental. Autonomia requer limite superior de erro <5%
   em casos independentes e confirmação em outro conjunto; esta rodada não promete isso.

## Desenho e limites

- Até 100 chamadas iniciais; teto do bloco US$ 0,20 e teto global acumulado US$ 5.
- Nenhuma chamada antes da reserva persistente pelo contexto máximo publicado.
- Preço consultado novamente no endpoint público; falha na consulta bloqueia rede.
- Contabilizar histórico dos outros consumidores conservadoramente; nunca zerá-lo.
- Reutilizar o ledger SQLite e encaminhar laboratório e integração pelo mesmo controle.
- Sem retry automático nesta rodada; falhas são resultados programados e têm denominador.
- Persistir payload público/sanitizado, hash, rubrica, versão resolvida, latência,
  uso e cobrança real, status, escolha, confiança, fonte e gabarito anterior à chamada.
- Registrar timestamps e SHA-256 deste protocolo e do corpus antes de despachar.
- Economia de Astra é NÃO MEDIDA até comparação completa. Bytes selecionados não são
  tokens poupados nem redução de mensalidade. Revisão do gabarito pelo próprio autor
  é limitação explícita; resultados por família não são observações independentes.

## Implantação

Corrigir primeiro o caminho financeiro e a perda silenciosa de entrada. Disponibilizar
classificação e ordenação como ferramenta assistida, com referências recuperáveis e
abstenção. Sem substituição automática do Astra, envio externo, comando ou decisão jurídica.
Preservar dados e artefatos anteriores; emendas e resultados entram em documentos separados.
