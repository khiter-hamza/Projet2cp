import asyncio
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.application import Application
from app.models.enums import Countries, CSDecision, StageType, Status, UserGrade, UserRole
from app.models.laboratory import Laboratory
from app.models.session import Session
from app.models.user import User


DEV_PASSWORD = "password"
DEV_SESSION_NAME = "Dev Integration Session 2026"


async def get_or_create_laboratory(db):
    result = await db.execute(select(Laboratory).where(Laboratory.name == "Dev Test Laboratory"))
    laboratory = result.scalar_one_or_none()

    if laboratory:
        return laboratory

    laboratory = Laboratory(name="Dev Test Laboratory")
    db.add(laboratory)
    await db.flush()
    return laboratory


async def get_or_create_user(db, *, email, username, lastname, role, grade, laboratory_id, anciente=3):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user:
        user.username = username
        user.lastname = lastname
        user.role = role
        user.grade = grade
        user.laboratory_id = laboratory_id
        user.is_active = True
        return user

    user = User(
        email=email,
        username=username,
        lastname=lastname,
        role=role,
        grade=grade,
        anciente=anciente,
        is_active=True,
        laboratory_id=laboratory_id,
        hashed_password=hash_password(DEV_PASSWORD),
    )
    db.add(user)
    await db.flush()
    return user


async def get_or_create_dev_session(db, admin_id):
    result = await db.execute(select(Session).where(Session.name == DEV_SESSION_NAME))
    session = result.scalar_one_or_none()

    if not session:
        session = Session(
            name=DEV_SESSION_NAME,
            academic_year="2025-2026",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            budget=1_000_000,
            created_by=admin_id,
        )
        db.add(session)
        await db.flush()

    # The current backend decision service expects one active session.
    active_sessions = await db.execute(select(Session).where(Session.is_active == True))
    for active_session in active_sessions.scalars().all():
        active_session.is_active = active_session.id == session.id

    session.is_active = True
    session.is_open = True
    session.end_date = date(2026, 12, 31)
    session.budget = 1_000_000
    return session


async def upsert_application(db, *, title, user_id, session_id, status, stage_type, start_date, end_date,
                             destination_country, destination_city, host_institution, score, is_eligible,
                             calculated_fees, submitted_at, admin_id=None, cs_decision=None,
                             rejection_reason=None, approved_at=None, rejected_at=None,
                             completed_at=None, closed_at=None, cancelled_at=None):
    result = await db.execute(select(Application).where(Application.title_of_stay == title))
    application = result.scalar_one_or_none()

    if not application:
        application = Application(title_of_stay=title)
        db.add(application)

    application.user_id = user_id
    application.session_id = session_id
    application.status = status
    application.stage_type = stage_type
    application.start_date = start_date
    application.end_date = end_date
    application.destination_country = destination_country
    application.destination_city = destination_city
    application.host_institution = host_institution
    application.scientific_objective = f"Seed data for integration test: {title}."
    application.score = score
    application.is_eligible = is_eligible
    application.calculated_fees = calculated_fees
    application.submitted_at = submitted_at
    application.created_at = submitted_at
    application.cs_decision = cs_decision
    application.rejection_reason = rejection_reason
    application.approved_at = approved_at
    application.rejected_at = rejected_at
    application.completed_at = completed_at
    application.closed_at = closed_at
    application.cancelled_at = cancelled_at
    application.action_confirmation_by_id = admin_id if cs_decision or status in {Status.CANCELLED, Status.CLOSED} else None
    application.stage_report_submitted = status in {Status.COMPLETED, Status.CLOSED}
    application.attestation_submitted = status in {Status.APPROVED, Status.COMPLETED, Status.CLOSED}
    return application


