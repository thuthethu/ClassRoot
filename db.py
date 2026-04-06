import sqlite3
import os
import sys
from datetime import date, timedelta

# Localização do banco de dados
if getattr(sys, 'frozen', False):
    DB_PATH = os.path.join(os.path.dirname(sys.executable), "classroot.db")
else:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "classroot.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    
    # Schema idêntico ao PostgreSQL (adaptado para SQLite)
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS turmas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        ano INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS alunos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        observacoes TEXT,
        data_inicio DATE DEFAULT (DATE('now')),
        data_fim DATE,
        cid TEXT,
        pcd BOOLEAN DEFAULT 0,
        tipo_nee TEXT,
        necessita_adaptacao BOOLEAN DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS matriculas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER NOT NULL,
        turma_id INTEGER NOT NULL,
        data_inicio DATE DEFAULT (DATE('now')),
        data_fim DATE,
        FOREIGN KEY(aluno_id) REFERENCES alunos(id),
        FOREIGN KEY(turma_id) REFERENCES turmas(id)
    );

    CREATE TABLE IF NOT EXISTS aulas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        turma_id INTEGER NOT NULL,
        data DATE DEFAULT (DATE('now')),
        teve_dever BOOLEAN DEFAULT 0,
        descricao TEXT,
        observacoes_pos_aula TEXT,
        FOREIGN KEY(turma_id) REFERENCES turmas(id)
    );

    CREATE TABLE IF NOT EXISTS registros_aula (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aula_id INTEGER NOT NULL,
        aluno_id INTEGER NOT NULL,
        presente BOOLEAN DEFAULT 1,
        fez_atividade BOOLEAN DEFAULT 1,
        comportamento BOOLEAN DEFAULT 1,
        dever_passado_feito BOOLEAN DEFAULT 1,
        copiou_quadro BOOLEAN DEFAULT 1,
        bonus INTEGER DEFAULT 0,
        observacoes TEXT,
        FOREIGN KEY(aula_id) REFERENCES aulas(id),
        FOREIGN KEY(aluno_id) REFERENCES alunos(id)
    );
    """)
    conn.commit()
    conn.close()

# --- TRADUÇÃO DAS FUNÇÕES DO POSTGRES PARA PYTHON/SQLITE ---

def sql_trocar_turma(aluno_id, nova_turma_id, p_data_inicio=None):
    if p_data_inicio is None:
        p_data_inicio = date.today()
    else:
        p_data_inicio = date.fromisoformat(p_data_inicio) if isinstance(p_data_inicio, str) else p_data_inicio

    conn = get_connection()
    cur = conn.cursor()
    
    # 1. Busca a data de início da matrícula ativa
    cur.execute("SELECT data_inicio FROM matriculas WHERE aluno_id = ? AND data_fim IS NULL", (aluno_id,))
    row = cur.fetchone()
    v_data_inicio_atual = date.fromisoformat(row['data_inicio']) if row and row['data_inicio'] else None

    # 2. Se a matrícula atual começou no mesmo dia da troca, apenas atualizamos a turma
    if v_data_inicio_atual and v_data_inicio_atual == p_data_inicio:
        cur.execute("UPDATE matriculas SET turma_id = ? WHERE aluno_id = ? AND data_fim IS NULL", 
                    (nova_turma_id, aluno_id))
    else:
        # Caso comum: encerra a matrícula atual no dia anterior à nova matrícula
        v_data_fim = p_data_inicio - timedelta(days=1)
        cur.execute("UPDATE matriculas SET data_fim = ? WHERE aluno_id = ? AND data_fim IS NULL", 
                    (v_data_fim.isoformat(), aluno_id))

        # Insere a nova matrícula
        cur.execute("INSERT INTO matriculas (aluno_id, turma_id, data_inicio) VALUES (?, ?, ?)", 
                    (aluno_id, nova_turma_id, p_data_inicio.isoformat()))
    
    conn.commit()
    conn.close()

def sql_remover_aluno(aluno_id, p_data_fim=None):
    if p_data_fim is None:
        p_data_fim = date.today().isoformat()
    elif isinstance(p_data_fim, date):
        p_data_fim = p_data_fim.isoformat()

    conn = get_connection()
    cur = conn.cursor()
    
    # 1. encerra matrícula ativa
    cur.execute("UPDATE matriculas SET data_fim = ? WHERE aluno_id = ? AND data_fim IS NULL", 
                (p_data_fim, aluno_id))

    # 2. encerra aluno
    cur.execute("UPDATE alunos SET data_fim = ? WHERE id = ? AND data_fim IS NULL", 
                (p_data_fim, aluno_id))
    
    conn.commit()
    conn.close()
