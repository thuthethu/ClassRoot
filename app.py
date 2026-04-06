import os
import sys
import json
import re
import webbrowser
from threading import Timer
from flask import Flask, request, redirect, url_for, render_template, abort, flash, send_from_directory
from db import get_connection, init_db
from alunos import remover_aluno, trocar_turma
from import_logic import processar_xlsx_alunos

# Configuração de caminhos para portabilidade (Windows EXE)
if getattr(sys, 'frozen', False):
    # Se for executável, a raiz é a pasta onde o .exe está localizado
    BASE_DIR = os.path.dirname(sys.executable)
    # Mas templates e static internos ficam no bundle temporário (_MEIPASS)
    # Isso garante que CSS/JS do sistema funcionem sem pastas externas
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    static_folder = os.path.join(sys._MEIPASS, 'static')
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    app = Flask(__name__)

app.secret_key = "secret_key_diario"

# Pastas Externas Persistentes (fora do .exe - Onde ficam as fotos e PDFs)
PASTA_FOTOS = os.path.join(BASE_DIR, "static", "fotos_alunos")
PASTA_PDFS = os.path.join(BASE_DIR, "static", "relatorios_nee")
os.makedirs(PASTA_FOTOS, exist_ok=True)
os.makedirs(PASTA_PDFS, exist_ok=True)

# Rotas customizadas para servir arquivos externos e persistentes
@app.route('/static/fotos_alunos/<path:filename>')
def serve_fotos_externas(filename):
    return send_from_directory(PASTA_FOTOS, filename)

@app.route('/static/relatorios_nee/<path:filename>')
def serve_pdfs_externos(filename):
    return send_from_directory(PASTA_PDFS, filename)

# Inicializa o banco se não existir
init_db()

# ===============================
# LISTAR TURMAS
# ===============================
@app.route("/")
def listar_turmas():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, nome, ano
        FROM turmas
        ORDER BY ano DESC, nome;
    """)
    turmas = [dict(row) for row in cur.fetchall()]
    conn.close()
    return render_template("turmas.html", turmas=turmas)

# ===============================
# FORMULÁRIO NOVA AULA
# ===============================
@app.route("/form_aula/<int:turma_id>")
def form_aula(turma_id):
    return render_template("form_aula.html", turma_id=turma_id)

# ===============================
# CRIAR AULA
# ===============================
@app.route("/nova_aula/<int:turma_id>", methods=["POST"])
def nova_aula(turma_id):
    data_aula = request.form.get("data")
    descricao = request.form.get("descricao", "")
    teve_dever = 1 if "teve_dever" in request.form else 0

    if not data_aula:
        abort(400, "Data é obrigatória.")

    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO aulas (turma_id, data, teve_dever, descricao)
        VALUES (?, ?, ?, ?)
    """, (turma_id, data_aula, teve_dever, descricao))
    aula_id = cur.lastrowid

    cur.execute("""
        INSERT INTO registros_aula (
            aula_id, aluno_id, presente, fez_atividade,
            comportamento, dever_passado_feito, copiou_quadro, bonus
        )
        SELECT ?, a.id, 1, 1, 1, 1, 1, 0
        FROM alunos a
        JOIN matriculas m ON m.aluno_id = a.id
        WHERE m.turma_id = ? AND m.data_fim IS NULL;
    """, (aula_id, turma_id))
    
    conn.commit()
    conn.close()

    return redirect(url_for("visualizar_aula", aula_id=aula_id))

