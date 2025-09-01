# app.py

import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# --- CONFIGURAÇÃO INICIAL ---
# Encontra o caminho absoluto do diretório do projeto
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__, template_folder='templates')
CORS(app) # Habilita o CORS para permitir requisições do front-end

# Configuração do Banco de Dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS DO BANCO DE DADOS ---
# Espelham as tabelas que definimos anteriormente, mas em formato de classes Python.

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    # Relacionamento: um usuário pode ter várias conversas
    conversations = db.relationship('Conversation', backref='user', lazy=True, cascade="all, delete-orphan")

    def as_dict(self):
        return {'id': self.id, 'username': self.username}

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False, default="Nova Conversa")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Relacionamento: uma conversa pode ter várias mensagens
    messages = db.relationship('Message', backref='conversation', lazy=True, cascade="all, delete-orphan")

    def as_dict(self):
        return {'id': self.id, 'title': self.title, 'user_id': self.user_id}

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    sender_type = db.Column(db.String(10), nullable=False) # 'user' ou 'bot'
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    
    def as_dict(self):
        return {'id': self.id, 'content': self.content, 'sender_type': self.sender_type}

# --- ROTA PARA SERVIR OS ARQUIVOS HTML ---
# Faz o Flask encontrar seus arquivos HTML na pasta 'templates'
@app.route('/')
def login():
    return render_template('login.html')

@app.route('/chat')
def chat():
    return render_template('layout.html')

# --- INÍCIO DAS ROTAS DA API ---
@app.route('/api/login', methods=['POST'])
def handle_login():
    data = request.json
    username = data.get('username')

    if not username:
        return jsonify({'error': 'Nome de usuário é obrigatório'}), 400

    # Procura se o usuário já existe
    user = User.query.filter_by(username=username).first()
    
    # Se não existir, cria um novo
    if not user:
        user = User(username=username)
        db.session.add(user)
        db.session.commit()
        
        # Cria a primeira conversa para o novo usuário
        first_convo = Conversation(title="Primeiros Passos", user_id=user.id)
        db.session.add(first_convo)
        db.session.commit()
        
        # Adiciona a primeira mensagem do bot
        first_message = Message(content=f"Olá {user.username}! Bem-vindo ao ChatBot. Como posso ajudar?", sender_type="bot", conversation_id=first_convo.id)
        db.session.add(first_message)
        db.session.commit()

    return jsonify(user.as_dict())

@app.route('/api/conversations/<int:user_id>', methods=['GET'])
def get_conversations(user_id):
    # Busca todas as conversas de um usuário específico
    convos = Conversation.query.filter_by(user_id=user_id).all()
    # Converte para uma lista de dicionários
    return jsonify([c.as_dict() for c in convos])

@app.route('/api/messages/<int:conversation_id>', methods=['GET'])
def get_messages(conversation_id):
    messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.id).all()
    return jsonify([m.as_dict() for m in messages])

@app.route('/api/messages', methods=['POST'])
def post_message():
    data = request.json
    user_message_content = data.get('content')
    conversation_id = data.get('conversation_id')

    # Salva a mensagem do usuário no banco
    user_message = Message(content=user_message_content, sender_type="user", conversation_id=conversation_id)
    db.session.add(user_message)
    db.session.commit()

    # =========================================================
    # AQUI VOCÊ CHAMA A LÓGICA DA IA DO SEU AMIGO
    # Por enquanto, vamos simular uma resposta simples
    # =========================================================
    # ia_response = seu_amigo_ia.gerar_resposta(user_message_content)
    ia_response = f"Obrigado por dizer '{user_message_content}'. Estou processando sua solicitação."
    
    # Salva a resposta do bot no banco
    bot_message = Message(content=ia_response, sender_type="bot", conversation_id=conversation_id)
    db.session.add(bot_message)
    db.session.commit()

    return jsonify(bot_message.as_dict())
# --- FIM DAS ROTAS DA API ---


# --- INICIALIZAÇÃO DO APP ---
if __name__ == '__main__':
    with app.app_context():
        # Cria as tabelas no banco de dados se elas não existirem
        db.create_all()
    app.run(debug=True)
