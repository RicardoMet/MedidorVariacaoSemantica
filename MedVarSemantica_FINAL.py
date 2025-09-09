"""
Análise de Variabilidade Semântica em verbos e adjetivos (Português)

Autor: Ricardo Monteiro
Descrição:
-----------
Este script processa ficheiros XML contendo resultados de KWIC (Key Word in Context)
extraídos de corpora através de expressões regulares.

Executa três tipos de construções:
- 'svo'   → Sujeito + Verbo + Objeto
- 'n_adj' → Nome + Adjetivo
- 'adj_n' → Adjetivo + Nome

Funcionalidades:
----------------
1. Extrai construções sintáticas via spaCy.
2. Atribui domínios semânticos a nomes, verbos e adjetivos via WordNet.
3. Calcula variabilidade semântica de cada elemento:
   - Para SVO: verbo em relação a objetos **e** sujeitos.
   - Para n_adj: nome e adjetivo.
   - Para adj_n: adjetivo.
4. Exporta resultados para Excel com várias folhas:
   - Construções extraídas
   - Tabelas de variabilidade
5. Imprime estatísticas no terminal.

Input:
------
- Ficheiro XML com KWICs (resultados de pesquisa por expressão regular).

Output:
-------
- Excel com os resultados da análise.

"""

#!/usr/bin/env python3
"""
analise_variabilidade.py

Análise de Variabilidade Semântica em Construções Sintáticas (Português)

- Suporta: 'svo' (sujeito+verbo+objeto), 'n_adj' (nome+adjetivo), 'adj_n' (adjetivo+nome)
- Usa spaCy (pt_core_news_lg) + WordNet (NLTK) para extrair informação e domínios
- Exporta resultados para Excel com timestamp no nome
- Pensado para correr em Google Colab, mas também executável localmente
"""

import sys
import os
import subprocess
from datetime import datetime

