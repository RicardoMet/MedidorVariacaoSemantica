"""
Análise de Variabilidade Semântica em Construções Sintáticas (Português)

Autor: [O Teu Nome]
Descrição:
-----------
Este script processa ficheiros XML contendo resultados de KWIC (Key Word in Context)
extraídos de corpora através de expressões regulares.

Suporta três tipos de construções:
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

# =========================
# 🔧 Dependências e setup
# =========================
import pandas as pd
from bs4 import BeautifulSoup
import re
import spacy
import nltk
from nltk.corpus import wordnet as wn
from datetime import datetime

# Downloads necessários (apenas na 1ª execução)
nltk.download('wordnet')
nltk.download('omw-1.4')
import subprocess
subprocess.run(["python", "-m", "spacy", "download", "pt_core_news_lg"])

nlp = spacy.load("pt_core_news_lg")

# ======================
# 📁 Input
# ======================
file = "input.xml"          # <- caminho do ficheiro XML
tipo_construcao = "svo"     # 'svo', 'n_adj', 'adj_n'

# =============================
# 🧹 Pré-processamento
# =============================
def limpar_kwic(texto_kwic):
    return re.sub(r"/[a-z]+", "", texto_kwic)

with open(file, "r", encoding="utf-8") as f:
    xml = f.read()

soup = BeautifulSoup(xml, "xml")
kwics = soup.find_all("kwic")
kwic_pairs = [(limpar_kwic(k.text.strip()), k.text.strip()) for k in kwics]

# ===================================
# 📐 Extração sintática
# ===================================
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

# ===============================
# 🧠 Domínios WordNet
# ===============================
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
    'noun.phenomenon': 'fenômeno',
}

def obter_dominios(word, lang='por'):
    if not word:
        return "desconhecido", "desconhecido"
    synsets = wn.synsets(word, lang=lang)
    if not synsets:
        return "desconhecido", "desconhecido"
    primeiro = synsets[0]
    subdominio = primeiro.lexname()
    dominio_mapeado = mapeamento_dominios.get(subdominio, "outro")
    return dominio_mapeado, subdominio

# ========================================
# 🔄 Processamento das frases
# ========================================
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

for entrada in dados:
    if tipo_construcao == "svo":
        entrada["dominio"], entrada["subdominio"] = obter_dominios(entrada["objeto"])
        entrada["dominio_sujeito"], entrada["subdominio_sujeito"] = obter_dominios(entrada["sujeito"])
        entrada["construcao"] = f"{entrada['verbo']} X"
    elif tipo_construcao == "n_adj":
        entrada["dominio"], entrada["subdominio"] = obter_dominios(entrada["nome"])
        entrada["construcao"] = f"{entrada['nome']} + {entrada['adjetivo']}"
    elif tipo_construcao == "adj_n":
        entrada["dominio"], entrada["subdominio"] = obter_dominios(entrada["nome"])
        entrada["construcao"] = f"{entrada['adjetivo']} {entrada['nome']}"

df = pd.DataFrame(dados)

# ========================================
# 📊 Variabilidade semântica
# ========================================
if tipo_construcao == "svo":
    # verbo → objeto
    agrupados_verbo_obj = df.groupby("verbo")["dominio"].apply(list)
    df_var_verbo_obj = agrupados_verbo_obj.apply(lambda x: pd.Series({
        "variabilidade_verbo_obj": len(set(x)),
        "dominios_obj": ", ".join(sorted(set(x)))
    })).reset_index()

    # verbo → sujeito
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

# ===============================
# 📤 Exportar para Excel
# ===============================
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_path = f"output_variabilidade_{tipo_construcao}_{timestamp}.xlsx"

with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    df.to_excel(writer, index=False, sheet_name="Construcoes")

    if tipo_construcao == "svo":
        df_var_obj_sorted = df_var_verbo_obj.sort_values(by="variabilidade_verbo_obj", ascending=False)
        df_var_suj_sorted = df_var_verbo_suj.sort_values(by="variabilidade_verbo_suj", ascending=False)
        df_var_obj_sorted.to_excel(writer, index=False, sheet_name="Variabilidade_verbo_objeto")
        df_var_suj_sorted.to_excel(writer, index=False, sheet_name="Variabilidade_verbo_sujeito")

    elif tipo_construcao == "n_adj":
        df_var_nome_sorted = df_var_nome.sort_values(by="variabilidade_nome", ascending=False)
        df_var_adj_sorted = df_var_adj.sort_values(by="variabilidade_adjetivo", ascending=False)
        df_var_nome_sorted.to_excel(writer, index=False, sheet_name="Variabilidade_nome")
        df_var_adj_sorted.to_excel(writer, index=False, sheet_name="Variabilidade_adjetivo")

    elif tipo_construcao == "adj_n":
        df_var_sorted = df_var.sort_values(by="variabilidade_semântica", ascending=False)
        df_var_sorted.to_excel(writer, index=False, sheet_name="Variabilidade")

print(f"📁 Ficheiro exportado com sucesso: {output_path}")
