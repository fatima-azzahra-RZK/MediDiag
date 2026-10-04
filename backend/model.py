"""
Modèle de prédiction des maladies basé sur les symptômes et paramètres médicaux.
Utilise un système de règles médicales + scoring pour la prédiction.
"""

import numpy as np

DISEASES = {
    "Diabète de type 2": {
        "description": "Trouble métabolique caractérisé par une glycémie élevée.",
        "recommendations": [
            "Consultez un endocrinologue immédiatement",
            "Adoptez un régime alimentaire pauvre en sucres",
            "Pratiquez une activité physique régulière (30 min/jour)",
            "Surveillez votre glycémie régulièrement",
            "Évitez l'alcool et le tabac"
        ],
        "urgency": "high",
        "icon": "🩸"
    },
    "Hypertension artérielle": {
        "description": "Pression artérielle chroniquement élevée (>140/90 mmHg).",
        "recommendations": [
            "Réduisez votre consommation de sel",
            "Pratiquez une activité physique modérée",
            "Évitez le stress et les situations anxiogènes",
            "Consultez un cardiologue",
            "Prenez vos médicaments si prescrits"
        ],
        "urgency": "high",
        "icon": "❤️"
    },
    "Obésité": {
        "description": "Excès de masse grasse avec IMC ≥ 30.",
        "recommendations": [
            "Consultez un nutritionniste",
            "Adoptez une alimentation équilibrée et hypocalorique",
            "Augmentez progressivement votre activité physique",
            "Évitez les aliments ultra-transformés",
            "Envisagez un suivi psychologique si nécessaire"
        ],
        "urgency": "medium",
        "icon": "⚖️"
    },
    "Syndrome métabolique": {
        "description": "Ensemble de troubles augmentant le risque cardiovasculaire.",
        "recommendations": [
            "Perte de poids de 5-10% du poids corporel recommandée",
            "Exercice aérobique 150 min/semaine",
            "Alimentation méditerranéenne",
            "Bilan biologique complet recommandé",
            "Suivi médical régulier"
        ],
        "urgency": "medium",
        "icon": "🫀"
    },
    "Insuffisance respiratoire": {
        "description": "Difficulté à maintenir des échanges gazeux adéquats.",
        "recommendations": [
            "Arrêt du tabac immédiat et définitif",
            "Consultation pneumologue urgente",
            "Spirométrie recommandée",
            "Éviter les environnements pollués",
            "Vaccinations antigrippale et antipneumococcique"
        ],
        "urgency": "critical",
        "icon": "🫁"
    },
    "Anémie": {
        "description": "Taux d'hémoglobine insuffisant pour oxygéner les tissus.",
        "recommendations": [
            "Augmentez votre consommation de fer (viandes, légumineuses)",
            "Supplémentation en fer et/ou vitamine B12",
            "Bilan sanguin complet",
            "Consultez votre médecin généraliste",
            "Évitez le thé et café avec les repas"
        ],
        "urgency": "medium",
        "icon": "🔴"
    },
    "Trouble anxieux": {
        "description": "Anxiété excessive perturbant le quotidien.",
        "recommendations": [
            "Consultez un psychiatre ou psychologue",
            "Pratiquez la méditation et la relaxation",
            "Réduisez la consommation de caféine",
            "Maintenez un sommeil régulier",
            "Thérapie cognitivo-comportementale (TCC) recommandée"
        ],
        "urgency": "medium",
        "icon": "🧠"
    },
    "Bonne santé générale": {
        "description": "Aucun signe pathologique majeur détecté.",
        "recommendations": [
            "Maintenez votre mode de vie sain",
            "Bilan de santé annuel recommandé",
            "Continuez l'activité physique régulière",
            "Alimentation équilibrée et hydratation suffisante",
            "Vaccinations à jour"
        ],
        "urgency": "low",
        "icon": "✅"
    }
}


def calculate_bmi(weight, height):
    """Calcule l'IMC (Indice de Masse Corporelle)"""
    if height <= 0 or weight <= 0:
        return 0
    return weight / ((height / 100) ** 2)


