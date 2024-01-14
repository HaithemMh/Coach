from flask import Flask, request, jsonify, session
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import snowflake.connector
import os
import urllib.parse
import openai

# Configuration de la connexion Snowflake
user = os.environ.get('SNOWFLAKE_USER', 'haithemmh')
password = urllib.parse.quote_plus(os.environ.get('SNOWFLAKE_PASSWORD', ''))
account = os.environ.get('SNOWFLAKE_ACCOUNT', 'BCLSTQF-SG71977')

// Svp d'enlever le nom de votre warehouse
conn = snowflake.connector.connect(
    user='haithemmh',
    password='',
    account=account,
    warehouse='COMPUTE_WH',
    database='COACHSANTEDB',
    schema='COACHSANTESCHEMA'
)

app = Flask(__name__)
app.config['SECRET_KEY'] = b"\xe7\x12\t\xaf,\xedF\xe1g#V"

bcrypt = Bcrypt(app)
CORS(app, supports_credentials=True)

@app.route("/")
def hello_world():
    return "Hello, World!"

# Route d'inscription
@app.route("/signup", methods=["POST"])
def signup():
    email = request.json["email"]
    password = request.json["password"]

    cursor = conn.cursor()
    try:
        # Vérification de l'existence de l'email
        cursor.execute("SELECT EMAIL FROM COACHSANTEDB.COACHSANTESCHEMA.UTILISATEURS WHERE EMAIL = %s", (email,))
        if cursor.fetchone():
            return jsonify({"error": "Email already exists"}), 409

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Insertion du nouvel utilisateur
        cursor.execute("""
            INSERT INTO COACHSANTEDB.COACHSANTESCHEMA.UTILISATEURS (NOM, EMAIL, MOT_DE_PASSE) 
            VALUES (%s, %s, %s)
        """, (email.split('@')[0], email, hashed_password))
        conn.commit()

        return jsonify({"success": "User created successfully"})
    finally:
        cursor.close()


# Route de connexionvoici
@app.route("/login", methods=["POST"])
def login_user():
    email = request.json["email"]
    password = request.json["password"]

    cursor = conn.cursor()
    try:
        # Récupération de l'utilisateur par email
        cursor.execute("SELECT ID, EMAIL, MOT_DE_PASSE FROM COACHSANTEDB.COACHSANTESCHEMA.UTILISATEURS WHERE EMAIL = %s", (email,))
        user = cursor.fetchone()

        if not user or not bcrypt.check_password_hash(user[2], password):
            return jsonify({"error": "Unauthorized Access"}), 401

        session["user_id"] = user[0]
        return jsonify({"id": user[0], "email": user[1]})
    finally:
        cursor.close()

openai.api_key = ("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")

def get_openai_response(message):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a nutrition expert. Provide recipes and calorie counts based on user requests. Give detailed and accurate nutrition advice. "},
            {"role": "user", "content": message}
        ],
        max_tokens=100
    )
    return response['choices'][0]['message']['content']

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message")
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    chat_response = get_openai_response(user_message)
    return jsonify({"response": chat_response})



def generer_conseils_personnalises(questionnaire_data):
    conseils = "Voici quelques conseils de base pour commencer : "
    
    # Exemple de logique conditionnelle pour générer des conseils
    if questionnaire_data.get("niveauExperience") == "Débutant":
        conseils += "Comme vous êtes débutant, commencez par des séances de 30 minutes, 3 fois par semaine. "
    elif questionnaire_data.get("niveauExperience") == "Intermédiaire":
        conseils += "Comme vous avez de l'expérience, vous pouvez augmenter l'intensité de vos entraînements. "
    elif questionnaire_data.get("niveauExperience") == "Avancé":
        conseils += "En tant que sportif avancé, variez vos entraînements pour éviter la routine. "
    
    # Vous pouvez continuer avec d'autres conditions ici
    
    return conseils

