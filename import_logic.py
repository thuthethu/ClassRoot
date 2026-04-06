import pandas as pd
import sqlite3
import os
import re
import unicodedata
import io
import json
import openpyxl
from PIL import Image
from db import get_connection

def remover_acentos(txt):
    if not txt: return ""
    return unicodedata.normalize('NFKD', str(txt)).encode('ASCII', 'ignore').decode('utf-8').upper().strip()

def obter_abas_xlsx(file_path):
    try:
        xl = pd.ExcelFile(file_path)
        return xl.sheet_names
    except Exception:
        return []

def processar_xlsx_alunos(file_path, turma_id=None, nome_turma=None, ano_turma=2026, sheet_name=0):
    """
    Importa alunos de um Excel/CSV. Se turma_id for None, cria uma nova turma.
    """
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            # Força o motor openpyxl para ser pego pelo PyInstaller
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
        
        # Normalização de colunas
        cols_norm = {remover_acentos(c): c for c in df.columns}
        
        map_cols = {}
        for norm, orig in cols_norm.items():
            if norm in ['NOME', 'ALUNO', 'ESTUDANTE', 'NOME DO ALUNO']: map_cols[orig] = 'nome'
            if norm in ['MATRICULA', 'ID', 'RA', 'CODIGO']: map_cols[orig] = 'matricula'
            if norm in ['PCD', 'NEE', 'DEFICIENCIA', 'IS_NEE']: map_cols[orig] = 'pcd'
            if norm in ['TIPO_NEE', 'DIAGNOSTICO', 'TIPO']: map_cols[orig] = 'tipo_nee'
            if norm in ['CID']: map_cols[orig] = 'cid'
        
        df = df.rename(columns=map_cols)
        
        if 'nome' not in df.columns:
            return False, "Coluna 'Nome' não encontrada."

        conn = get_connection()
        cur = conn.cursor()

        # Cria turma se necessário
        if not turma_id:
            cur.execute("INSERT INTO turmas (nome, ano) VALUES (?, ?)", (nome_turma, ano_turma))
            turma_id = cur.lastrowid
        
        count = 0
        for _, row in df.iterrows():
            nome = str(row['nome']).strip()
            mat = str(row.get('matricula', ''))
            pcd = 1 if str(row.get('pcd', '')).lower() in ['sim', 'true', '1', 'x'] else 0
            tipo = str(row.get('tipo_nee', '')) if pd.notna(row.get('tipo_nee')) else ""
            cid = str(row.get('cid', '')) if pd.notna(row.get('cid')) else ""
            
            # Insere aluno
            cur.execute("INSERT INTO alunos (nome, observacoes, pcd, tipo_nee, cid) VALUES (?, ?, ?, ?, ?)",
                        (nome, f"Matricula original: {mat}", pcd, tipo, cid))
            aluno_id = cur.lastrowid
            
            # Matricula
            cur.execute("INSERT INTO matriculas (aluno_id, turma_id) VALUES (?, ?)", (aluno_id, turma_id))
            count += 1
            
        conn.commit()
        conn.close()
        return True, f"{count} alunos importados com sucesso."
    except Exception as e:
        return False, f"Erro na importação: {str(e)}"

