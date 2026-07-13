"""
Correction ponctuelle : le montant de preuve financière Canada/visa_etudiant a été
mis à jour par IRCC (20 635 -> 22 895 CAD/an, effectif depuis septembre 2025), mais
cette donnée est déjà en base sur les environnements existants (seed_criteria.py ne
re-seed pas les lignes déjà présentes). Ce script corrige la ligne existante en place.

Usage : PYTHONPATH=. python3 seeds/fix_montant_canada_2026.py
"""
from app.database import SessionLocal
from app.models.criteria import CountryCriteria


def run():
    db = SessionLocal()
    try:
        critere = (
            db.query(CountryCriteria)
            .filter(
                CountryCriteria.pays == "Canada",
                CountryCriteria.type_demarche == "visa_etudiant",
                CountryCriteria.libelle == "Preuve de fonds suffisants",
            )
            .first()
        )
        if not critere:
            print("⚠️ Critère non trouvé — rien à corriger (déjà à jour ou seed jamais lancé ?).")
            return

        ancien = critere.valeur_requise
        critere.valeur_requise = "22 895 CAD/an (depuis sept. 2025, hors Québec)"
        critere.valeur_requise_numerique = 22895
        db.commit()
        print(f"✅ Corrigé : '{ancien}' -> '{critere.valeur_requise}'")
    finally:
        db.close()


if __name__ == "__main__":
    run()
