# MedidorVariacaoSemantica

Este repositório contém um script em Python para analisar construções sintáticas extraídas de corpora em português europeu, medindo a sua variabilidade semântica de adjetivos e verbos.
Esta medição é feita através do cálculo dos diferentes domínios conceptuais associados aos nomes que ocorrem com o adjetivo ou verbo sob análise.
Quanto mais domínios poderem ocorrer com o verbo ou adjetivo, maior é a sua variação semântica, a qual poderá indicar um uso metafórico.

## Funcionalidades
- Suporte a três tipos de construções:
  - `svo`: Sujeito + Verbo + Objeto
  - `n_adj`: Nome + Adjetivo
  - `adj_n`: Adjetivo + Nome
- Atribuição de domínios semânticos via WordNet.
- Cálculo de variabilidade semântica.
- Exportação de resultados para Excel.

## Requisitos
```bash
pip install -r requirements.txt
python -m spacy download pt_core_news_lg
