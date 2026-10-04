"""
Backend Flask - Application Médicale de Détection des Maladies
Sécurité : blocage 24h après 3 tentatives + email d'alerte
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta, datetime
import json
import os
import uuid
from model import predict_disease

app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.config['JWT_SECRET_KEY'] = 'medical-secret-key-change-in-production-2024'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# ===== CONFIGURATION EMAIL =====
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'votre_email@gmail.com'       # ← changer
app.config['MAIL_PASSWORD'] = 'votre_mot_de_passe_app'      # ← changer
app.config['MAIL_DEFAULT_SENDER'] = 'votre_email@gmail.com' # ← changer

CORS(app)
jwt = JWTManager(app)
mail = Mail(app)

# ===== RATE LIMITER =====
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# ===== BASE DE DONNÉES =====
USERS_FILE = 'users.json'
HISTORY_FILE = 'history.json'
ATTEMPTS_FILE = 'attempts.json'

def load_json(filename):
    if not os.path.exists(filename):
        return {}
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ===== FONCTIONS SÉCURITÉ =====

def get_attempts(username):
    attempts = load_json(ATTEMPTS_FILE)
    return attempts.get(username, {'count': 0, 'locked_until': None})

def save_attempts(username, data):
    attempts = load_json(ATTEMPTS_FILE)
    attempts[username] = data
    save_json(ATTEMPTS_FILE, attempts)

def reset_attempts(username):
    attempts = load_json(ATTEMPTS_FILE)
    if username in attempts:
        del attempts[username]
        save_json(ATTEMPTS_FILE, attempts)

def is_account_locked(username):
    data = get_attempts(username)
    if data.get('locked_until'):
        locked_until = datetime.fromisoformat(data['locked_until'])
        if datetime.now() < locked_until:
            remaining = locked_until - datetime.now()
            hours = int(remaining.total_seconds() // 3600)
            minutes = int((remaining.total_seconds() % 3600) // 60)
            return True, hours, minutes
        else:
            reset_attempts(username)
    return False, 0, 0

def send_alert_email(user_email, username, ip_address):
    try:
        now = datetime.now().strftime('%d/%m/%Y à %H:%M:%S')
        msg = Message(
            subject='⚠️ Alerte Sécurité MédiDiag - Tentative de connexion suspecte',
            recipients=[user_email]
        )
        msg.html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#0d9488;padding:20px;border-radius:10px;text-align:center;">
                <h1 style="color:white;margin:0;">🏥 MédiDiag - Alerte Sécurité</h1>
            </div>
            <div style="background:#fff3cd;border:1px solid #ffc107;border-radius:8px;padding:16px;margin:20px 0;">
                <h2 style="color:#856404;">⚠️ 3 tentatives de connexion échouées détectées !</h2>
            </div>
            <div style="background:white;border-radius:8px;padding:20px;border:1px solid #e9ecef;">
                <p><strong>👤 Compte :</strong> {username}</p>
                <p><strong>📅 Date :</strong> {now}</p>
                <p><strong>🌐 Adresse IP :</strong> {ip_address}</p>
                <p><strong>🔒 Statut :</strong> <span style="color:red;">Bloqué 24 heures</span></p>
            </div>
            <div style="background:#f8d7da;border-radius:8px;padding:16px;margin:20px 0;">
                <p style="color:#721c24;">Si ce n'était pas vous, votre compte est en sécurité car il est bloqué. Contactez l'administrateur.</p>
            </div>
        </div>
        """
        mail.send(msg)
        print(f"✅ Email d'alerte envoyé à {user_email}")
    except Exception as e:
        print(f"⚠️ Erreur envoi email : {e}")


