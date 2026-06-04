from flask import Flask, render_template, request, redirect, url_for, flash
import os
from werkzeug.utils import secure_filename
import database
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = "frequencia123"

UPLOAD_FOLDER = "static/fotos"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ======================================
# DASHBOARD
# ======================================

@app.route("/")
def dashboard():
    conn = database.conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) total FROM alunos")
    total_alunos = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) total FROM presencas")
    total_presencas = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) total FROM faltas")
    total_faltas = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        total_alunos=total_alunos,
        total_presencas=total_presencas,
        total_faltas=total_faltas
    )

# ======================================
# LISTAR ALUNOS
# ======================================

@app.route("/alunos")
def alunos():
    conn = database.conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM alunos
        ORDER BY nome
    """)

    alunos = cursor.fetchall()
    conn.close()

    return render_template(
        "alunos.html",
        alunos=alunos
    )

# ======================================
# CADASTRAR ALUNO
# ======================================

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():

    if request.method == "POST":

        nome = request.form["nome"]
        # Gerar matrícula automaticamente
        matricula = f"MAT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        turma = None # Turma não será mais informada no cadastro
        email = request.form["email"]
        telefone = request.form["telefone"]

        foto = request.files["foto"]

        foto_path = ""

        if foto:
            filename = secure_filename(foto.filename)

            foto_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )

            foto.save(foto_path)

        conn = database.conectar()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO alunos
            (
                nome,
                matricula,
                turma,
                email,
                telefone,
                foto_path
            )
            VALUES (?,?,?,?,?,?)
        """, (
            nome,
            matricula,
            turma,
            email,
            telefone,
            foto_path
        ))

        conn.commit()
        conn.close()

        flash("Aluno cadastrado com sucesso!")

        return redirect(url_for("alunos"))

    return render_template("cadastro.html")

# ======================================
# DELETAR ALUNO
# ======================================

@app.route("/deletar_aluno/<int:id>")
def deletar_aluno(id):
    conn = database.conectar()
    cursor = conn.cursor()

    # Buscar caminho da foto para remover o arquivo físico
    cursor.execute("SELECT foto_path FROM alunos WHERE id=?", (id,))
    aluno = cursor.fetchone()

    if aluno and aluno["foto_path"] and os.path.exists(aluno["foto_path"]):
        try:
            os.remove(aluno["foto_path"])
        except Exception as e:
            print(f"Erro ao remover arquivo: {e}")

    cursor.execute("DELETE FROM alunos WHERE id=?", (id,))
    conn.commit()
    conn.close()

    flash("Aluno removido com sucesso!")
    return redirect(url_for("alunos"))

# ======================================
# PERFIL ALUNO
# ======================================

@app.route("/aluno/<int:id>")
def aluno(id):
    conn = database.conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM alunos WHERE id=?",
        (id,)
    )

    aluno = cursor.fetchone()

    cursor.execute("""
        SELECT *
        FROM presencas
        WHERE aluno_id=?
        ORDER BY data_presenca DESC
    """, (id,))

    presencas = cursor.fetchall()

    cursor.execute("""
        SELECT *
        FROM faltas
        WHERE aluno_id=?
        ORDER BY data_falta DESC
    """, (id,))

    faltas = cursor.fetchall()

    total_faltas = len(faltas)

    if total_faltas >= 7:
        status = "EXCEDEU LIMITE DE FALTAS"
    elif total_faltas >= 5:
        status = "EM ALERTA"
    else:
        status = "REGULAR"

    conn.close()

    return render_template(
        "aluno.html",
        aluno=aluno,
        presencas=presencas,
        faltas=faltas,
        total_faltas=total_faltas,
        status=status
    )

# ======================================
# FECHAR CHAMADA
# ======================================

@app.route("/fechar_chamada")
def fechar_chamada():
    conn = database.conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM alunos")

    alunos = cursor.fetchall()

    from datetime import date

    hoje = date.today()

    for aluno in alunos:

        cursor.execute("""
            SELECT *
            FROM presencas
            WHERE aluno_id=?
            AND data_presenca=?
        """, (
            aluno["id"],
            str(hoje)
        ))

        presente = cursor.fetchone()

        # Verifica se já existe uma falta registrada para hoje
        cursor.execute("""
            SELECT *
            FROM faltas
            WHERE aluno_id=?
            AND data_falta=?
        """, (
            aluno["id"],
            str(hoje)
        ))
        falta_existente = cursor.fetchone()

        if not presente and not falta_existente:

            cursor.execute("""
                INSERT INTO faltas
                (
                    aluno_id,
                    data_falta
                )
                VALUES (?,?)
            """, (
                aluno["id"],
                str(hoje)
            ))

    conn.commit()
    conn.close()

    flash("Chamada encerrada!")

    return redirect(url_for("dashboard"))

# ======================================
# EXECUÇÃO
# ======================================

if __name__ == "__main__":
    database.criar_banco()

    os.makedirs(
        "static/fotos",
        exist_ok=True
    )

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )