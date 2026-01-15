"""Small, trusted FAQ snippets to prevent hallucinations on factual Epitech topics.

These answers are intentionally high-level and avoid inventing numbers/dates.
"""

from __future__ import annotations


def methodology_fr() -> str:
    return (
        "La pédagogie Epitech est surtout une pédagogie **par projets** (learning by doing) :\n"
        "- **Peu de cours magistraux** : tu apprends en construisant des projets concrets.\n"
        "- **Autonomie + responsabilité** : on te donne un objectif, à toi d’organiser ton travail.\n"
        "- **Apprentissage entre pairs** : entraide, review, travail en équipe (comme en entreprise).\n"
        "- **Évaluation continue** : on juge sur les livrables, la progression et la capacité à résoudre.\n"
        "- **Professionnalisation** : projets proches du réel, stages/alternance selon parcours.\n\n"
        "Pour te répondre précisément : tu vises quel parcours (PGE / MSc / Coding Academy) et tu es à quel niveau (Lycée, Bac+2/3, reconversion) ?"
    )


def methodology_en() -> str:
    return (
        "Epitech’s approach is mainly **project-based learning** (learning by doing):\n"
        "- **Few traditional lectures**: you learn by building real projects.\n"
        "- **Autonomy & accountability**: you organize your work to reach clear goals.\n"
        "- **Peer learning**: teamwork, code reviews, mutual help.\n"
        "- **Continuous assessment**: evaluated on deliverables and progress.\n"
        "- **Industry focus**: projects close to real-world needs + internships/apprenticeship depending on track.\n\n"
        "To tailor it: which track (PGE / MSc / Coding Academy) and what’s your current level?"
    )

