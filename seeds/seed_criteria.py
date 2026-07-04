"""
Peuplement initial des critères d'éligibilité pour le MVP.

Scope Phase 1 volontairement restreint :
- Pays : Canada, France
- Démarches : visa_etudiant, bourse

⚠️ Ces critères sont des approximations pédagogiques basées sur les exigences
généralement observées. AVANT mise en production réelle, chaque ligne doit être
vérifiée et sourcée auprès des sites officiels (ambassade, Campus France, IRCC).
C'est indiqué explicitement pour rappeler qu'il ne faut jamais présenter ces
chiffres comme une vérité absolue aux utilisateurs finaux.
"""
from app.database import SessionLocal, engine, Base
from app.models.criteria import CountryCriteria, DocumentChecklist, TypeCritere


def seed_canada_visa_etudiant(db):
    criteres = [
        CountryCriteria(
            pays="Canada", type_demarche="visa_etudiant",
            type_critere=TypeCritere.NIVEAU_DIPLOME,
            libelle="Niveau de diplôme minimum",
            valeur_requise="Bac", valeur_requise_numerique=1,
            poids=15, eliminatoire=True,
            explication="Une admission dans un établissement désigné (DLI) est indispensable pour le permis d'études.",
            source_officielle="https://www.canada.ca/fr/immigration-refugies-citoyennete/services/etudier-canada/permis-etudes.html",
        ),
        CountryCriteria(
            pays="Canada", type_demarche="visa_etudiant",
            type_critere=TypeCritere.LANGUE,
            libelle="Niveau d'anglais (IELTS) ou de français (TEF)",
            valeur_requise="IELTS 6.0 ou TEF équivalent B2", valeur_requise_numerique=6.0,
            poids=20, eliminatoire=False,
            explication="Exigé par la plupart des établissements ; certains programmes en français acceptent le TEF/TCF.",
            source_officielle="https://www.canada.ca/fr/immigration-refugies-citoyennete/services/etudier-canada/permis-etudes.html",
        ),
        CountryCriteria(
            pays="Canada", type_demarche="visa_etudiant",
            type_critere=TypeCritere.CAPACITE_FINANCIERE,
            libelle="Preuve de fonds suffisants",
            valeur_requise="20 635 CAD/an (hors Québec, 2024)", valeur_requise_numerique=20635,
            poids=25, eliminatoire=True,
            explication="Doit couvrir frais de scolarité + subsistance pour la première année.",
            source_officielle="https://www.canada.ca/fr/immigration-refugies-citoyennete/services/etudier-canada/permis-etudes.html",
        ),
        CountryCriteria(
            pays="Canada", type_demarche="visa_etudiant",
            type_critere=TypeCritere.AGE,
            libelle="Âge",
            valeur_requise="Pas de limite officielle, mais dossier plus solide < 35 ans",
            valeur_requise_numerique=35,
            poids=10, eliminatoire=False,
            explication="Pas de plafond légal, mais l'agent d'immigration évalue la cohérence du projet migratoire selon l'âge.",
        ),
        CountryCriteria(
            pays="Canada", type_demarche="visa_etudiant",
            type_critere=TypeCritere.EXPERIENCE,
            libelle="Expérience professionnelle en lien avec le projet d'études",
            valeur_requise="Non obligatoire mais valorisée", valeur_requise_numerique=0,
            poids=10, eliminatoire=False,
            explication="Renforce la cohérence du projet, surtout pour les études supérieures spécialisées.",
        ),
        CountryCriteria(
            pays="Canada", type_demarche="visa_etudiant",
            type_critere=TypeCritere.DOMAINE_ETUDE,
            libelle="Cohérence du domaine d'étude avec le parcours antérieur",
            valeur_requise="Recommandée", valeur_requise_numerique=0,
            poids=20, eliminatoire=False,
            explication="Un changement radical de domaine sans justification affaiblit le dossier.",
        ),
    ]
    db.add_all(criteres)