# ---------------------------
# Instala dependências se necessário
# ---------------------------
def ensure_package(pkg):
    try:
        __import__(pkg)
    except Exception:
        print(f"Package '{pkg}' not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

# Pacotes python necessários
for p in ("pandas", "openpyxl", "beautifulsoup4", "spacy", "nltk"):
    ensure_package(p)

# Instala / garante o modelo spaCy PT
try:
    import spacy
    spacy.load("pt_core_news_lg")
except Exception:
    print("Installing spaCy model 'pt_core_news_lg'...")
    subprocess.check_call([sys.executable, "-m", "spacy", "download", "pt_core_news_lg"])

# ---------------------------
# Imports principais
# ---------------------------
import pandas as pd
import re
import spacy
import nltk
from bs4 import BeautifulSoup
from nltk.corpus import wordnet as wn

# Downloads NLTK data se necessário
nltk.download('wordnet', quiet=True)
nltk.download('omw-1.4', quiet=True)

nlp = spacy.load("pt_core_news_lg")

# ---------------------------
# CONFIGURAÇÕES DO UTILIZADOR
# ---------------------------
# Se estiveres a correr no Colab, podes escolher o ficheiro no teu Drive.
# Se estiveres a correr localmente, substitui o FILE_PATH por algo local: FILE_PATH = "exemplo_input.xml"

FILE_PATH = "/content/drive/MyDrive/Constructions_concordances/EXEMPLO.xml"

# Escolhe: 'svo', 'n_adj', 'adj_n'
tipo_construcao = "svo"

# ---------------------------
# (Opcional) Montar Google Drive em Colab - só faz sentido no Colab
# ---------------------------
try:
    from google.colab import drive as _drive
    # Apenas monta se o path começar por /content/drive e não estiver montado
    if FILE_PATH.startswith("/content/drive") and not os.path.exists("/content/drive/MyDrive"):
        print("Montando Google Drive...")
        _drive.mount('/content/drive/')
except Exception:
    # Não estamos no Colab; prosseguir sem montar drive
    pass

# ---------------------------
# Funções utilitárias
# ---------------------------
def limpar_kwic(texto_kwic):
    """Remove anotações do KWIC como '/tag'."""
    return re.sub(r"/[a-zA-Z]+", "", texto_kwic)

def extrair_svo(frase):
    doc = nlp(frase)
    sujeito = verbo = objeto = None
    for token in doc:
        if token.dep_ == "ROOT" and token.pos_ == "VERB":
            verbo = token.lemma_
        elif token.dep_ == "nsubj":
            sujeito = token.text
        elif token.dep_ in {"obj", "dobj", "obl", "attr"}:
            objeto = token.lemma_
    if verbo and (sujeito or objeto):
        return {
            "frase_limpa": frase,
            "sujeito": sujeito if sujeito else "",
            "verbo": verbo,
            "objeto": objeto if objeto else ""
        }
    return None

def extrair_n_adj(frase):
    doc = nlp(frase)
    for token in doc:
        if token.pos_ == "ADJ" and token.head.pos_ == "NOUN":
            return {"frase_limpa": frase, "nome": token.head.lemma_, "adjetivo": token.lemma_}
    return None

def extrair_adj_n(frase):
    doc = nlp(frase)
    for token in doc:
        if token.pos_ == "ADJ" and token.head.pos_ == "NOUN" and token.i < token.head.i:
            return {"frase_limpa": frase, "adjetivo": token.lemma_, "nome": token.head.lemma_}
    for i in range(len(doc) - 1):
        if doc[i].pos_ == "ADJ" and doc[i + 1].pos_ == "NOUN":
            return {"frase_limpa": frase, "adjetivo": doc[i].lemma_, "nome": doc[i + 1].lemma_}
    return None

# Mapeamento de subdomínios WordNet -> domínios abrangentes (ajusta conforme necessário)
mapeamento_dominios = {
    'noun.person': 'pessoa',
    'noun.artifact': 'objeto',
    'noun.act': 'evento',
    'noun.event': 'evento',
    'noun.group': 'organização',
    'noun.location': 'lugar',
    'noun.communication': 'comunicação',
    'noun.state': 'estado',
    'noun.cognition': 'conhecimento',
    'noun.quantity': 'quantidade',
    'noun.attribute': 'característica',
    'noun.time': 'tempo',
    'noun.animal': 'animal',
    'noun.body': 'corpo',
    'noun.food': 'comida',
    'noun.substance': 'matéria',
    'noun.object': 'objeto',
    'noun.feeling': 'emoção',
    'noun.phenomenon': 'fenómeno',
}

def obter_dominios(word, lang='por'):
    """Retorna (dominio, subdominio) para uma palavra; 'desconhecido' se nada for encontrado."""
    if not word or str(word).strip() == "":
        return "desconhecido", "desconhecido"
    try:
        synsets = wn.synsets(word, lang=lang)
    except Exception:
        synsets = []
    if not synsets:
        return "desconhecido", "desconhecido"
    primeiro = synsets[0]
    subdominio = primeiro.lexname()
    dominio_mapeado = mapeamento_dominios.get(subdominio, "outro")
    return dominio_mapeado, subdominio

# ---------------------------
# Leitura do ficheiro XML
# ---------------------------
if not os.path.exists(FILE_PATH):
    raise FileNotFoundError(f"Arquivo não encontrado: {FILE_PATH}\nAltera FILE_PATH para o caminho correto.")

with open(FILE_PATH, "r", encoding="utf-8") as f:
    xml = f.read()

soup = BeautifulSoup(xml, "xml")
kwics = soup.find_all("kwic")
kwic_pairs = [(limpar_kwic(k.text.strip()), k.text.strip()) for k in kwics]

frases_limpas = [p[0] for p in kwic_pairs]
frases_originais = [p[1] for p in kwic_pairs]

# ---------------------------
# Extrair e construir dataset
# ---------------------------
dados = []
for frase_limpa, frase_original in kwic_pairs:
    if tipo_construcao == "svo":
        extraido = extrair_svo(frase_limpa)
    elif tipo_construcao == "n_adj":
        extraido = extrair_n_adj(frase_limpa)
    elif tipo_construcao == "adj_n":
        extraido = extrair_adj_n(frase_limpa)
    else:
        extraido = None
    if extraido:
        extraido["frase_original"] = frase_original
        extraido["frase_limpa"] = frase_limpa
        dados.append(extraido)

print(f"Número de frases extraídas: {len(dados)}")

# Preenche domínios

for entrada in dados:
    if tipo_construcao == "svo":
        entrada["dominio"], entrada["subdominio"] = obter_dominios(entrada.get("objeto", ""))
        entrada["dominio_sujeito"], entrada["subdominio_sujeito"] = obter_dominios(entrada.get("sujeito", ""))
        entrada["construcao"] = f"{entrada['verbo']} X"
    elif tipo_construcao == "n_adj":
        entrada["dominio"], entrada["subdominio"] = obter_dominios(entrada.get("nome", ""))
        entrada["construcao"] = f"{entrada['nome']} + {entrada['adjetivo']}"
    elif tipo_construcao == "adj_n":
        entrada["dominio"], entrada["subdominio"] = obter_dominios(entrada.get("nome", ""))
        entrada["construcao"] = f"{entrada['adjetivo']} {entrada['nome']}"

df = pd.DataFrame(dados)

# Normalização de tokens para comparações
if tipo_construcao in ["n_adj", "adj_n"]:
    df["nome"] = df["nome"].astype(str).str.lower()
    df["adjetivo"] = df["adjetivo"].astype(str).str.lower()

if tipo_construcao == "svo":
    # remover Verbos Leves
    verbos_leves = {"fazer", "ter", "dar", "estar", "haver", "ficar", "pôr", "levar", "deixar", "manter"}
    df = df[~df["verbo"].isin(verbos_leves)].copy()

# ---------------------------
# Cálculo da variabilidade
# ---------------------------
if tipo_construcao == "svo":
    agrupados_verbo_obj = df.groupby("verbo")["dominio"].apply(list)
    df_var_verbo_obj = agrupados_verbo_obj.apply(lambda x: pd.Series({
        "variabilidade_verbo_obj": len(set(x)),
        "dominios_obj": ", ".join(sorted(set(x)))
    })).reset_index()

    agrupados_verbo_suj = df.groupby("verbo")["dominio_sujeito"].apply(list)
    df_var_verbo_suj = agrupados_verbo_suj.apply(lambda x: pd.Series({
        "variabilidade_verbo_suj": len(set(x)),
        "dominios_suj": ", ".join(sorted(set(x)))
    })).reset_index()

elif tipo_construcao == "adj_n":
    agrupados = df.groupby("adjetivo")["dominio"].apply(list)
    df_var = agrupados.apply(lambda x: pd.Series({
        "variabilidade_semântica": len(set(x)),
        "dominios": ", ".join(sorted(set(x)))
    })).reset_index()
    df_var = df_var.rename(columns={"adjetivo": "construcao"})

elif tipo_construcao == "n_adj":
    df['dominio_adjetivo'], df['subdominio_adjetivo'] = zip(*df['adjetivo'].apply(obter_dominios))
    agrupados_nome = df.groupby("nome")["dominio_adjetivo"].apply(list)
    df_var_nome = agrupados_nome.apply(lambda x: pd.Series({
        "variabilidade_nome": len(set(x)),
        "dominios": ", ".join(sorted(set(x)))
    })).reset_index()
    agrupados_adj = df.groupby("adjetivo")["dominio"].apply(list)
    df_var_adj = agrupados_adj.apply(lambda x: pd.Series({
        "variabilidade_adjetivo": len(set(x)),
        "dominios": ", ".join(sorted(set(x)))
    })).reset_index()

# ---------------------------
# Mostrar resultados no terminal (resumo)
# ---------------------------
print(f"\n📊 Top 10 construções ({tipo_construcao}):\n")

if tipo_construcao == "n_adj":
    df_var_nome_sorted = df_var_nome.sort_values(by="variabilidade_nome", ascending=False)
    df_var_adj_sorted = df_var_adj.sort_values(by="variabilidade_adjetivo", ascending=False)

    print("🔸 Variabilidade por nome:")
    print(df_var_nome_sorted.head(10).to_string(index=False))
    print("\n🔸 Variabilidade por adjetivo:")
    print(df_var_adj_sorted.head(10).to_string(index=False))

    print("\n📌 Exemplos para os 5 nomes mais variáveis:")
    for nome in df_var_nome_sorted.head(5)["nome"]:
        print(f"\n🔹 Nome: {nome}")
        frases_filtradas = df[df["nome"] == nome].head(4)
        for _, row in frases_filtradas.iterrows():
            print(f" - {row['frase_limpa']} | adj: {row['adjetivo']} | dom_adjetivo: {row['dominio_adjetivo']}")

    print("\n📌 Exemplos para os 5 adjetivos mais variáveis:")
    for adj in df_var_adj_sorted.head(5)["adjetivo"]:
        print(f"\n🔹 Adjetivo: {adj}")
        frases_filtradas = df[df["adjetivo"] == adj].head(4)
        for _, row in frases_filtradas.iterrows():
            print(f" - {row['frase_limpa']} | nome: {row['nome']} | dom_nome: {row['dominio']}")

elif tipo_construcao == "svo":
    df_var_obj_sorted = df_var_verbo_obj.sort_values(by="variabilidade_verbo_obj", ascending=False)
    df_var_suj_sorted = df_var_verbo_suj.sort_values(by="variabilidade_verbo_suj", ascending=False)

    print("🔸 Variabilidade verbo → objeto:")
    print(df_var_obj_sorted.head(10).to_string(index=False))

    print("\n🔸 Variabilidade verbo → sujeito:")
    print(df_var_suj_sorted.head(10).to_string(index=False))

    print("\n📌 Exemplos (verbo → objeto):")
    for verbo in df_var_obj_sorted.head(5)["verbo"]:
        print(f"\n🔹 Verbo: {verbo}")
        frases_filtradas = df[df["verbo"] == verbo].head(4)
        for _, row in frases_filtradas.iterrows():
            print(f" - {row['frase_limpa']} | objeto: {row['objeto']} | dom_obj: {row['dominio']}")

    print("\n📌 Exemplos (verbo → sujeito):")
    for verbo in df_var_suj_sorted.head(5)["verbo"]:
        print(f"\n🔹 Verbo: {verbo}")
        frases_filtradas = df[df["verbo"] == verbo].head(4)
        for _, row in frases_filtradas.iterrows():
            print(f" - {row['frase_limpa']} | sujeito: {row['sujeito']} | dom_suj: {row['dominio_sujeito']}")

elif tipo_construcao == "adj_n":
    df_var_sorted = df_var.sort_values(by="variabilidade_semântica", ascending=False)
    print(df_var_sorted.head(10).to_string(index=False))
    print("\n📌 Exemplos:")
    for adj in df_var_sorted.head(5)["construcao"].str.split().str[0]:
        frases_filtradas = df[df["adjetivo"] == adj].head(4)
        for _, row in frases_filtradas.iterrows():
            print(f" - {row['frase_limpa']} | nome: {row['nome']} | dom_nome: {row['dominio']}")

# ---------------------------
# Estatísticas de cobertura
# ---------------------------
total = len(df)
desconhecidos = df[df['dominio'] == "desconhecido"].shape[0]
percentagem = 100 * (total - desconhecidos) / total if total else 0
print(f"\n📊 Percentagem de Domínios Atribuídos: {percentagem:.2f}% (desconhecido: {100-percentagem:.2f}%)")

# ---------------------------
# Exportação para Excel (com timestamp)
# ---------------------------
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_path = f"/content/drive/MyDrive/Constructions_concordances/output_variabilidade_{tipo_construcao}_{timestamp}.xlsx" \
    if FILE_PATH.startswith("/content/drive") else f"output_variabilidade_{tipo_construcao}_{timestamp}.xlsx"

with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    df.to_excel(writer, index=False, sheet_name="Construcoes")

    if tipo_construcao == "svo":
        df_var_obj_sorted.to_excel(writer, index=False, sheet_name="Variabilidade_verbo_objeto")
        df_var_suj_sorted.to_excel(writer, index=False, sheet_name="Variabilidade_verbo_sujeito")
    elif tipo_construcao == "n_adj":
        df_var_nome_sorted.to_excel(writer, index=False, sheet_name="Variabilidade_nome")
        df_var_adj_sorted.to_excel(writer, index=False, sheet_name="Variabilidade_adjetivo")
    elif tipo_construcao == "adj_n":
        df_var_sorted.to_excel(writer, index=False, sheet_name="Variabilidade")

print(f"\n📁 Ficheiro exportado com sucesso: {output_path}")