# Fonction pour calculer l'IMC
def calcul_imc(poids, taille):
    taille_en_metres = taille / 100
    return poids / (taille_en_metres ** 2)

# Fonction pour calculer le TMB
def calcul_tmb(poids, taille, age, sexe):
    if sexe == 'Mâle':
        return 88.362 + (13.397 * poids) + (4.799 * taille) - (5.677 * age)
    else:
        return 447.593 + (9.247 * poids) + (3.098 * taille) - (4.330 * age)

# Fonction pour calculer les besoins caloriques quotidiens
def calcul_besoins_caloriques(tmb, niveau_activite):
    return tmb * niveau_activite

# Fonction pour estimer la masse musculaire (cette formule est très approximative)
def estim_masse_musculaire(poids, taille, sexe):
    if sexe == 'Mâle':
        return (0.32810 * poids) + (0.33929 * taille) - 29.5336
    else:
        return (0.29569 * poids) + (0.41813 * taille) - 43.2933

# Fonction pour estimer la masse grasse
def estim_masse_grasse(imc, age, sexe):
    if sexe == 'Mâle':
        return 1.20 * imc + 0.23 * age - 16.2
    else:
        return 1.20 * imc + 0.23 * age - 5.4

@app.route("/submit-form", methods=["POST"])
def submit_form():
    user_id = request.json.get("userId")
    questionnaire_data = request.json.get("fitnessData")

    # Vérifiez si questionnaire_data est None
    if questionnaire_data is None:
        return jsonify({"error": "No questionnaire data provided"}), 400

    # Vérifiez si toutes les clés nécessaires sont présentes
    required_keys = ["genre", "frequenceEntrainement", "niveauExperience", "objectifPrincipal", "equipement", "poids", "taille"]
    if not all(key in questionnaire_data for key in required_keys):
        return jsonify({"error": "Missing questionnaire data"}), 400
    
    # Connectez-vous à votre base de données Snowflake
    conn = snowflake.connector.connect(
    user='haithemmh',
    password='Haithem2013nike@',
    account=account,
    warehouse='COMPUTE_WH',
    database='COACHSANTEDB',
    schema='COACHSANTESCHEMA'
)
    cursor = conn.cursor()

    try:

        user_id = request.json.get("userId")
        questionnaire_data = request.json.get("fitnessData")

        print("User ID:", user_id)  # Log pour débogage
        print("Questionnaire Data:", questionnaire_data)
        # Insérez les données dans la table questionnaire_responses
        query = """
        INSERT INTO PUBLIC.questionnaire_responses 
        (user_id, genre, frequence_entrainement, niveau_experience, objectif_principal, equipement, poids, taille, age)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(query, (
            user_id, 
            questionnaire_data.get("genre"), 
            questionnaire_data.get("frequenceEntrainement"),
            questionnaire_data.get("niveauExperience"),
            questionnaire_data.get("objectifPrincipal"),
            questionnaire_data.get("equipement"),
            questionnaire_data.get("poids"),
            questionnaire_data.get("taille"),
            questionnaire_data.get("age")
        ))
        imc = calcul_imc(questionnaire_data.get("poids"), questionnaire_data.get("taille"))
        tmb = calcul_tmb(questionnaire_data.get("poids"), questionnaire_data.get("taille"), questionnaire_data.get("age"), questionnaire_data.get("genre"))
        # Ajouter d'autres calculs si nécessaire
        conn.commit()
       # Générer des conseils personnalisés
        conseils_personnalises = generer_conseils_personnalises(questionnaire_data)
        return jsonify({"message": "Questionnaire submitted successfully",
            "conseils": conseils_personnalises,
            "imc": imc,
            "tmb": tmb,
            "conseils": conseils_personnalises
            })
    except Exception as e:
        # Gérez ici les exceptions
        print("Error occurred:", e)
        return jsonify({"error": str(e.__traceback__)}), 500
    finally:
        cursor.close()
        conn.close()



if __name__ == "__main__":
    app.run(debug=True)