def seed_canada_bourse(db):
    criteres = [
        CountryCriteria(
            pays="Canada", type_demarche="bourse",
            type_critere=TypeCritere.NIVEAU_DIPLOME,
            libelle="Niveau de diplôme minimum",
            valeur_requise="Licence pour Master, Master pour Doctorat", valeur_requise_numerique=2,
            poids=25, eliminatoire=True,
            explication="Les bourses type Vanier, ÉLAP ciblent les cycles supérieurs.",
        ),
        CountryCriteria(
            pays="Canada", type_demarche="bourse",
            type_critere=TypeCritere.LANGUE,
            libelle="Niveau d'anglais ou de français",
            valeur_requise="IELTS 6.5+ ou équivalent", valeur_requise_numerique=6.5,
            poids=20, eliminatoire=False,
            explication="Un bon niveau linguistique renforce fortement le dossier académique.",
        ),
        CountryCriteria(
            pays="Canada", type_demarche="bourse",
            type_critere=TypeCritere.EXPERIENCE,
            libelle="Expérience en recherche ou publications",
            valeur_requise="Valorisée, surtout pour doctorat", valeur_requise_numerique=1,
            poids=25, eliminatoire=False,
            explication="Les bourses d'excellence évaluent fortement le potentiel de recherche.",
        ),
        CountryCriteria(
            pays="Canada", type_demarche="bourse",
            type_critere=TypeCritere.DOMAINE_ETUDE,
            libelle="Pertinence du domaine par rapport aux priorités de financement",
            valeur_requise="Variable selon la bourse", valeur_requise_numerique=0,
            poids=15, eliminatoire=False,
            explication="Certains domaines (STEM, santé) sont davantage priorisés par les programmes canadiens.",
        ),
        CountryCriteria(
            pays="Canada", type_demarche="bourse",
            type_critere=TypeCritere.AGE,
            libelle="Âge",
            valeur_requise="Généralement < 35 ans pour bourses jeunes chercheurs", valeur_requise_numerique=35,
            poids=15, eliminatoire=False,
            explication="Varie fortement selon le programme, à vérifier au cas par cas.",
        ),
    ]
    db.add_all(criteres)


def seed_france_visa_etudiant(db):
    criteres = [
        CountryCriteria(
            pays="France", type_demarche="visa_etudiant",
            type_critere=TypeCritere.NIVEAU_DIPLOME,
            libelle="Niveau de diplôme minimum",
            valeur_requise="Bac (via Études en France / Campus France)", valeur_requise_numerique=1,
            poids=15, eliminatoire=True,
            explication="Passage obligatoire par la procédure Études en France pour le Sénégal.",
            source_officielle="https://www.campusfrance.org/fr/senegal",
        ),
        CountryCriteria(
            pays="France", type_demarche="visa_etudiant",
            type_critere=TypeCritere.LANGUE,
            libelle="Niveau de français (DELF/DALF si cursus non francophone)",
            valeur_requise="B2 recommandé", valeur_requise_numerique=0,
            poids=10, eliminatoire=False,
            explication="Le Sénégal étant francophone, ce critère est souvent déjà rempli, mais reste vérifié via l'entretien Campus France.",
        ),
        CountryCriteria(
            pays="France", type_demarche="visa_etudiant",
            type_critere=TypeCritere.CAPACITE_FINANCIERE,
            libelle="Preuve de ressources suffisantes",
            valeur_requise="~7 380 EUR/an (615 EUR/mois)", valeur_requise_numerique=7380,
            poids=30, eliminatoire=True,
            explication="Justificatif de ressources exigé pour le visa long séjour étudiant (VLS-TS).",
            source_officielle="https://france-visas.gouv.fr/",
        ),
        CountryCriteria(
            pays="France", type_demarche="visa_etudiant",
            type_critere=TypeCritere.DOMAINE_ETUDE,
            libelle="Cohérence et progressivité du projet d'études",
            valeur_requise="Fortement évaluée à l'entretien Campus France", valeur_requise_numerique=0,
            poids=25, eliminatoire=False,
            explication="L'entretien Campus France évalue la cohérence du projet académique et professionnel.",
        ),
        CountryCriteria(
            pays="France", type_demarche="visa_etudiant",
            type_critere=TypeCritere.AGE,
            libelle="Âge",
            valeur_requise="Pas de limite stricte", valeur_requise_numerique=40,
            poids=5, eliminatoire=False,
            explication="Pas de plafond légal mais un âge élevé sans progression de carrière peut être questionné.",
        ),
        CountryCriteria(
            pays="France", type_demarche="visa_etudiant",
            type_critere=TypeCritere.EXPERIENCE,
            libelle="Expérience professionnelle",
            valeur_requise="Valorisée pour Master 2 / MBA", valeur_requise_numerique=0,
            poids=15, eliminatoire=False,
            explication="Particulièrement importante pour les admissions en formation continue ou executive.",
        ),
    ]
    db.add_all(criteres)


