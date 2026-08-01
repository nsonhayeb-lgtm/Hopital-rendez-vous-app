import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="Gestion File d'Attente Hôpital", page_icon="🏥"
)

st.title("🏥 Système Intelligent de Gestion des Files d'Attente")
st.write(
    "Inscrivez-vous à distance pour obtenir votre heure de passage estimée."
)

# Initialisation de la mémoire (session_state) pour stocker la liste des patients
if "liste_patients" not in st.session_state:
    st.session_state["liste_patients"] = []

# Barème des symptômes
bareme = {
    "fièvre": 1,
    "toux": 1,
    "douleur modérée": 2,
    "femme enceinte": 3,
    "difficulté respiratoire": 8,
    "perte de connaissance": 10,
}

# --- FORMULAIRE D'INSCRIPTION ---
st.header("📝 Inscription à distance")

with st.form("form_patient"):
    nom = st.text_input("Nom & Prénom")
    age = st.number_input("Âge", min_value=0, max_value=120, value=25)
    sexe = st.selectbox("Sexe", ["M", "F"])
    service = st.selectbox(
        "Service demandé", ["Cardiologie", "Pédiatrie", "Médecine Générale"]
    )

    st.write("---")
    st.subheader("Sélectionnez vos symptômes / état :")

    # Cases à cocher pour les symptômes
    fievre = st.checkbox("Fièvre")
    toux = st.checkbox("Toux")
    douleur = st.checkbox("Douleur modérée")
    enceinte = st.checkbox("Femme enceinte")
    diff_resp = st.checkbox("Difficulté respiratoire")
    perte_connaissance = st.checkbox("Perte de connaissance")

    st.write("**Cas d'urgences graves :**")
    urgence_vitale = st.checkbox(
        "Accident grave / AVC / Crise cardiaque suspectée"
    )

    submit = st.form_submit_button("S'inscrire")

# --- TRAITEMENT ET CALCUL ---
if submit:
    if not nom:
        st.error("Veuillez entrer votre nom.")
    elif urgence_vitale:
        st.error("🚨 URGENCE CRITIQUE DÉTECTÉE !")
        st.warning(
            "Ne venez pas via l'application. Rendez-vous DIRECTEMENT aux urgences de l'hôpital !"
        )
    else:
        # Calcul du score
        score = 0
        if fievre:
            score += bareme["fièvre"]
        if toux:
            score += bareme["toux"]
        if douleur:
            score += bareme["douleur modérée"]
        if enceinte:
            score += bareme["femme enceinte"]
        if diff_resp:
            score += bareme["difficulté respiratoire"]
        if perte_connaissance:
            score += bareme["perte de connaissance"]

        # Détermination de la priorité
        if score <= 3:
            priorite = "Faible"
        elif score <= 7:
            priorite = "Moyenne"
        elif score <= 12:
            priorite = "Élevée"
        else:
            priorite = "Urgence"

        # Calcul du temps de consultation (15 min par patient)
        heure_debut_h = 8
        heure_debut_m = 0
        duree = 15

        nb_patients = len(st.session_state["liste_patients"])
        total_minutes = (nb_patients * duree) + heure_debut_m

        rdv_h = heure_debut_h + (total_minutes // 60)
        rdv_m = total_minutes % 60

        heure_rdv = f"{rdv_h:02d}h{rdv_m:02d}"

        # Calcul de l'heure d'arrivée conseillée (-10 min)
        m_conseil = total_minutes - 10
        cons_h = heure_debut_h + (m_conseil // 60)
        cons_m = m_conseil % 60
        heure_conseil = f"{cons_h:02d}h{cons_m:02d}"

        # Sauvegarde
        st.session_state["liste_patients"].append(
            {"nom": nom, "heure_rdv": heure_rdv, "priorite": priorite}
        )

        # Affichage du billet de RDV
        st.success("✅ Inscription réussie !")
        st.info(f"**Heure de consultation prévue :** {heure_rdv}")
        st.warning(
            f"📩 **Message :** Ne venez pas maintenant. Veuillez arriver à **{heure_conseil}** (10 minutes avant)."
        )

# --- TABLEAU DE BORD (Côté Hôpital) ---
st.write("---")
st.header("📊 Vue Hôpital / File d'attente du jour")
if len(st.session_state["liste_patients"]) > 0:
    st.table(st.session_state["liste_patients"])
else:
    st.write("Aucun patient inscrit pour le moment.")
