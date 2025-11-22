# 📊 Banco de Dados Legis-AI

Este projeto coleta e armazena proposições legislativas (PL, PEC, MPV) de 2024 diretamente no PostgreSQL, extraindo dados da API da Câmara dos Deputados e trechos dos PDFs das proposições.

---

## 📋 **Sumário**
- [Requisitos](#requisitos)
- [Instalação do PostgreSQL](#instalação-do-postgresql)
- [Configuração do Banco](#configuração-do-banco)
- [Instalação das Dependências](#instalação-das-dependências)
- [Execução](#execução)
- [Backup e Restore](#backup-e-restore)
- [Estrutura do Banco](#estrutura-do-banco)
- [Exemplos de Consultas](#exemplos-de-consultas)

---

## 🔧 **Requisitos**

- Python 3.8+
- PostgreSQL 14+
- Ubuntu 20.04+ (ou distribuição compatível)

---

## 🐘 **Instalação do PostgreSQL**

```bash
# Atualize os repositórios
sudo apt update

# Instale o PostgreSQL
sudo apt install postgresql postgresql-contrib

# Verifique se o serviço está ativo
sudo systemctl status postgresql

# (Opcional) Configure para iniciar automaticamente
sudo systemctl enable postgresql
```

### Criar usuário e banco de dados

```bash
# Acesse o PostgreSQL
sudo -u postgres psql

# Dentro do psql, execute:
CREATE USER seu_usuario WITH LOGIN CREATEDB PASSWORD 'sua_senha';
CREATE DATABASE legislativo_2024 OWNER seu_usuario;
\q
```

**Substitua `seu_usuario` e `sua_senha` pelas suas credenciais.**

---

## 📦 **Instalação das Dependências Python**

```bash
# Clone ou baixe o projeto
cd /caminho/para/o/projeto

# Instale as dependências
pip install -r requirements.txt
```

Ou instale manualmente:

```bash
pip install psycopg2-binary pdfplumber requests urllib3
```

---

## ⚙️ **Configuração do Banco**

Execute o script SQL para criar a tabela e os índices:

```bash
psql -h localhost -U seu_usuario -d legislativo_2024 -f setup_banco.sql
```

Ou cole diretamente no pgAdmin:

```sql
-- Criação da tabela
CREATE TABLE proposicoes_legislativas (
    id SERIAL PRIMARY KEY,
    numero INTEGER NOT NULL,
    tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('PL', 'PEC', 'MPV')),
    ano INTEGER NOT NULL,
    data_apresentacao TIMESTAMP,
    ementa_resumo TEXT,
    artigo_1_trecho TEXT,
    link_pdf TEXT,
    
    CONSTRAINT unico_proposicao UNIQUE (tipo, numero, ano)
);

-- Índices para otimização
CREATE INDEX idx_tipo ON proposicoes_legislativas(tipo);
CREATE INDEX idx_ano ON proposicoes_legislativas(ano);
CREATE INDEX idx_data_apresentacao ON proposicoes_legislativas(data_apresentacao DESC);

-- Comentários para documentação
COMMENT ON TABLE proposicoes_legislativas IS 'Repositório de Projetos de Lei, Emendas Constitucionais e Medidas Provisórias';
```

---

## 🚀 **Execução do Script**

```bash
python import_legislativo.py
```

O script mostrará progresso no terminal:
```
================================================
⏩ PROCESSANDO: PL
================================================
  📄 Página 1... | 15 itens encontrados.
    ✅ Inseridas 15 novas proposições.
================================================
⏩ PROCESSANDO: PEC
================================================
...
```

### Configurar credenciais do banco

Edite as variáveis no início do script `import_legislativo.py`:

```python
DB_CONFIG = {
    'dbname': 'legislativo_2024',
    'user': 'seu_usuario',
    'password': 'sua_senha',
    'host': 'localhost',
    'port': '5432'
}
```

---

## 💾 **Backup e Restore**

### **Exportar (backup)**
```bash
# Formato SQL simples
pg_dump -h localhost -U seu_usuario -d legislativo_2024 -f backup_legislativo.sql

# Formato compactado (recomendado)
pg_dump -h localhost -U seu_usuario -d legislativo_2024 | gzip > backup_legislativo.sql.gz

# Formato personalizado (mais rápido para restaurar)
pg_dump -h localhost -U seu_usuario -d legislativo_2024 -F c -f backup_legislativo.dump
```

### **Importar (restore)**
```bash
# Na máquina de destino, crie o banco primeiro
createdb -U postgres legislativo_2024

# Restaurar de .sql
psql -h localhost -U seu_usuario -d legislativo_2024 -f backup_legislativo.sql

# Restaurar de .dump (mais rápido)
pg_restore -h localhost -U seu_usuario -d legislativo_2024 -v backup_legislativo.dump
```

### **Transferir entre máquinas**
```bash
# Exportar no servidor A
pg_dump -h localhost -U seu_usuario -d legislativo_2024 -F c -f backup_legislativo.dump

# Copiar para servidor B
scp backup_legislativo.dump usuario@servidor_b:/home/usuario/

# Importar no servidor B
pg_restore -h localhost -U seu_usuario -d legislativo_2024 -v backup_legislativo.dump
```

---

## 📐 **Estrutura do Banco**

A tabela `proposicoes_legislativas` possui:

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | SERIAL PK | Identificador único |
| `numero` | INTEGER | Número da proposição |
| `tipo` | VARCHAR(10) | PL, PEC ou MPV |
| `ano` | INTEGER | Ano da proposição |
| `data_apresentacao` | TIMESTAMP | Data e hora de apresentação |
| `ementa_resumo` | TEXT | Ementa completa |
| `artigo_1_trecho` | TEXT | Trecho inicial do Artigo 1º |
| `link_pdf` | TEXT | URL do PDF na Câmara |

**Restrição:** `UNIQUE(tipo, numero, ano)` evita duplicatas.

---

## 🔍 **Exemplos de Consultas**

### 1. Total de proposições por tipo
```sql
SELECT tipo, COUNT(*) as total
FROM proposicoes_legislativas
GROUP BY tipo
ORDER BY total DESC;
```

### 2. Proposições apresentadas em 2024
```sql
SELECT numero, tipo, data_apresentacao, ementa_resumo
FROM proposicoes_legislativas
WHERE ano = 2024
ORDER BY data_apresentacao DESC
LIMIT 10;
```

### 3. Buscar por palavra-chave na ementa
```sql
SELECT numero, tipo, ementa_resumo
FROM proposicoes_legislativas
WHERE ementa_resumo ILIKE '%cultura%'
ORDER BY tipo, numero;
```

### 4. Detalhes de uma proposição específica
```sql
SELECT * FROM proposicoes_legislativas
WHERE tipo = 'PL' AND numero = 4809 AND ano = 2024;
```

### 5. Proposições sobre crédito extraordinário (MPVs)
```sql
SELECT numero, ano, ementa_resumo
FROM proposicoes_legislativas
WHERE tipo = 'MPV' AND ementa_resumo ILIKE '%crédito extraordinário%'
ORDER BY numero DESC;
```

---

## 🖥️ **Acesso com pgAdmin**

Para gerenciar visualmente:

```bash
# Instale o pgAdmin (opcional)
sudo apt install pgadmin4-desktop

# Execute
pgadmin4
```

No pgAdmin, registre um novo servidor:
- **Host**: `localhost`
- **Port**: `5432`
- **Database**: `legislativo_2024`
- **Username**: `seu_usuario`
- **Password**: `sua_senha`

---

## 📄 **Arquivos do Projeto**

- `import_legislativo.py` - Script principal de coleta
- `setup_banco.sql` - Script de criação da tabela
- `requirements.txt` - Dependências Python
- `README.md` - Este arquivo

---

## 📝 **Notas**

- O script verifica duplicatas automaticamente via `ON CONFLICT DO NOTHING`
- A extração de PDFs é limitada à 1ª página para otimizar velocidade
- O `time.sleep(1.5)` evita sobrecarga na API da Câmara
- Certifique-se de que o PostgreSQL está rodando: `sudo systemctl status postgresql`

---

## 🤝 **Suporte**

Para problemas de conexão, verifique:
- Credenciais no script Python
- Firewall (porta 5432 aberta se conectar remotamente)
- Permissões do usuário no PostgreSQL

---

**Gerado a partir de backup do banco legis_ai** - Deploy pronto para produção.