def seed_france_bourse(db):
    criteres = [
        CountryCriteria(
            pays="France", type_demarche="bourse",
            type_critere=TypeCritere.NIVEAU_DIPLOME,
            libelle="Niveau de diplôme minimum",
            valeur_requise="Licence pour bourses Master (ex. Eiffel)", valeur_requise_numerique=2,
            poids=25, eliminatoire=True,
            explication="La bourse Eiffel cible les meilleurs étudiants internationaux en Master/Doctorat.",
            source_officielle="https://www.campusfrance.org/fr/bourse-eiffel",
        ),
        CountryCriteria(
            pays="France", type_demarche="bourse",
            type_critere=TypeCritere.AGE,
            libelle="Âge maximum",
            valeur_requise="25 ans (Master) / 30 ans (Doctorat) - critère Eiffel", valeur_requise_numerique=25,
            poids=20, eliminatoire=True,
            explication="La bourse Eiffel a un plafond d'âge strict et éliminatoire à la date de la candidature.",
        ),
        CountryCriteria(
            pays="France", type_demarche="bourse",
            type_critere=TypeCritere.DOMAINE_ETUDE,
            libelle="Établissement candidat classé prioritaire par le programme",
            valeur_requise="L'établissement français doit lui-même soumettre la candidature", valeur_requise_numerique=0,
            poids=20, eliminatoire=True,
            explication="Contrairement à d'autres bourses, c'est l'établissement français qui candidate pour l'étudiant, pas l'étudiant directement.",
        ),
        CountryCriteria(
            pays="France", type_demarche="bourse",
            type_critere=TypeCritere.EXPERIENCE,
            libelle="Excellence académique (classement, mentions)",
            valeur_requise="Dossier dans le top de la promotion", valeur_requise_numerique=0,
            poids=20, eliminatoire=False,
            explication="Critère central d'évaluation par le jury Eiffel.",
        ),
        CountryCriteria(
            pays="France", type_demarche="bourse",
            type_critere=TypeCritere.LANGUE,
            libelle="Niveau de français ou d'anglais selon le programme",
            valeur_requise="B2 minimum", valeur_requise_numerique=0,
            poids=15, eliminatoire=False,
            explication="Varie selon que le programme est enseigné en français ou en anglais.",
        ),
    ]
    db.add_all(criteres)


