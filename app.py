from flask import Flask, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from datetime import datetime, timedelta
import jwt
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reclamacoes.db'
app.config['SECRET_KEY'] = 'seu_segredo_aqui'
db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True)
    senha_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_password(self, senha):
        return check_password_hash(self.senha_hash, senha)

class Reclamacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    data_de_criacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = request.headers.get('x-access-token')

        if not token:
            return jsonify({'message': 'Token de acesso necessário!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            usuario_atual = Usuario.query.get(data['id'])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expirado! Faça login novamente.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token inválido!'}), 401

        return f(usuario_atual, *args, **kwargs)

    return decorator

@app.route('/login', methods=['POST'])
def login():
    dados_autenticacao = request.json

    if not dados_autenticacao or 'nome' not in dados_autenticacao or 'senha' not in dados_autenticacao:
        abort(400) 

    nome = dados_autenticacao['nome']
    senha = dados_autenticacao['senha']

    usuario = Usuario.query.filter_by(nome=nome).first()

    if not usuario or not usuario.check_password(senha):
        return jsonify({'message': 'Falha na autenticação! Nome de usuário ou senha incorretos.'}), 401

    token = jwt.encode({'id': usuario.id, 'exp': datetime.utcnow() + timedelta(hours=24)}, app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({'token': token.decode('utf-8')})

@app.route('/reclamacoes', methods=['POST'])
@token_required
def criar_reclamacao(usuario_atual):
    dados_reclamacao = request.json
    if not dados_reclamacao or 'titulo' not in dados_reclamacao or 'descricao' not in dados_reclamacao:
        abort(400) 

    nova_reclamacao = Reclamacao(titulo=dados_reclamacao['titulo'], descricao=dados_reclamacao['descricao'], usuario_id=usuario_atual.id)
    db.session.add(nova_reclamacao)
    db.session.commit()
    return jsonify({'message': 'Reclamação criada com sucesso!'}), 201

@app.route('/reclamacoes', methods=['GET'])
@token_required
def listar_reclamacoes(usuario_atual):
    reclamacoes = Reclamacao.query.filter_by(usuario_id=usuario_atual.id).all()
    return jsonify([{'id': reclamacao.id, 'titulo': reclamacao.titulo, 'descricao': reclamacao.descricao} for reclamacao in reclamacoes]), 200

@app.route('/reclamacoes/<int:id>', methods=['PUT'])
@token_required
def atualizar_reclamacao(usuario_atual, id):
    reclamacao = Reclamacao.query.get(id)
    if not reclamacao:
        return jsonify({'message': 'Reclamação não encontrada!'}), 404

    dados_atualizacao = request.json
    if not dados_atualizacao or ('titulo' not in dados_atualizacao and 'descricao' not in dados_atualizacao):
        return jsonify({'message': 'Nenhum campo para atualizar!'}), 400

    if reclamacao.usuario_id != usuario_atual.id:
        return jsonify({'message': 'Você não tem permissão para atualizar esta reclamação!'}), 403

    if 'titulo' in dados_atualizacao:
        reclamacao.titulo = dados_atualizacao['titulo']
    if 'descricao' in dados_atualizacao:
        reclamacao.descricao = dados_atualizacao['descricao']

    db.session.commit()
    return jsonify({'message': 'Reclamação atualizada com sucesso!'}), 200

@app.route('/reclamacoes/<int:id>', methods=['DELETE'])
@token_required
def deletar_reclamacao(usuario_atual, id):
    reclamacao = Reclamacao.query.get(id)
    if not reclamacao:
        return jsonify({'message': 'Reclamação não encontrada!'}), 404

    if reclamacao.usuario_id != usuario_atual.id:
        return jsonify({'message': 'Você não tem permissão para excluir esta reclamação!'}), 403

    db.session.delete(reclamacao)
    db.session.commit()
    return jsonify({'message': 'Reclamação excluída com sucesso!'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=443, ssl_context='adhoc')