async def main():
    async with AsyncSessionLocal() as db:
        laboratory = await get_or_create_laboratory(db)

        admin = await get_or_create_user(
            db,
            email="dev.admin@esi.dz",
            username="Dev",
            lastname="Admin",
            role=UserRole.admin_dpgr,
            grade=UserGrade.mca_a,
            laboratory_id=laboratory.id,
            anciente=10,
        )
        super_admin = await get_or_create_user(
            db,
            email="dev.superadmin@esi.dz",
            username="Dev",
            lastname="SuperAdmin",
            role=UserRole.super_admin,
            grade=UserGrade.professeur,
            laboratory_id=laboratory.id,
            anciente=15,
        )
        assistant = await get_or_create_user(
            db,
            email="dev.assistant@esi.dz",
            username="Dev",
            lastname="Assistant",
            role=UserRole.assistant_dpgr,
            grade=UserGrade.enseignant_chercheur,
            laboratory_id=laboratory.id,
            anciente=5,
        )
        researchers = [
            await get_or_create_user(
                db,
                email="dev.chercheur1@esi.dz",
                username="Sara",
                lastname="Hamidouche",
                role=UserRole.chercheur,
                grade=UserGrade.professeur,
                laboratory_id=laboratory.id,
                anciente=12,
            ),
            await get_or_create_user(
                db,
                email="dev.chercheur2@esi.dz",
                username="Ali",
                lastname="Benali",
                role=UserRole.chercheur,
                grade=UserGrade.mca_a,
                laboratory_id=laboratory.id,
                anciente=7,
            ),
            await get_or_create_user(
                db,
                email="dev.chercheur3@esi.dz",
                username="Leila",
                lastname="Kaci",
                role=UserRole.chercheur,
                grade=UserGrade.doctorant_salarie,
                laboratory_id=laboratory.id,
                anciente=2,
            ),
        ]
        active_researchers = [
            await get_or_create_user(
                db,
                email="dev.active1@esi.dz",
                username="Nadir",
                lastname="Mansouri",
                role=UserRole.chercheur,
                grade=UserGrade.mca_b,
                laboratory_id=laboratory.id,
                anciente=6,
            ),
            await get_or_create_user(
                db,
                email="dev.active2@esi.dz",
                username="Oumaima",
                lastname="Rahmani",
                role=UserRole.chercheur,
                grade=UserGrade.enseignant_chercheur,
                laboratory_id=laboratory.id,
                anciente=4,
            ),
            await get_or_create_user(
                db,
                email="dev.active3@esi.dz",
                username="Karim",
                lastname="Saidi",
                role=UserRole.chercheur,
                grade=UserGrade.professeur,
                laboratory_id=laboratory.id,
                anciente=11,
            ),
            await get_or_create_user(
                db,
                email="dev.active4@esi.dz",
                username="Meriem",
                lastname="Boukhalfa",
                role=UserRole.chercheur,
                grade=UserGrade.doctorant_non_salarie,
                laboratory_id=laboratory.id,
                anciente=1,
            ),
        ]
        submitted_researchers = [
            await get_or_create_user(
                db,
                email="dev.submitted1@esi.dz",
                username="Anis",
                lastname="Derradji",
                role=UserRole.chercheur,
                grade=UserGrade.professeur,
                laboratory_id=laboratory.id,
                anciente=9,
            ),
            await get_or_create_user(
                db,
                email="dev.submitted2@esi.dz",
                username="Yasmine",
                lastname="Meziane",
                role=UserRole.chercheur,
                grade=UserGrade.mca_a,
                laboratory_id=laboratory.id,
                anciente=7,
            ),
            await get_or_create_user(
                db,
                email="dev.submitted3@esi.dz",
                username="Rabah",
                lastname="Khellaf",
                role=UserRole.chercheur,
                grade=UserGrade.mca_b,
                laboratory_id=laboratory.id,
                anciente=5,
            ),
            await get_or_create_user(
                db,
                email="dev.submitted4@esi.dz",
                username="Lina",
                lastname="Aitouche",
                role=UserRole.chercheur,
                grade=UserGrade.doctorant_salarie,
                laboratory_id=laboratory.id,
                anciente=2,
            ),
            await get_or_create_user(
                db,
                email="dev.submitted5@esi.dz",
                username="Hichem",
                lastname="Bensaid",
                role=UserRole.chercheur,
                grade=UserGrade.enseignant_chercheur,
                laboratory_id=laboratory.id,
                anciente=4,
            ),
            await get_or_create_user(
                db,
                email="dev.submitted6@esi.dz",
                username="Amel",
                lastname="Zerrouki",
                role=UserRole.chercheur,
                grade=UserGrade.doctorant_non_salarie,
                laboratory_id=laboratory.id,
                anciente=1,
            ),
            await get_or_create_user(
                db,
                email="dev.submitted7@esi.dz",
                username="Mounir",
                lastname="Lahlou",
                role=UserRole.chercheur,
                grade=UserGrade.professeur,
                laboratory_id=laboratory.id,
                anciente=13,
            ),
            await get_or_create_user(
                db,
                email="dev.submitted8@esi.dz",
                username="Selma",
                lastname="Boudjemaa",
                role=UserRole.chercheur,
                grade=UserGrade.mca_a,
                laboratory_id=laboratory.id,
                anciente=8,
            ),
        ]

        session = await get_or_create_dev_session(db, admin.id)

        submitted_apps = [
            ("DEV-SUB-001 Paris Research Stay", submitted_researchers[0], Countries.france, "Paris", "Sorbonne Universite", 92, True, 120000, date(2026, 4, 10), date(2026, 4, 20)),
            ("DEV-SUB-002 Berlin Training", submitted_researchers[1], Countries.allemagne, "Berlin", "TU Berlin", 74, True, 98000, date(2026, 5, 5), date(2026, 5, 15)),
            ("DEV-SUB-003 Tunis Collaboration", submitted_researchers[2], Countries.tunisie, "Tunis", "University of Tunis El Manar", 81, True, 110000, date(2026, 6, 8), date(2026, 6, 22)),
            ("DEV-SUB-004 Constantine Training", submitted_researchers[3], Countries.algerie, "Constantine", "University of Constantine 2", 61, False, 45000, date(2026, 7, 1), date(2026, 7, 8)),
            ("DEV-SUB-005 Munich Research Stay", submitted_researchers[4], Countries.allemagne, "Munich", "Technical University of Munich", 88, True, 140000, date(2026, 9, 12), date(2026, 9, 26)),
            ("DEV-SUB-006 Grenoble Training", submitted_researchers[5], Countries.france, "Grenoble", "Universite Grenoble Alpes", 55, False, 76000, date(2026, 10, 3), date(2026, 10, 10)),
            ("DEV-SUB-007 Lyon Publication Stay", submitted_researchers[6], Countries.france, "Lyon", "INSA Lyon", 95, True, 132000, date(2026, 11, 5), date(2026, 11, 19)),
            ("DEV-SUB-008 Sousse Quality Training", submitted_researchers[7], Countries.tunisie, "Sousse", "University of Sousse", 68, True, 69000, date(2026, 12, 2), date(2026, 12, 9)),
        ]

        for index, (title, researcher, country, city, institution, score, eligible, fees, start, end) in enumerate(submitted_apps, start=1):
            await upsert_application(
                db,
                title=title,
                user_id=researcher.id,
                session_id=session.id,
                status=Status.SUBMITTED,
                stage_type=StageType.sejour_scientifique if index % 2 else StageType.stage_perfectionnement,
                start_date=start,
                end_date=end,
                destination_country=country,
                destination_city=city,
                host_institution=institution,
                score=score,
                is_eligible=eligible,
                calculated_fees=fees,
                submitted_at=datetime(2026, 2, index, 9, 0, 0),
            )

        history_apps = [
            ("DEV-HIST-001 Approved Paris", researchers[0], Status.EXPIRED, CSDecision.approved, None, datetime(2026, 1, 18, 9, 0, 0), None, None, None, None),
            ("DEV-HIST-002 Rejected Lyon", researchers[1], Status.REJECTED, CSDecision.rejected, "Missing invitation document.", None, datetime(2026, 1, 19, 9, 0, 0), None, datetime(2026, 1, 19, 9, 0, 0), None),
            ("DEV-HIST-003 Closed Munich", researchers[2], Status.CLOSED, CSDecision.approved, None, datetime(2026, 1, 20, 9, 0, 0), None, datetime(2026, 3, 25, 9, 0, 0), datetime(2026, 4, 2, 9, 0, 0), None),
            ("DEV-HIST-004 Cancelled Tunis", researchers[0], Status.CANCELLED, CSDecision.approved, "Visa appointment delayed.", datetime(2026, 1, 21, 9, 0, 0), None, None, None, datetime(2026, 2, 10, 9, 0, 0)),
            ("DEV-HIST-005 Expired Grenoble", researchers[1], Status.EXPIRED, CSDecision.approved, None, datetime(2026, 1, 22, 9, 0, 0), None, None, None, None),
        ]

        for index, (title, researcher, status, decision, reason, approved_at, rejected_at, completed_at, closed_at, cancelled_at) in enumerate(history_apps, start=1):
            await upsert_application(
                db,
                title=title,
                user_id=researcher.id,
                session_id=session.id,
                status=status,
                stage_type=StageType.sejour_scientifique,
                start_date=date(2026, 3, index + 5),
                end_date=date(2026, 3, index + 12),
                destination_country=Countries.france,
                destination_city="Paris",
                host_institution="Seed History Institution",
                score=70 + index,
                is_eligible=True,
                calculated_fees=80000 + (index * 5000),
                submitted_at=datetime(2026, 1, index, 9, 0, 0),
                admin_id=assistant.id,
                cs_decision=decision,
                rejection_reason=reason,
                approved_at=approved_at,
                rejected_at=rejected_at,
                completed_at=completed_at,
                closed_at=closed_at,
                cancelled_at=cancelled_at,
            )

        active_apps = [
            ("DEV-ACTIVE-001 Approved Stay", active_researchers[0], Status.APPROVED, None, None, date(2026, 4, 28), date(2026, 5, 8)),
            ("DEV-ACTIVE-002 Report Submitted", active_researchers[1], Status.COMPLETED, datetime(2026, 3, 11, 9, 0, 0), None, date(2026, 3, 1), date(2026, 3, 10)),
            ("DEV-ACTIVE-003 Cancellation Request", active_researchers[2], Status.CANCELLATION_REQUEST, None, "Schedule conflict with final exams.", date(2026, 5, 15), date(2026, 5, 25)),
            ("DEV-ACTIVE-004 Correction Needed", active_researchers[3], Status.CORRECTION_NEEDED, datetime(2026, 2, 20, 9, 0, 0), None, date(2026, 2, 12), date(2026, 2, 19)),
        ]

        for index, (title, researcher, status, completed_at, cancel_reason, start, end) in enumerate(active_apps, start=1):
            application = await upsert_application(
                db,
                title=title,
                user_id=researcher.id,
                session_id=session.id,
                status=status,
                stage_type=StageType.sejour_scientifique,
                start_date=start,
                end_date=end,
                destination_country=Countries.france if index != 3 else Countries.tunisie,
                destination_city="Paris" if index != 3 else "Sousse",
                host_institution="Dev Active Stay Institution",
                score=80 + index,
                is_eligible=True,
                calculated_fees=90000 + (index * 7000),
                submitted_at=datetime(2026, 2, 10 + index, 9, 0, 0),
                admin_id=admin.id,
                cs_decision=CSDecision.approved,
                rejection_reason=None,
                approved_at=datetime(2026, 2, 20 + index, 9, 0, 0),
                completed_at=completed_at,
                closed_at=None,
                cancelled_at=None,
            )
            if cancel_reason:
                application.cancellation_reason = cancel_reason
                application.cancelled_requested_at = datetime(2026, 3, 5, 9, 0, 0)

        await db.commit()

        print("Seed complete.")
        print(f"Active session: {DEV_SESSION_NAME} ({session.id})")
        print("Super Admin login: dev.superadmin@esi.dz / password")
        print("Admin login: dev.admin@esi.dz / password")
        print("Assistant login: dev.assistant@esi.dz / password")
        print("Submitted-app researcher logins: dev.chercheur1@esi.dz, dev.chercheur2@esi.dz, dev.chercheur3@esi.dz / password")
        print("Unique submitted-app users: dev.submitted1@esi.dz through dev.submitted8@esi.dz / password")
        print("Active-stay researcher logins: dev.active1@esi.dz, dev.active2@esi.dz, dev.active3@esi.dz, dev.active4@esi.dz / password")
        print("Correction-needed researcher login: dev.active4@esi.dz / password")
        print("Created/updated 8 submitted applications, 5 history applications, and 4 active stays.")


if __name__ == "__main__":
    asyncio.run(main())
