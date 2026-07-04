"""initial schema

Revision ID: 96184c2f96ae
Revises:
Create Date: 2026-07-03

Crée les 5 tables du MVP Phase 1 : users, profiles, countries_criteria,
documents_checklist, scoring_history.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "96184c2f96ae"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("whatsapp_number", sa.String(20), unique=True, nullable=True),
        sa.Column("email", sa.String(255), unique=True, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.Column("updated_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_users_whatsapp_number", "users", ["whatsapp_number"])
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), unique=True, nullable=False),
        sa.Column("age", sa.Integer, nullable=True),
        sa.Column("nationalite", sa.String(100), server_default="Sénégal"),
        sa.Column("niveau_diplome", sa.String(100), nullable=True),
        sa.Column("domaine_etude", sa.String(255), nullable=True),
        sa.Column("etablissement", sa.String(255), nullable=True),
        sa.Column("annee_obtention", sa.Integer, nullable=True),
        sa.Column("annees_experience", sa.Float, server_default="0"),
        sa.Column("secteur_activite", sa.String(255), nullable=True),
        sa.Column("poste_actuel", sa.String(255), nullable=True),
        sa.Column("langues", postgresql.JSON, server_default="{}"),
        sa.Column("capacite_financiere_fcfa", sa.Integer, nullable=True),
        sa.Column("pays_cible", sa.String(100), nullable=True),
        sa.Column("type_demarche", sa.String(100), nullable=True),
        sa.Column("donnees_source", sa.String(50), server_default="questionnaire"),
        sa.Column("cv_brut_json", postgresql.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.Column("updated_at", sa.DateTime, nullable=True),
    )

    op.create_table(
        "countries_criteria",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pays", sa.String(100), nullable=False),
        sa.Column("type_demarche", sa.String(100), nullable=False),
        sa.Column(
            "type_critere",
            sa.Enum(
                "NIVEAU_DIPLOME", "LANGUE", "EXPERIENCE", "AGE",
                "CAPACITE_FINANCIERE", "DOMAINE_ETUDE", "AUTRE",
                name="typecritere",
            ),
            nullable=False,
        ),
        sa.Column("libelle", sa.String(255), nullable=False),
        sa.Column("valeur_requise", sa.String(255), nullable=False),
        sa.Column("valeur_requise_numerique", sa.Float, nullable=True),
        sa.Column("poids", sa.Integer, server_default="10"),
        sa.Column("eliminatoire", sa.Boolean, server_default="false"),
        sa.Column("explication", sa.Text, nullable=True),
        sa.Column("source_officielle", sa.String(500), nullable=True),
    )
    op.create_index("ix_countries_criteria_pays", "countries_criteria", ["pays"])
    op.create_index("ix_countries_criteria_type_demarche", "countries_criteria", ["type_demarche"])

    op.create_table(
        "documents_checklist",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pays", sa.String(100), nullable=False),
        sa.Column("type_demarche", sa.String(100), nullable=False),
        sa.Column("document", sa.String(255), nullable=False),
        sa.Column("delai_obtention_estime", sa.String(100), nullable=True),
        sa.Column("obligatoire", sa.Boolean, server_default="true"),
        sa.Column("ordre_affichage", sa.Integer, server_default="0"),
        sa.Column("remarque", sa.Text, nullable=True),
    )
    op.create_index("ix_documents_checklist_pays", "documents_checklist", ["pays"])
    op.create_index("ix_documents_checklist_type_demarche", "documents_checklist", ["type_demarche"])

    op.create_table(
        "scoring_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("pays", sa.String(100), nullable=False),
        sa.Column("type_demarche", sa.String(100), nullable=False),
        sa.Column("score_total", sa.Float, nullable=False),
        sa.Column("tranche", sa.String(50), nullable=False),
        sa.Column("eliminatoire_manquant", postgresql.JSON, server_default="[]"),
        sa.Column("details_criteres", postgresql.JSON, nullable=False),
        sa.Column("plan_coaching", postgresql.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("scoring_history")
    op.drop_table("documents_checklist")
    op.drop_table("countries_criteria")
    op.drop_table("profiles")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS typecritere")
