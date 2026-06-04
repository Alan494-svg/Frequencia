CREATE DATABASE frequencia_escolar;

USE frequencia_escolar;

CREATE TABLE alunos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    matricula VARCHAR(30) NOT NULL UNIQUE,
    turma VARCHAR(50) NOT NULL,
    email VARCHAR(100),
    telefone VARCHAR(20),
    foto_path VARCHAR(255),
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE presencas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    aluno_id INT NOT NULL,
    data_presenca DATE NOT NULL,
    hora_presenca TIME NOT NULL,
    FOREIGN KEY (aluno_id) REFERENCES alunos(id)
);

CREATE TABLE faltas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    aluno_id INT NOT NULL,
    data_falta DATE NOT NULL,
    FOREIGN KEY (aluno_id) REFERENCES alunos(id)
);