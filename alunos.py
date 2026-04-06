from datetime import date
from db import get_connection, sql_remover_aluno, sql_trocar_turma

def remover_aluno(aluno_id, data_fim=None):
    sql_remover_aluno(aluno_id, data_fim)

def trocar_turma(aluno_id, nova_turma_id, data_inicio=None):
    sql_trocar_turma(aluno_id, nova_turma_id, data_inicio)
