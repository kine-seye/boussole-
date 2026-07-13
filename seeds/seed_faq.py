"""
Peuplement de la FAQ avec des réponses vérifiées manuellement (recherche web + sources
officielles citées). Contrairement aux critères de scoring, ce sont des questions
transversales (frais, délais généraux) qui ne varient pas selon le profil de l'utilisateur.

⚠️ Chaque entrée doit avoir une source officielle vérifiable. Ne jamais ajouter un chiffre
qui n'est pas confirmé par au moins une source fiable et récente.
"""
from app.database import SessionLocal, engine, Base
from app.models.faq import FAQEntry


def seed_faq(db):
    entries = [
        FAQEntry(
            pays="Canada", type_demarche="visa_etudiant",
            sujet="frais_permis_etudes",
            question_type="Combien coûte le permis d'études / visa étudiant ?",
            reponse=(
                "Le permis d'études coûte 150 CAD (frais de traitement) + 85 CAD "
                "(biométrie) = 235 CAD au total. Ces frais sont ajustés chaque année, "
                "généralement au 31 mars."
            ),
            source_officielle="https://www.canada.ca/fr/immigration-refugies-citoyennete/services/frais.html",
            date_verification="2026-07",
        ),
        FAQEntry(
            pays="Canada", type_demarche="visa_etudiant",
            sujet="delai_traitement",
            question_type="Combien de temps prend le traitement d'un permis d'études ?",
            reponse=(
                "Le délai de traitement standard est généralement de 4 à 16 semaines, "
                "selon le bureau des visas et la période de l'année. Ce délai peut varier "
                "fortement, vérifie toujours le délai actuel affiché sur le site IRCC "
                "pour ton pays."
            ),
            source_officielle="https://www.canada.ca/fr/immigration-refugies-citoyennete/services/etudes-canada/permis-etudes.html",
            date_verification="2026-07",
        ),
        FAQEntry(
            pays="France", type_demarche="visa_etudiant",
            sujet="delai_traitement_visa",
            question_type="Combien de temps prend le traitement du visa étudiant France (VLS-TS) ?",
            reponse=(
                "Après validation du dossier Campus France, le délai de traitement du "
                "visa long séjour étudiant (VLS-TS) au consulat est généralement de "
                "2 à 8 semaines selon le consulat."
            ),
            source_officielle="https://www.senegal.campusfrance.org/la-procedure-etudes-en-france",
            date_verification="2026-07",
        ),
        FAQEntry(
            pays="France", type_demarche=None,
            sujet="budget_etudiant",
            question_type="Quel budget prévoir pour vivre en France ?",
            reponse=(
                "Campus France fournit un guide détaillé de budget étudiant par poste de "
                "dépense (logement, alimentation, transport, santé). Le montant exact varie "
                "fortement selon la ville (Paris étant nettement plus cher). Consulte le "
                "guide officiel plutôt qu'un chiffre unique, qui serait trompeur."
            ),
            source_officielle="https://www.senegal.campusfrance.org/preparer-son-budget",
            date_verification="2026-07",
        ),
    ]
    db.add_all(entries)


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(FAQEntry).count()
        if existing > 0:
            print(f"⚠️  {existing} entrées FAQ déjà présentes. Seed ignoré (évite les doublons).")
            return
        seed_faq(db)
        db.commit()
        print("✅ Seed FAQ terminé.")
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur pendant le seed FAQ : {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