# ===== ROUTES FRONTEND =====
@app.route('/')
def index():
    return send_from_directory('../frontend', 'login.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)


# ===== AUTH ROUTES =====
@app.route('/api/register', methods=['POST'])
@limiter.limit("10 per hour")
def register():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    email = data.get('email', '').strip()
    full_name = data.get('full_name', '').strip()

    if not username or not password or not email:
        return jsonify({'error': 'Champs obligatoires manquants'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Mot de passe trop court (min 6 caractères)'}), 400

    users = load_json(USERS_FILE)
    if username in users:
        return jsonify({'error': "Nom d'utilisateur déjà pris"}), 409
    for u in users.values():
        if u.get('email') == email:
            return jsonify({'error': 'Email déjà utilisé'}), 409

    users[username] = {
        'id': str(uuid.uuid4()),
        'username': username,
        'email': email,
        'full_name': full_name,
        'password': generate_password_hash(password),
        'language': 'fr'
    }
    save_json(USERS_FILE, users)
    token = create_access_token(identity=username)
    return jsonify({
        'message': 'Compte créé avec succès',
        'token': token,
        'user': {'username': username, 'email': email, 'full_name': full_name}
    }), 201


@app.route('/api/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    ip = request.remote_addr

    users = load_json(USERS_FILE)
    user = users.get(username)

    if not user:
        return jsonify({'error': 'Identifiants incorrects'}), 401

    # Vérifier si compte bloqué
    locked, hours, minutes = is_account_locked(username)
    if locked:
        return jsonify({
            'error': f'🔒 Compte bloqué encore {hours}h {minutes}min. Vérifiez votre email.'
        }), 403

    # Vérifier mot de passe
    if not check_password_hash(user['password'], password):
        attempt_data = get_attempts(username)
        attempt_data['count'] = attempt_data.get('count', 0) + 1
        attempt_data['last_attempt'] = datetime.now().isoformat()
        remaining = 3 - attempt_data['count']

        if attempt_data['count'] >= 3:
            # Bloquer 24h
            locked_until = datetime.now() + timedelta(hours=24)
            attempt_data['locked_until'] = locked_until.isoformat()
            save_attempts(username, attempt_data)
            # Envoyer email
            if user.get('email'):
                send_alert_email(user['email'], username, ip)
            return jsonify({
                'error': '🔒 Compte bloqué 24h ! Un email d\'alerte a été envoyé.'
            }), 403
        else:
            save_attempts(username, attempt_data)
            return jsonify({
                'error': f'❌ Mot de passe incorrect. {remaining} tentative(s) restante(s).'
            }), 401

    # Connexion réussie
    reset_attempts(username)
    token = create_access_token(identity=username)
    return jsonify({
        'token': token,
        'user': {
            'username': user['username'],
            'email': user['email'],
            'full_name': user.get('full_name', ''),
            'language': user.get('language', 'fr')
        }
    })


@app.route('/api/profile', methods=['GET'])
@jwt_required()
def get_profile():
    username = get_jwt_identity()
    users = load_json(USERS_FILE)
    user = users.get(username)
    if not user:
        return jsonify({'error': 'Utilisateur non trouvé'}), 404
    return jsonify({
        'username': user['username'],
        'email': user['email'],
        'full_name': user.get('full_name', ''),
        'language': user.get('language', 'fr')
    })


@app.route('/api/profile', methods=['PUT'])
@jwt_required()
@limiter.limit("20 per hour")
def update_profile():
    username = get_jwt_identity()
    data = request.get_json()
    users = load_json(USERS_FILE)

    if username not in users:
        return jsonify({'error': 'Utilisateur non trouvé'}), 404
    if 'full_name' in data:
        users[username]['full_name'] = data['full_name']
    if 'email' in data:
        users[username]['email'] = data['email']
    if 'language' in data:
        users[username]['language'] = data['language']
    if 'new_password' in data and data['new_password']:
        if len(data['new_password']) < 6:
            return jsonify({'error': 'Nouveau mot de passe trop court'}), 400
        users[username]['password'] = generate_password_hash(data['new_password'])

    save_json(USERS_FILE, users)
    return jsonify({'message': 'Profil mis à jour avec succès'})


# ===== PREDICTION =====
@app.route('/api/predict', methods=['POST'])
@jwt_required()
@limiter.limit("30 per hour")
def predict():
    username = get_jwt_identity()
    data = request.get_json()

    for field in ['weight', 'height', 'age']:
        if field not in data:
            return jsonify({'error': f'Champ manquant: {field}'}), 400
    try:
        weight = float(data['weight'])
        height = float(data['height'])
        age = int(data['age'])
    except (ValueError, TypeError):
        return jsonify({'error': 'Valeurs numériques invalides'}), 400

    if not (20 <= weight <= 300):
        return jsonify({'error': 'Poids invalide (20-300 kg)'}), 400
    if not (100 <= height <= 250):
        return jsonify({'error': 'Taille invalide (100-250 cm)'}), 400
    if not (1 <= age <= 120):
        return jsonify({'error': 'Âge invalide (1-120)'}), 400

    predictions, bmi = predict_disease(data)

    history = load_json(HISTORY_FILE)
    if username not in history:
        history[username] = []

    entry = {
        'id': str(uuid.uuid4()),
        'date': datetime.now().isoformat(),
        'data': {k: v for k, v in data.items()},
        'bmi': bmi,
        'results': predictions
    }
    history[username].insert(0, entry)
    history[username] = history[username][:20]
    save_json(HISTORY_FILE, history)

    return jsonify({'predictions': predictions, 'bmi': bmi, 'entry_id': entry['id']})


@app.route('/api/history', methods=['GET'])
@jwt_required()
def get_history():
    username = get_jwt_identity()
    history = load_json(HISTORY_FILE)
    return jsonify({'history': history.get(username, [])})


@app.route('/api/history/<entry_id>', methods=['DELETE'])
@jwt_required()
def delete_history_entry(entry_id):
    username = get_jwt_identity()
    history = load_json(HISTORY_FILE)
    history[username] = [e for e in history.get(username, []) if e['id'] != entry_id]
    save_json(HISTORY_FILE, history)
    return jsonify({'message': 'Entrée supprimée'})


@app.errorhandler(429)
def too_many_requests(e):
    return jsonify({'error': '⛔ Trop de tentatives. Patientez quelques minutes.'}), 429


if __name__ == '__main__':
    print("🏥 Serveur médical démarré sur http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)