import streamlit as st
from datetime import datetime, timezone, timedelta

# Configuration de la page
st.set_page_config(
    page_title="Gestion File d'Attente Hôpital", page_icon="🏥"
)

st.title("🏥 Système Intelligent de Gestion des Files d'Attente")
st.write(
    "Inscrivez-vous à distance pour obtenir votre heure de passage estimée."
)


# Mémoire partagée globale entre tous les utilisateurs
@st.cache_resource
def obtenir_registre_global():
    return []


# On récupère la liste partagée
liste_patients = obtenir_registre_global()

# Nouveau barème complet des symptômes (sans descriptions)
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

# Crée deux onglets dans l'application web
onglet1, onglet2 = st.tabs(
    ["📝 Inscription Patient", "⏱️ Accueil & Contrôle des Retards"]
)

# ==========================================
# ONGLET 1 : INSCRIPTION PATIENT A DISTANCE
# ==========================================
with onglet1:
    st.header("Formulaire d'inscription")

    # Affichage de l'heure actuelle en GMT
    maintenant_gmt = datetime.now(timezone.utc)
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

        # Dynamisation des cases à cocher à partir du barème
        cochés = {}
        for symptome, score in bareme.items():
            cochés[symptome] = st.checkbox(f"{symptome} (Sévérité: {score})")

        st.write("---")
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
            # Calcul du score cumulé
            score_total = sum(bareme[symp] for symp, selectionne in cochés.items() if selectionne)

            # Détermination de la priorité en fonction du score
            if score_total <= 3:
                priorite = "Faible"
            elif score_total <= 7:
                priorite = "Moyenne"
            elif score_total <= 12:
                priorite = "Élevée"
            else:
                priorite = "Urgence"

            est_apres_20h = maintenant_gmt.hour >= 20
            est_urgent = score_total >= 8 or priorite in ["Élevée", "Urgence"]

            # Règle sur l'horaire selon l'heure GMT et le niveau d'urgence
            if est_apres_20h and not est_urgent:
                # Reprogrammation sur le jour suivant à partir de 08:00 GMT
                date_rdv = maintenant_gmt + timedelta(days=1)
                
                # Calcul de l'horaire pour le lendemain
                duree = 15
                nb_patients = len(liste_patients)
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
                # Prise en charge aujourd'hui (Urgence après 20h ou créneau normal en journée)
                duree = 15
                nb_patients = len(liste_patients)
                
                # Heure de démarrage (8h00 sauf si c'est une urgence de nuit où c'est immédiat)
                if est_apres_20h:
                    rdv_dt = maintenant_gmt + timedelta(minutes=nb_patients * duree)
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
                if est_apres_20h and est_urgent:
                    st.error("🚨 Prise en charge d'urgence autorisée après 20h GMT.")
                st.info(f"**Heure de consultation prévue (GMT) :** {heure_rdv}")
                st.warning(f"📩 Veuillez arriver à **{heure_conseil} GMT** (10 minutes avant).")


# ==========================================
# ONGLET 2 : CONTROLE DU RETARD (Côté Hôpital)
# ==========================================
with onglet2:
    st.header("📊 Vue Hôpital & Gestion des Retards")

    if len(liste_patients) > 0:
        st.subheader("Planning des rendez-vous :")
        st.table(liste_patients)

        st.write("---")
        st.subheader("🔍 Vérification du retard à l'arrivée :")

        # Saisie manuelle du nom du patient (au lieu de la liste déroulante)
        nom_saisi = st.text_input("Saisissez le nom du patient à vérifier :")

        heure_arrivee_reelle = st.text_input(
            "Heure d'arrivée réelle à l'accueil (Format GMT, ex: 08h20 ou 20:15)",
            maintenant_gmt.strftime("%Hh%M"),
        )

        if st.button("Vérifier l'arrivée"):
            if not nom_saisi:
                st.error("Veuillez saisir un nom.")
            else:
                # Recherche insensible à la casse
                info_p = next(
                    (p for p in liste_patients if p["nom"].strip().lower() == nom_saisi.strip().lower()),
                    None,
                )

                if info_p is None:
                    st.error(f"❌ Aucun patient trouvé au nom de '{nom_saisi}'. Veuillez vérifier la saisie.")
                else:
                    heure_rdv = info_p["heure_rdv"]

                    # Conversion sécurisée en minutes
                    h_rdv, m_rdv = map(int, heure_rdv.split("h"))
                    min_rdv = h_rdv * 60 + m_rdv

                    # Harmonisation du format saisie heure d'arrivée
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
                                f"🚨 RETARD DE {retard} MIN (> 10 min) ! Rendez-vous ANNULÉ ou replacé en fin de file."
                            )
                            info_p["statut"] = "Annulé (Retard)"
                    except ValueError:
                        st.error("Format d'heure d'arrivée invalide. Utilisez 'HHhMM' ou 'HH:MM'.")
    else:
        st.write("Aucun patient inscrit pour le moment.")
