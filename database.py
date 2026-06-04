import sqlite3

DATABASE = "frequencia.db"

def conectar():
    """Retorna uma conexão com o banco de dados SQLite com row_factory configurado."""
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row  # Permite acessar colunas pelo nome como um dicionário
    return conn

def criar_banco():
    """Cria as tabelas necessárias caso elas não existam."""
    conn = conectar()
    cursor = conn.cursor()

    # Tabela de alunos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alunos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        matricula TEXT UNIQUE,
        turma TEXT,
        email TEXT,
        telefone TEXT,
        foto_path TEXT
    )
    """)

    # Tabela de presenças
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS presencas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER,
        data_presenca DATE,
        hora_presenca TIME,
        FOREIGN KEY (aluno_id) REFERENCES alunos(id) ON DELETE CASCADE
    )
    """)

    # Tabela de faltas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS faltas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER,
        data_falta DATE,
        FOREIGN KEY (aluno_id) REFERENCES alunos(id) ON DELETE CASCADE
    )
    """)

    conn.commit()
    conn.close()