# ===============================
# LISTAR AULAS
# ===============================
@app.route("/aulas")
def listar_aulas():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.id,
                t.nome AS turma,
                a.data,
                a.descricao
        FROM aulas a
        JOIN turmas t ON t.id = a.turma_id
        ORDER BY a.data DESC, a.id DESC;
    """)
    aulas = [dict(row) for row in cur.fetchall()]
    conn.close()
    return render_template("aulas.html", aulas=aulas)

# ===============================
# VISUALIZAR / EDITAR AULA
# ===============================
@app.route("/aula/<int:aula_id>", methods=["GET", "POST"])
def visualizar_aula(aula_id):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT id, data, descricao, observacoes_pos_aula FROM aulas WHERE id = ?;", (aula_id,))
    aula = cur.fetchone()
    if not aula:
        conn.close()
        abort(404)

    if request.method == "POST":
        observacoes_aula = request.form.get("observacoes_pos_aula", "")
        cur.execute("UPDATE aulas SET observacoes_pos_aula = ? WHERE id = ?;", (observacoes_aula, aula_id))

        cur.execute("SELECT id FROM registros_aula WHERE aula_id = ?;", (aula_id,))
        registros_ids = [r["id"] for r in cur.fetchall()]

        for registro_id in registros_ids:
            presente = 1 if f"presente_{registro_id}" in request.form else 0
            
            # Se não estiver presente, desmarca tudo automaticamente (Lógica solicitada)
            if presente == 0:
                fez_atividade = 0
                comportamento = 0
                dever = 0
                copiou = 0
                bonus = 0
            else:
                fez_atividade = 1 if f"atividade_{registro_id}" in request.form else 0
                comportamento = 1 if f"comportamento_{registro_id}" in request.form else 0
                dever = 1 if f"dever_{registro_id}" in request.form else 0
                copiou = 1 if f"copiou_{registro_id}" in request.form else 0
                bonus = 1 if f"bonus_{registro_id}" in request.form else 0
            
            observacao_aluno = request.form.get(f"obs_{registro_id}", "")

            cur.execute("""
                UPDATE registros_aula
                SET presente = ?, fez_atividade = ?, comportamento = ?,
                    dever_passado_feito = ?, copiou_quadro = ?,
                    observacoes = ?, bonus = ?
                WHERE id = ?;
            """, (presente, fez_atividade, comportamento, dever, copiou, observacao_aluno, bonus, registro_id))
        
        conn.commit()

    cur.execute("""
        SELECT r.id, a.nome AS aluno, r.presente, r.fez_atividade,
               r.comportamento, r.dever_passado_feito,
               r.copiou_quadro, r.observacoes, r.bonus,
               a.pcd, a.tipo_nee
        FROM registros_aula r
        JOIN alunos a ON a.id = r.aluno_id
        WHERE r.aula_id = ?
        ORDER BY a.nome;
    """, (aula_id,))
    registros = [dict(row) for row in cur.fetchall()]
    conn.close()

    # Lógica de Carômetro
    import unicodedata
    mapa_fotos = {}
    caminho_mapa = os.path.join(BASE_DIR, "mapa_fotos.json")
    print(f"DEBUG: Procurando mapa em {caminho_mapa}")
    if os.path.exists(caminho_mapa):
        print("DEBUG: Mapa encontrado!")
        with open(caminho_mapa, "r", encoding="utf-8") as f:
            mapa_fotos = json.load(f)
            print(f"DEBUG: Mapa carregado com {len(mapa_fotos)} chaves.")
    else:
        print("DEBUG: Mapa NAO encontrado!")

    def remover_acentos(txt):
        return unicodedata.normalize('NFKD', txt).encode('ASCII', 'ignore').decode('utf-8').upper()

    def normalize_tokens(name):
        n = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8').upper()
        n = re.sub(r'^[0-9]+-?', '', n) # Remove prefixos numéricos (1-, 22-)
        n = re.sub(r'[^A-Z ]', ' ', n)  # Mantém apenas letras e espaços
        # Filtra preposições comuns e tokens vazios
        irrelevant = {'DE', 'DA', 'DO', 'DOS', 'DAS', 'E'}
        return [t for t in n.split() if t not in irrelevant and len(t) >= 2]

    for r in registros:
        r['foto'] = None
        tokens_db = normalize_tokens(r['aluno'])
        if not tokens_db: continue
        
        best_score = 0
        best_foto = None
        
        for key_nome, file_foto in mapa_fotos.items():
            tokens_key = normalize_tokens(key_nome)
            if not tokens_key: continue
            
            matches = 0
            for tk in tokens_key:
                for td in tokens_db:
                    # Match se um token começa com o outro (abreviações) ou são iguais
                    if td.startswith(tk) or tk.startswith(td):
                        matches += 1
                        break
            
            # Score = (Número de matches) / (Média do tamanho das listas de tokens)
            score = matches / max(len(tokens_key), 1)
            
            # Bonus se o primeiro nome (token) bater exatamente
            if tokens_key[0] == tokens_db[0]:
                score += 0.1
                
            if score > best_score:
                best_score = score
                best_foto = file_foto
        
        # Threshold de confiança de 0.6 (60% de similaridade + bônus)
        if best_score >= 0.7:
            r['foto'] = best_foto

    return render_template(
        "aula.html",
        aula_id=aula_id,
        registros=registros,
        observacoes_aula=aula["observacoes_pos_aula"] or ""
    )

# ===============================
# EXCLUIR AULA
# ===============================
@app.route("/excluir_aula/<int:aula_id>", methods=["POST"])
def excluir_aula(aula_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM aulas WHERE id = ?;", (aula_id,))
    cur.execute("DELETE FROM registros_aula WHERE aula_id = ?;", (aula_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("listar_aulas"))

# ===============================
# EXCLUIR TURMA
# ===============================
@app.route("/confirmar_exclusao_turma/<int:turma_id>")
def confirmar_exclusao_turma(turma_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT nome FROM turmas WHERE id = ?", (turma_id,))
    turma = cur.fetchone()
    conn.close()
    
    if not turma: abort(404)
    
    return render_template(
        "confirmar.html",
        mensagem=f"Deseja excluir a turma '{turma['nome']}'? Isso apagará TODAS as aulas e frequências desta turma!",
        acao_url=url_for("excluir_turma_rota", turma_id=turma_id),
        voltar_url=url_for("listar_turmas")
    )

@app.route("/excluir_turma/<int:turma_id>", methods=["POST"])
def excluir_turma_rota(turma_id):
    conn = get_connection()
    cur = conn.cursor()
    
    # Busca IDs das aulas para limpar registros_aula
    cur.execute("SELECT id FROM aulas WHERE turma_id = ?", (turma_id,))
    aula_ids = [r[0] for r in cur.fetchall()]
    
    for aid in aula_ids:
        cur.execute("DELETE FROM registros_aula WHERE aula_id = ?", (aid,))
    
    cur.execute("DELETE FROM aulas WHERE turma_id = ?", (turma_id,))
    cur.execute("DELETE FROM matriculas WHERE turma_id = ?", (turma_id,))
    cur.execute("DELETE FROM turmas WHERE id = ?", (turma_id,))
    
    conn.commit()
    conn.close()
    flash("Turma excluída com sucesso.")
    return redirect(url_for("listar_turmas"))

# ===============================
# CONFIRMAÇÃO GENÉRICA
# ===============================
@app.route("/confirmar_exclusao/<int:aula_id>")
def confirmar_exclusao(aula_id):
    return render_template(
        "confirmar.html",
        mensagem="Deseja excluir esta aula?",
        acao_url=url_for("excluir_aula", aula_id=aula_id),
        voltar_url=url_for("visualizar_aula", aula_id=aula_id)
    )

# ===============================
# GERENCIAR MATRÍCULAS
# ===============================
@app.route("/alunos_turma/<int:turma_id>", methods=["GET", "POST"])
def alunos_turma(turma_id):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT nome FROM turmas WHERE id = ?", (turma_id,))
    turma_row = cur.fetchone()
    turma_nome = turma_row['nome'] if turma_row else "Turma"

    cur.execute("""
        SELECT a.id, a.nome, a.pcd, a.tipo_nee, a.cid
        FROM alunos a
        JOIN matriculas m ON m.aluno_id = a.id
        WHERE m.turma_id = ? AND m.data_fim IS NULL
        ORDER BY a.nome
    """, (turma_id,))
    matriculados = [dict(row) for row in cur.fetchall()]

    cur.execute("""
        SELECT id, nome
        FROM alunos
        WHERE id NOT IN (
            SELECT aluno_id FROM matriculas WHERE turma_id = ? AND data_fim IS NULL
        )
        ORDER BY nome
    """, (turma_id,))
    disponiveis = [dict(row) for row in cur.fetchall()]

    cur.execute("SELECT id, nome || ' (' || ano || ')' AS descricao FROM turmas WHERE id != ? ORDER BY ano DESC, nome", (turma_id,))
    outras_turmas = [dict(row) for row in cur.fetchall()]
    conn.close()

    return render_template(
        "alunos_turma.html",
        turma_id=turma_id,
        turma_nome=turma_nome,
        matriculados=matriculados,
        disponiveis=disponiveis,
        outras_turmas=outras_turmas
    )

@app.route("/adicionar_aluno/<int:turma_id>", methods=["POST"])
def adicionar_aluno(turma_id):
    aluno_id = request.form.get("aluno_id")
    if not aluno_id: abort(400)
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO matriculas (aluno_id, turma_id) VALUES (?, ?)", (aluno_id, turma_id))
    conn.commit()
    conn.close()
    return redirect(url_for("alunos_turma", turma_id=turma_id))

@app.route("/novo_aluno/<int:turma_id>", methods=["POST"])
def novo_aluno(turma_id):
    nome = request.form.get("nome")
    if not nome: abort(400)
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO alunos (nome, pcd, tipo_nee, cid) VALUES (?, ?, ?, ?)", 
                (nome, 1 if "pcd" in request.form else 0, request.form.get("tipo_nee", ""), request.form.get("cid", "")))
    aluno_id = cur.lastrowid
    cur.execute("INSERT INTO matriculas (aluno_id, turma_id) VALUES (?, ?)", (aluno_id, turma_id))
    conn.commit()
    conn.close()
    return redirect(url_for("alunos_turma", turma_id=turma_id))

@app.route("/remover_aluno/<int:turma_id>/<int:aluno_id>", methods=["POST"])
def remover_aluno_rota(turma_id, aluno_id):
    remover_aluno(aluno_id)
    return redirect(url_for("alunos_turma", turma_id=turma_id))

@app.route("/trocar_turma/<int:turma_id>/<int:aluno_id>", methods=["POST"])
def trocar_turma_rota(turma_id, aluno_id):
    nova_turma_id = request.form.get("nova_turma_id")
    if nova_turma_id and nova_turma_id != "manter":
        trocar_turma(aluno_id, nova_turma_id)
    return redirect(url_for("alunos_turma", turma_id=turma_id))

# ===============================
# GESTÃO NEE
# ===============================
@app.route("/nee/<int:turma_id>")
def gerenciar_nee(turma_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nome FROM turmas WHERE id = ?", (turma_id,))
    turma = cur.fetchone()
    
    cur.execute("""
        SELECT a.id, a.nome, a.pcd, a.tipo_nee, a.cid
        FROM alunos a
        JOIN matriculas m ON m.aluno_id = a.id
        WHERE m.turma_id = ? AND m.data_fim IS NULL
        ORDER BY a.nome
    """, (turma_id,))
    alunos = [dict(row) for row in cur.fetchall()]
    conn.close()

    for a in alunos:
        pdf_path = os.path.join(PASTA_PDFS, f"{a['id']}.pdf")
        a['tem_pdf'] = os.path.exists(pdf_path)

    return render_template("nee.html", turma=turma, alunos=alunos)

@app.route("/nee/<int:turma_id>/salvar", methods=["POST"])
def salvar_nee(turma_id):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT a.id FROM alunos a JOIN matriculas m ON m.aluno_id = a.id WHERE m.turma_id = ? AND m.data_fim IS NULL", (turma_id,))
    ids = [r[0] for r in cur.fetchall()]

    for aid in ids:
        if f"aluno_id_{aid}" in request.form:
            pcd = 1 if f"pcd_{aid}" in request.form else 0
            cur.execute("UPDATE alunos SET pcd = ?, tipo_nee = ?, cid = ?, necessita_adaptacao = ? WHERE id = ?",
                        (pcd, request.form.get(f"tipo_nee_{aid}", ""), request.form.get(f"cid_{aid}", ""), pcd, aid))
            
            f = request.files.get(f"pdf_{aid}")
            if f and f.filename.endswith('.pdf'):
                f.save(os.path.join(PASTA_PDFS, f"{aid}.pdf"))
    
    conn.commit()
    conn.close()
    return redirect(url_for('listar_turmas'))

# ===============================
# NOVAS ROTAS: IMPORTAÇÃO
# ===============================
@app.route("/importar", methods=["GET", "POST"])
def view_importar():
    conn = get_connection()
    cur = conn.cursor()
    
    if request.method == "POST":
        # PASSO 2: Seleção de Abas confirmada
        if "confirmar_importacao_abas" in request.form:
            temp_name = request.form.get("temp_file")
            abas_selecionadas = request.form.getlist("abas_selecionadas")
            temp_path = os.path.join(BASE_DIR, temp_name)
            
            if not abas_selecionadas:
                flash("Nenhuma aba selecionada.")
            else:
                for aba in abas_selecionadas:
                    ok, msg = processar_xlsx_alunos(temp_path, nome_turma=aba, sheet_name=aba)
                    flash(f"Aba {aba}: {msg}")
                
                try:
                    os.remove(temp_path)
                except:
                    pass
                return redirect(url_for("listar_turmas"))

        # PASSO 1: Upload de arquivo
        if "xlsx" in request.files:
            file = request.files["xlsx"]
            if file.filename != "":
                temp_name = "temp_import.xlsx"
                temp_path = os.path.join(BASE_DIR, temp_name)
                file.save(temp_path)
                
                from import_logic import obter_abas_xlsx
                abas = obter_abas_xlsx(temp_path)
                
                if len(abas) > 1:
                    # Retorna com a lista de abas para o usuário escolher
                    cur.execute("SELECT id, nome, ano FROM turmas ORDER BY ano DESC, nome")
                    turmas = [dict(row) for row in cur.fetchall()]
                    conn.close()
                    return render_template("importar.html", turmas=turmas, abas_detectadas=abas, temp_file=temp_name)
                else:
                    # Importa a única aba (ou a primeira)
                    ok, msg = processar_xlsx_alunos(temp_path, nome_turma=request.form.get("nome_turma") or abas[0])
                    flash(msg)
                    try:
                        os.remove(temp_path)
                    except:
                        pass
        
        # PASSO 3: Upload de Múltiplas Imagens (Arquivos Soltos)
        if "fotos_avulsas" in request.files:
            files = request.files.getlist("fotos_avulsas")
            if files and files[0].filename != "":
                try:
                    caminho_mapa = os.path.join(BASE_DIR, "mapa_fotos.json")
                    mapa = {}
                    if os.path.exists(caminho_mapa):
                        with open(caminho_mapa, "r", encoding="utf-8") as f:
                            mapa = json.load(f)
                    
                    import unicodedata, re
                    from import_logic import remover_acentos
                    
                    os.makedirs(PASTA_FOTOS, exist_ok=True)
                    
                    count = 0
                    for f in files:
                        if f.filename:
                            # Pega o nome do arquivo sem a extensão
                            nome_original = os.path.splitext(f.filename)[0]
                            nome_slug = re.sub(r'[^a-z0-9]', '_', remover_acentos(nome_original).lower())
                            ext = os.path.splitext(f.filename)[1].lower()
                            # Normaliza .jpeg para .jpg para padronização interna
                            if ext == ".jpeg": ext = ".jpg"
                            fname = f"{nome_slug}{ext}"
                            
                            f.save(os.path.join(PASTA_FOTOS, fname))
                            mapa[nome_original] = fname
                            count += 1
                    
                    with open(caminho_mapa, "w", encoding="utf-8") as fw:
                        json.dump(mapa, fw, indent=4)
                        
                    flash(f"{count} fotos enviadas e vinculadas aos respectivos nomes!")
                except Exception as e:
                    flash(f"Erro ao salvar fotos: {str(e)}")

        return redirect(url_for("view_importar"))
    
    cur.execute("SELECT id, nome, ano FROM turmas ORDER BY ano DESC, nome")
    turmas = [dict(row) for row in cur.fetchall()]
    conn.close()
    
    return render_template("importar.html", turmas=turmas)

# ===============================
# INICIALIZAÇÃO E WRAPPER
# ===============================
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == "__main__":
    if not os.environ.get("FLASK_RUN_FROM_CLI"):
        Timer(1.5, open_browser).start()
    app.run(port=5000)
