# CNE AI

Esta versão do projecto inclui um pequeno front-end web para testar o processamento de documentos com os Operadores A e B.

## Requisitos

* Python 3.11 ou superior
* [pip](https://pip.pypa.io/en/stable/)

## Instalação

Todos os comandos apresentados assumem que está na pasta do projecto.

### Instalação directa (sem ambiente virtual)

Se preferir trabalhar apenas com o Python já instalado no seu sistema, execute:

```bash
pip install -r requirements.txt
python -m spacy download pt_core_news_sm
```

### Instalação isolada (opcional)

Caso queira manter as dependências separadas do resto do sistema pode criar um ambiente virtual:

```bash
python -m venv .venv
source .venv/bin/activate  # No Windows use `.venv\Scripts\activate`
pip install -r requirements.txt
python -m spacy download pt_core_news_sm
```

### Preparação para uma instalação offline

Se precisar de configurar a aplicação numa máquina sem acesso à internet:

1. Num computador com ligação, crie um ambiente temporário e faça o download das dependências e do modelo spaCy para uma pasta portátil:
   ```bash
   python -m venv fetch-env
   source fetch-env/bin/activate
   pip download -r requirements.txt -d offline-packages
   pip download pt_core_news_sm -d offline-packages
   deactivate
   ```
2. Copie o repositório e a pasta `offline-packages` para a máquina offline (por exemplo, através de uma pen USB).
3. Na máquina offline, crie um ambiente virtual, active-o e instale as dependências a partir da pasta copiada:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install --no-index --find-links=offline-packages -r requirements.txt
   pip install --no-index --find-links=offline-packages pt_core_news_sm
   ```
   No Windows substitua o comando de activação por `.venv\Scripts\activate`.

## Executar a aplicação web

```bash
flask --app webapp.app --debug run
```

Por omissão o servidor fica disponível em <http://127.0.0.1:5000>. A interface permite carregar um ficheiro DOCX e devolve um ficheiro ZIP com os CSV gerados pelos dois operadores. Pode manter o terminal aberto com o comando acima a correr e, se necessário, interromper com `Ctrl+C`.

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

