import os
import streamlit as st
from datetime import datetime, timezone, timedelta

# Configuration de la page
st.set_page_config(
    page_title="Gestion File d'Attente Hôpital", page_icon="🏥"
)

# --- GESTION DYNAMIQUE DU MOT DE PASSE ---
FICHIER_MDP = "mdp_staff.txt"

def lire_mot_de_passe():
    """Lit le mot de passe dans le fichier local ou retourne un mot de passe par défaut."""
    if os.path.exists(FICHIER_MDP):
        with open(FICHIER_MDP, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "hopital2026"  # Mot de passe par défaut à la première utilisation

def sauvegarder_mot_de_passe(nouveau_mdp):
    """Enregistre le nouveau mot de passe dans le fichier local."""
    with open(FICHIER_MDP, "w", encoding="utf-8") as f:
        f.write(nouveau_mdp)


# --- EN-TÊTE DE L'APPLICATION ---
st.title("🏥 Système Intelligent de Gestion des Files d'Attente")

st.warning(
    "⚠️ **Attention :** Si vous n'arrivez pas à l'heure prévue, votre rendez-vous est automatiquement annulé."
)

st.write(
    "Inscrivez-vous à distance pour obtenir votre heure de passage estimée."
)


# Mémoire partagée globale entre tous les utilisateurs
@st.cache_resource
def obtenir_registre_global():
    return []


# On récupère la liste partagée
liste_patients = obtenir_registre_global()

# Bareme complet des symptômes
bareme = {
    "Congestion nasale (nez bouché)": 1,
    "Maux de gorge légers": 2,
    "Toux sèche ou grasse": 3,
    "Nausées / Troubles digestifs légers": 3,
    "Fatigue modérée (Asthénie)": 4,
    "Fièvre modérée (38°C – 39°C)": 5,
    "Perte de poids involontaire": 6,
    "Vertiges / Étourdissements répétés": 6,
    "Céphalée intense et soudaine": 8,
    "Essoufflement / Dyspnée de repos": 9,
    "Douleur thoracique aiguë / Oppression": 10,
    "Perte de connaissance / Coma": 10,
}


# Fonction d'annulation automatique des rendez-vous dépassés
def mettre_a_jour_statuts_automatiques(liste_p, maintenant):
    for p in liste_p:
        if p["statut"] in ["En attente", "Programmé pour demain"] and p["heure_rdv"] != "IMMÉDIAT":
            try:
                jour, mois, annee = map(int, p["date_rdv"].split("/"))
                h_rdv, m_rdv = map(int, p["heure_rdv"].split("h"))
                rdv_dt = datetime(annee, mois, jour, h_rdv, m_rdv, tzinfo=timezone.utc)

                limite_passage = rdv_dt + timedelta(minutes=10)
                if maintenant > limite_passage:
                    p["statut"] = "Annulé (Absence / Non-présenté)"
            except Exception:
                pass


# Obtention de l'heure GMT actuelle et mise à jour automatique des annulations
maintenant_gmt = datetime.now(timezone.utc)
mettre_a_jour_statuts_automatiques(liste_patients, maintenant_gmt)


# Crée deux onglets dans l'application web
onglet1, onglet2 = st.tabs(
    ["📝 Inscription Patient", "⏱️ Accueil & Contrôle des Retards"]
)

# ==========================================
# ONGLET 1 : INSCRIPTION PATIENT A DISTANCE
# ==========================================
with onglet1:
    st.header("Formulaire d'inscription")

    st.info(f"🕒 **Heure actuelle (GMT) :** {maintenant_gmt.strftime('%H:%M')}")

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

        cochés = {}
        for symptome in bareme.keys():
            cochés[symptome] = st.checkbox(symptome)

        st.write("---")
        st.write("**Cas d'urgences graves :**")
        urgence_vitale = st.checkbox(
            "Accident grave / AVC / Crise cardiaque suspectée"
        )

        submit = st.form_submit_button("S'inscrire")

    if submit:
        if not nom:
            st.error("Veuillez entrer votre nom.")
        else:
            score_total = sum(bareme[symp] for symp, selectionne in cochés.items() if selectionne)

            if score_total <= 3:
                priorite = "Faible"
            elif score_total <= 7:
                priorite = "Moyenne"
            elif score_total <= 12:
                priorite = "Élevée"
            else:
                priorite = "Urgence"

            est_urgent = score_total >= 8 or priorite in ["Élevée", "Urgence"] or urgence_vitale

            if est_urgent:
                date_str = maintenant_gmt.strftime("%d/%m/%Y")
                liste_patients.append(
                    {
                        "nom": nom,
                        "date_rdv": date_str,
                        "heure_rdv": "IMMÉDIAT",
                        "priorite": priorite if not urgence_vitale else "Urgence Vitale",
                        "score": score_total if not urgence_vitale else 10,
                        "statut": "Prise en charge immédiate (Urgence)",
                    }
                )

                st.error("🚨 CAS URGENT / ÉLEVÉ DÉTECTÉ !")
                st.warning("⚠️ Prise en charge **IMMÉDIATE** requise. Aucune planification de créneau nécessaire.")
                st.info("Veuillez vous présenter DIRECTEMENT au service des urgences de l'hôpital.")

            else:
                patients_programmes = [p for p in liste_patients if p["heure_rdv"] != "IMMÉDIAT"]
                nb_patients = len(patients_programmes)
                duree = 15
                est_apres_20h = maintenant_gmt.hour >= 20

                if est_apres_20h:
                    date_rdv = maintenant_gmt + timedelta(days=1)
                    total_minutes = nb_patients * duree

                    rdv_dt = datetime(date_rdv.year, date_rdv.month, date_rdv.day, 8, 0, tzinfo=timezone.utc) + timedelta(minutes=total_minutes)
                    heure_rdv = rdv_dt.strftime("%Hh%M")
                    date_str = rdv_dt.strftime("%d/%m/%Y")

                    m_conseil = total_minutes - 10
                    cons_dt = datetime(date_rdv.year, date_rdv.month, date_rdv.day, 8, 0, tzinfo=timezone.utc) + timedelta(minutes=m_conseil)
                    heure_conseil = cons_dt.strftime("%Hh%M")

                    liste_patients.append(
                        {
                            "nom": nom,
                            "date_rdv": date_str,
                            "heure_rdv": heure_rdv,
                            "priorite": priorite,
                            "score": score_total,
                            "statut": "Programmé pour demain",
                        }
                    )

                    st.warning("⚠️ Il est plus de 20h00 GMT. Seules les urgences sont reçues cette nuit.")
                    st.success("✅ Votre rendez-vous a été reprogrammé pour DEMAIN !")
                    st.info(f"📅 **Date :** {date_str} à **{heure_rdv} GMT**")
                    st.warning(f"📩 **Arrivée conseillée :** {heure_conseil} GMT (10 minutes avant).")

                else:
                    heure_debut = datetime(maintenant_gmt.year, maintenant_gmt.month, maintenant_gmt.day, 8, 0, tzinfo=timezone.utc)
                    base_dt = max(maintenant_gmt, heure_debut)
                    rdv_dt = base_dt + timedelta(minutes=nb_patients * duree)

                    heure_rdv = rdv_dt.strftime("%Hh%M")
                    cons_dt = rdv_dt - timedelta(minutes=10)
                    heure_conseil = cons_dt.strftime("%Hh%M")
                    date_str = rdv_dt.strftime("%d/%m/%Y")

                    liste_patients.append(
                        {
                            "nom": nom,
                            "date_rdv": date_str,
                            "heure_rdv": heure_rdv,
                            "priorite": priorite,
                            "score": score_total,
                            "statut": "En attente",
                        }
                    )

                    st.success("✅ Inscription réussie !")
                    st.info(f"**Heure de consultation prévue (GMT) :** {heure_rdv}")
                    st.warning(f"📩 Veuillez arriver à **{heure_conseil} GMT** (10 minutes avant).")


# ==========================================
# ONGLET 2 : CONTROLE DU RETARD (Personnel Hôpital)
# ==========================================
with onglet2:
    st.header("🔒 Espace Réservé au Personnel de l'Hôpital")

    # Initialisation de l'état de connexion
    if "staff_connecte" not in st.session_state:
        st.session_state.staff_connecte = False

    mdp_actuel = lire_mot_de_passe()

    if not st.session_state.staff_connecte:
        st.warning("⚠️ Accès restreint. Veuillez vous connecter avec le mot de passe du personnel.")
        
        with st.form("form_connexion_staff"):
            mot_de_passe = st.text_input("Mot de passe", type="password")
            submit_login = st.form_submit_button("Se connecter")
            
        if submit_login:
            if mot_de_passe == mdp_actuel:
                st.session_state.staff_connecte = True
                st.success("Connexion réussie !")
                st.rerun()
            else:
                st.error("❌ Mot de passe incorrect.")
    else:
        # Barre d'actions du personnel (Déconnexion & Modification MDP)
        col_btn1, col_btn2 = st.columns([1, 2])
        
        with col_btn1:
            if st.button("Se déconnecter"):
                st.session_state.staff_connecte = False
                st.rerun()

        with st.expander("🔑 Modifier le mot de passe de l'espace personnel"):
            with st.form("form_change_mdp"):
                nouveau_mdp = st.text_input("Nouveau mot de passe", type="password")
                confirmation_mdp = st.text_input("Confirmer le nouveau mot de passe", type="password")
                submit_change = st.form_submit_button("Enregistrer le nouveau mot de passe")
                
            if submit_change:
                if not nouveau_mdp:
                    st.error("Le mot de passe ne peut pas être vide.")
                elif nouveau_mdp != confirmation_mdp:
                    st.error("Les deux mots de passe ne correspondent pas.")
                else:
                    sauvegarder_mot_de_passe(nouveau_mdp)
                    st.success("✅ Mot de passe mis à jour avec succès !")

        st.write("---")
        st.subheader("📊 Planning des rendez-vous & urgences")

        if len(liste_patients) > 0:
            st.table(liste_patients)

            st.write("---")
            st.subheader("🔍 Vérification du patient à l'arrivée")

            nom_saisi = st.text_input("Saisissez le nom du patient à vérifier :")

            heure_arrivee_reelle = st.text_input(
                "Heure d'arrivée réelle à l'accueil (Format GMT, ex: 08h20 ou 20:15)",
                maintenant_gmt.strftime("%Hh%M"),
            )

            if st.button("Vérifier l'arrivée"):
                if not nom_saisi:
                    st.error("Veuillez saisir un nom.")
                else:
                    info_p = next(
                        (p for p in liste_patients if p["nom"].strip().lower() == nom_saisi.strip().lower()),
                        None,
                    )

                    if info_p is None:
                        st.error(f"❌ Aucun patient trouvé au nom de '{nom_saisi}'. Veuillez vérifier la saisie.")
                    elif info_p["statut"] == "Annulé (Absence / Non-présenté)":
                        st.error(
                            f"❌ Le rendez-vous de **{info_p['nom']}** a été ANNULÉ automatiquement par le système car l'heure de passage est dépassée sans signalement d'arrivée."
                        )
                    elif info_p["heure_rdv"] == "IMMÉDIAT":
                        st.error(
                            f"🚨 Patient **{info_p['nom']}** enregistré en PRISE EN CHARGE IMMÉDIATE ({info_p['priorite']}). Envoyez-le directement au service d'urgence !"
                        )
                        info_p["statut"] = "Pris en charge (Urgence)"
                    else:
                        heure_rdv = info_p["heure_rdv"]

                        h_rdv, m_rdv = map(int, heure_rdv.split("h"))
                        min_rdv = h_rdv * 60 + m_rdv

                        heure_clean = heure_arrivee_reelle.replace(":", "h")
                        try:
                            h_arr, m_arr = map(int, heure_clean.split("h"))
                            min_arr = h_arr * 60 + m_arr

                            retard = min_arr - min_rdv

                            if retard <= 0:
                                st.success(
                                    f"✅ Patient **{info_p['nom']}** à l'heure ! ({abs(retard)} min d'avance). Envoyez-le en salle d'attente."
                                )
                                info_p["statut"] = "Présent"
                            elif retard <= 10:
                                st.warning(
                                    f"⚠️ Retard toléré pour **{info_p['nom']}** ({retard} min). Le patient est admis."
                                )
                                info_p["statut"] = "Présent (Retard accepté)"
                            else:
                                st.error(
                                    f"🚨 RETARD DE {retard} MIN (> 10 min) ! Rendez-vous ANNULÉ."
                                )
                                info_p["statut"] = "Annulé (Retard)"
                        except ValueError:
                            st.error("Format d'heure d'arrivée invalide. Utilisez 'HHhMM' ou 'HH:MM'.")
        else:
            st.write("Aucun patient inscrit pour le moment.")
