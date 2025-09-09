# MedidorVariacaoSemantica

Este repositório contém um script em Python para analisar construções sintáticas extraídas de corpora em português europeu, medindo a sua variabilidade semântica de adjetivos e verbos.
Esta medição é feita através do cálculo dos diferentes domínios conceptuais associados aos nomes que ocorrem com o adjetivo ou verbo sob análise.
Quanto mais domínios poderem ocorrer com o verbo ou adjetivo, maior é a sua variação semântica, a qual poderá indicar um uso metafórico.


Qualquer dúvida ou questão, contactar: ricardo.santos.monteiro@campus.fcsh.unl.pt

## Funcionalidades
- Suporte a três tipos de construções:
  - `svo`: Sujeito + Verbo + Objeto
  - `n_adj`: Nome + Adjetivo
  - `adj_n`: Adjetivo + Nome
- Atribuição de domínios semânticos via WordNet.
- Cálculo de variabilidade semântica.
- Exportação de resultados para Excel.

## Ficheiro input
O ficheiro input deverá ser um XML, descarregado de uma pesquisa em corpous através do SketchEngine.

De modo a que o parser sintático opere da melhor forma, os elementos dos três tipos de construções devem ser respeitados, contendo os KWICs destas apenas os elementos em questão.
Desta forma, deve ser feita uma pesquisa através de expressões regulares. As seguintes expressões regulares (ou pequenas variações das mesmas) são aconselhadas:
- Para a construção SVO: `[tag="NC.*"] [tag="VM.*"] [tag="NC.*"]`




## Requisitos
```bash
pip install -r requirements.txt
python -m spacy download pt_core_news_lg