def predict_disease(data):
    """
    Prédit les maladies potentielles basées sur les données patient.
    
    data: dict avec les clés:
        - weight (kg), height (cm), age, gender
        - smoker, alcohol, exercise
        - symptoms: list
        - allergies, chronic_disease, medications
        - fatigue, headache, chest_pain, shortness_breath,
          dizziness, nausea, fever, joint_pain
    """
    scores = {disease: 0 for disease in DISEASES}
    bmi = calculate_bmi(data.get('weight', 70), data.get('height', 170))
    age = data.get('age', 30)
    symptoms = data.get('symptoms', [])
    
    # ===== DIABÈTE =====
    if bmi >= 30: scores["Diabète de type 2"] += 30
    elif bmi >= 25: scores["Diabète de type 2"] += 15
    if age >= 45: scores["Diabète de type 2"] += 20
    if data.get('smoker'): scores["Diabète de type 2"] += 10
    if data.get('chronic_disease'): scores["Diabète de type 2"] += 15
    if 'fatigue' in symptoms: scores["Diabète de type 2"] += 15
    if 'frequent_thirst' in symptoms: scores["Diabète de type 2"] += 25
    if 'frequent_urination' in symptoms: scores["Diabète de type 2"] += 25
    if 'blurred_vision' in symptoms: scores["Diabète de type 2"] += 15
    if data.get('alcohol'): scores["Diabète de type 2"] += 10
    
    # ===== HYPERTENSION =====
    if bmi >= 28: scores["Hypertension artérielle"] += 20
    if age >= 50: scores["Hypertension artérielle"] += 25
    if data.get('smoker'): scores["Hypertension artérielle"] += 20
    if data.get('alcohol'): scores["Hypertension artérielle"] += 15
    if 'headache' in symptoms: scores["Hypertension artérielle"] += 20
    if 'chest_pain' in symptoms: scores["Hypertension artérielle"] += 25
    if 'dizziness' in symptoms: scores["Hypertension artérielle"] += 15
    if data.get('chronic_disease'): scores["Hypertension artérielle"] += 10
    if data.get('stress', False): scores["Hypertension artérielle"] += 15
    
    # ===== OBÉSITÉ =====
    if bmi >= 35: scores["Obésité"] += 80
    elif bmi >= 30: scores["Obésité"] += 60
    elif bmi >= 25: scores["Obésité"] += 20
    if not data.get('exercise'): scores["Obésité"] += 15
    if data.get('alcohol'): scores["Obésité"] += 10
    if 'joint_pain' in symptoms: scores["Obésité"] += 10
    if 'shortness_breath' in symptoms and bmi >= 28: scores["Obésité"] += 15
    
    # ===== SYNDROME MÉTABOLIQUE =====
    if bmi >= 27: scores["Syndrome métabolique"] += 20
    if data.get('smoker'): scores["Syndrome métabolique"] += 15
    if data.get('alcohol'): scores["Syndrome métabolique"] += 15
    if age >= 40: scores["Syndrome métabolique"] += 15
    if 'fatigue' in symptoms: scores["Syndrome métabolique"] += 10
    if data.get('chronic_disease'): scores["Syndrome métabolique"] += 20
    if not data.get('exercise'): scores["Syndrome métabolique"] += 15
    
    # ===== INSUFFISANCE RESPIRATOIRE =====
    if data.get('smoker'): scores["Insuffisance respiratoire"] += 40
    if 'shortness_breath' in symptoms: scores["Insuffisance respiratoire"] += 40
    if 'cough' in symptoms: scores["Insuffisance respiratoire"] += 25
    if 'chest_pain' in symptoms: scores["Insuffisance respiratoire"] += 20
    if age >= 55 and data.get('smoker'): scores["Insuffisance respiratoire"] += 20
    if bmi >= 35: scores["Insuffisance respiratoire"] += 15
    if data.get('allergies'): scores["Insuffisance respiratoire"] += 10
    
    # ===== ANÉMIE =====
    if 'fatigue' in symptoms: scores["Anémie"] += 30
    if 'dizziness' in symptoms: scores["Anémie"] += 25
    if 'pale_skin' in symptoms: scores["Anémie"] += 30
    if 'shortness_breath' in symptoms: scores["Anémie"] += 20
    if data.get('gender') == 'F': scores["Anémie"] += 10
    if data.get('medications'): scores["Anémie"] += 5
    
    # ===== TROUBLE ANXIEUX =====
    if 'headache' in symptoms: scores["Trouble anxieux"] += 20
    if 'dizziness' in symptoms: scores["Trouble anxieux"] += 15
    if 'nausea' in symptoms: scores["Trouble anxieux"] += 10
    if 'chest_pain' in symptoms: scores["Trouble anxieux"] += 15
    if 'fatigue' in symptoms: scores["Trouble anxieux"] += 10
    if 'insomnia' in symptoms: scores["Trouble anxieux"] += 30
    if 'palpitations' in symptoms: scores["Trouble anxieux"] += 25
    if data.get('smoker'): scores["Trouble anxieux"] += 5
    
    # ===== BONNE SANTÉ =====
    scores["Bonne santé générale"] = max(0, 100 - max(
        scores["Diabète de type 2"],
        scores["Hypertension artérielle"],
        scores["Obésité"],
        scores["Insuffisance respiratoire"],
        scores["Anémie"],
        scores["Trouble anxieux"]
    ))
    
    # Trier et filtrer les résultats
    sorted_diseases = sorted(
        [(k, v) for k, v in scores.items() if v > 0],
        key=lambda x: x[1],
        reverse=True
    )
    
    results = []
    for disease_name, score in sorted_diseases[:3]:
        if score > 10:
            disease_info = DISEASES[disease_name].copy()
            confidence = min(99, int(score * 1.2))
            disease_info['name'] = disease_name
            disease_info['confidence'] = confidence
            disease_info['bmi'] = round(bmi, 1)
            results.append(disease_info)
    
    if not results:
        disease_info = DISEASES["Bonne santé générale"].copy()
        disease_info['name'] = "Bonne santé générale"
        disease_info['confidence'] = 95
        disease_info['bmi'] = round(bmi, 1)
        results.append(disease_info)
    
    return results, round(bmi, 1)
