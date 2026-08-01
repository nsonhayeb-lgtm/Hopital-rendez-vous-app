import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="Gestion File d'Attente Hôpital", page_icon="🏥"
)

st.title("🏥 Système Intelligent de Gestion des Files d'Attente")
st.write(
    "Inscrivez-vous à distance pour obtenir votre heure de passage estimée."
)


# ✅ NOUVEAU CODE (Mémoire partagée globale entre TOUS les téléphones)
@st.cache_resource
def obtenir_registre_global():
    # Cette liste est stockée sur le serveur et partagée par tout le monde
    return []


# On récupère la liste partagée
liste_patients = obtenir_registre_global()

# Barème des symptômes
bareme = {
    "fièvre": 1,
    "toux": 1,
    "douleur modérée": 2,
    "femme enceinte": 3,
    "difficulté respiratoire": 8,
    "perte de connaissance": 10,
}

# Crée deux onglets dans l'application web
onglet1, onglet2 = st.tabs(
    ["📝 Inscription Patient", "⏱️ Accueil & Contrôle des Retards"]
)

# ==========================================
# ONGLET 1 : INSCRIPTION PATIENT A DISTANCE
# ==========================================
with onglet1:
    st.header("Formulaire d'inscription")

    with st.form("form_patient"):
        nom = st.text_input("Nom & Prénom")
        age = st.number_input("Âge", min_value=0, max_value=120, value=25)
        sexe = st.selectbox("Sexe", ["M", "F"])
        service = st.selectbox(
            "Service demandé",
            ["Cardiologie", "Pédiatrie", "Médecine Générale"],
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

            nb_patients = len(liste_patients)
            total_minutes = (nb_patients * duree) + heure_debut_m

            rdv_h = heure_debut_h + (total_minutes // 60)
            rdv_m = total_minutes % 60

            heure_rdv = f"{rdv_h:02d}h{rdv_m:02d}"

            # Calcul de l'heure d'arrivée conseillée (-10 min)
            m_conseil = total_minutes - 10
            cons_h = heure_debut_h + (m_conseil // 60)
            cons_m = m_conseil % 60
            heure_conseil = f"{cons_h:02d}h{cons_m:02d}"

            # Sauvegarde dans la liste globale
            liste_patients.append(
                {
                    "nom": nom,
                    "heure_rdv": heure_rdv,
                    "priorite": priorite,
                    "statut": "En attente",
                }
            )

            # Affichage du billet de RDV
            st.success("✅ Inscription réussie !")
            st.info(f"**Heure de consultation prévue :** {heure_rdv}")
            st.warning(
                f"📩 **Message :** Ne venez pas maintenant. Veuillez arriver à **{heure_conseil}** (10 minutes avant)."
            )


# ==========================================
# ONGLET 2 : CONTROLE DU RETARD (Côté Hôpital)
# ==========================================
with onglet2:
    st.header("📊 Vue Hôpital & Gestion des Retards")

    # Affichage du tableau des patients
    if len(liste_patients) > 0:
        st.subheader("Planning des rendez-vous du jour :")
        st.table(liste_patients)

        st.write("---")
        st.subheader("🔍 Vérification du retard à l'arrivée :")

        # Sélection du patient et saisie de l'heure
        noms_patients = [p["nom"] for p in liste_patients]
        patient_selectionne = st.selectbox(
            "Saisez le nom du patient qui arrive :", noms_patients
        )

        heure_arrivee_reelle = st.text_input(
            "Heure d'arrivée réelle à l'accueil (ex: 08h20 ou 08:20)", "08h15"
        )

        if st.button("Vérifier l'arrivée"):
            # Correction de la coquille : liste_patients au lieu de sliste_patients
            info_p = next(
                p for p in liste_patients if p["nom"] == patient_selectionne
            )
            heure_rdv = info_p["heure_rdv"]

            # Conversion sécurisée en minutes
            h_rdv, m_rdv = heure_rdv.split("h")
            min_rdv = int(h_rdv) * 60 + int(m_rdv)

            # Gestion du format si l'utilisateur met ':' au lieu de 'h'
            heure_clean = heure_arrivee_reelle.replace(":", "h")
            h_arr, m_arr = heure_clean.split("h")
            min_arr = int(h_arr) * 60 + int(m_arr)

            retard = min_arr - min_rdv

            # Application des règles
            if retard <= 0:
                st.success(
                    f"✅ Patient à l'heure ! ({abs(retard)} min d'avance). Envoyez-le en salle d'attente."
                )
                info_p["statut"] = "Présent"
            elif retard <= 10:
                st.warning(
                    f"⚠️ Retard toléré ({retard} min). Le patient est admis."
                )
                info_p["statut"] = "Présent (Retard accepté)"
            else:
                st.error(
                    f"🚨 RETARD DE {retard} MIN (> 10 min) ! Rendez-vous ANNULÉ ou replacé en fin de file."
                )
                info_p["statut"] = "Annulé (Retard)"
    else:
        st.write("Aucun patient inscrit pour le moment.")