def seed_documents_checklists(db):
    documents = [
        # Canada - visa étudiant
        ("Canada", "visa_etudiant", "Lettre d'acceptation d'un établissement désigné (DLI)", "Variable (1-3 mois)", True, 1, None),
        ("Canada", "visa_etudiant", "Preuve de fonds suffisants (relevé bancaire ou garant)", "1-2 semaines", True, 2, "Doit couvrir la 1ère année complète"),
        ("Canada", "visa_etudiant", "Passeport valide", "Déjà en possession idéalement", True, 3, None),
        ("Canada", "visa_etudiant", "Résultats de test de langue (IELTS/TEF)", "4-8 semaines (inscription + résultats)", False, 4, "Non obligatoire pour tous les programmes mais fortement recommandé"),
        ("Canada", "visa_etudiant", "Certificat médical (si séjour > 6 mois)", "2-4 semaines", True, 5, "Réalisé chez un médecin agréé IRCC"),
        ("Canada", "visa_etudiant", "Lettre de motivation / plan d'études", "Rédaction personnelle", True, 6, None),
        ("Canada", "visa_etudiant", "Casier judiciaire (selon province)", "2-4 semaines", False, 7, "Demandé pour certains programmes ou provinces"),
        # Canada - bourse
        ("Canada", "bourse", "Relevés de notes officiels traduits", "2-4 semaines", True, 1, None),
        ("Canada", "bourse", "Lettres de recommandation académiques (2-3)", "Variable, à anticiper", True, 2, None),
        ("Canada", "bourse", "Lettre de motivation / projet de recherche", "Rédaction personnelle", True, 3, None),
        ("Canada", "bourse", "CV académique détaillé", "Rédaction personnelle", True, 4, None),
        ("Canada", "bourse", "Preuve d'admission ou de pré-admission", "Variable selon établissement", True, 5, None),
        ("Canada", "bourse", "Résultats de test de langue", "4-8 semaines", False, 6, None),
        # France - visa étudiant
        ("France", "visa_etudiant", "Dossier Études en France (Campus France Sénégal)", "Ouverture campagne ~oct-jan", True, 1, "Étape obligatoire avant toute demande de visa"),
        ("France", "visa_etudiant", "Lettre/preuve d'admission dans un établissement français", "Variable", True, 2, None),
        ("France", "visa_etudiant", "Justificatif de ressources (garant ou attestation bancaire)", "1-2 semaines", True, 3, "~615 EUR/mois minimum"),
        ("France", "visa_etudiant", "Passeport valide", "Déjà en possession idéalement", True, 4, None),
        ("France", "visa_etudiant", "Entretien Campus France", "Sur rendez-vous après dossier validé", True, 5, "Évalue la cohérence du projet"),
        ("France", "visa_etudiant", "Justificatif de logement en France", "Variable", False, 6, "Parfois demandé au stade du visa, sinon à l'arrivée"),
        ("France", "visa_etudiant", "Assurance / preuve de couverture santé", "1 semaine", False, 7, None),
        # France - bourse Eiffel
        ("France", "bourse", "Candidature soumise par l'établissement français (pas par l'étudiant)", "Selon calendrier Eiffel (~nov-jan)", True, 1, "Contacter l'établissement en amont pour être proposé"),
        ("France", "bourse", "Relevés de notes et diplômes traduits", "2-4 semaines", True, 2, None),
        ("France", "bourse", "CV et lettre de motivation", "Rédaction personnelle", True, 3, None),
        ("France", "bourse", "Lettres de recommandation", "Variable, à anticiper", True, 4, None),
        ("France", "bourse", "Preuve d'âge (< 25 ou < 30 ans selon niveau)", "Immédiat", True, 5, "Critère éliminatoire à vérifier avant de candidater"),
    ]
    for pays, demarche, doc, delai, obligatoire, ordre, remarque in documents:
        db.add(DocumentChecklist(
            pays=pays, type_demarche=demarche, document=doc,
            delai_obtention_estime=delai, obligatoire=obligatoire,
            ordre_affichage=ordre, remarque=remarque,
        ))


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Évite les doublons si le script est relancé
        existing = db.query(CountryCriteria).count()
        if existing > 0:
            print(f"⚠️  {existing} critères déjà présents en base. Seed ignoré (évite les doublons).")
            print("   Pour reseeder, videz d'abord les tables countries_criteria et documents_checklist.")
            return

        seed_canada_visa_etudiant(db)
        seed_canada_bourse(db)
        seed_france_visa_etudiant(db)
        seed_france_bourse(db)
        seed_documents_checklists(db)
        db.commit()
        print("✅ Seed terminé : critères et checklists Canada/France (visa étudiant + bourse).")
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur pendant le seed : {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
