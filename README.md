# CNE AI

Esta versão do projecto inclui um pequeno front-end web para testar o processamento de documentos com os Operadores A e B.

## Requisitos

* Python 3.11 ou superior
* [pip](https://pip.pypa.io/en/stable/)

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate  # No Windows use `.venv\Scripts\activate`
pip install -r requirements.txt
```

A aplicação depende de um modelo de linguagem spaCy. Para efeitos de teste basta descarregar o modelo português leve:

```bash
python -m spacy download pt_core_news_sm
```

## Executar a aplicação web

```bash
flask --app webapp.app --debug run
```

Por omissão o servidor fica disponível em <http://127.0.0.1:5000>. A interface permite carregar um ficheiro DOCX e devolve um ficheiro ZIP com os CSV gerados pelos dois operadores.

## Testes rápidos

Para verificar que o código compila correctamente execute:

```bash
python -m compileall SpacyOperator.py cne_ai webapp scripts
```

Também pode verificar se o extractor de tabelas funciona através da linha de comandos:

```bash
python scripts/05_extract_docx_tables_am_cm.py caminho/para/documento.docx
```

Os CSV resultantes serão colocados na pasta `tables` por omissão.
