import enum


class UserRole(str, enum.Enum):
    chercheur = "chercheur"
    assistant_dpgr = "assistant_dpgr"
    admin_dpgr = "admin_dpgr"
    super_admin = "super_admin"


class UserGrade(str, enum.Enum):
    professeur = "professeur"
    mca_a = "mca_a"
    mca_b = "mca_b"
    enseignant_chercheur = "enseignant_chercheur"
    doctorant_salarie = "doctorant_salarie"
    doctorant_non_salarie = "doctorant_non_salarie"
    
class Status(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    COMPLETED = "completed"
    CANCELLATION_REQUEST="cancellation_request"
    CORRECTION_NEEDED="correction_needed"
    EXPIRED="expired"
    CLOSED = "closed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class NotificationType(str, enum.Enum):
    status_change = "status_change"
    cs_decision = "cs_decision"
    reminder = "reminder"
    deadline = "deadline"
    system_update = "system_update"

class Countries(str, enum.Enum):
    algerie = "algerie"
    france = "france"
    allemagne = "allemagne"
    tunisie = "tunisie"

class StageType(str,enum.Enum):
    stage_perfectionnement = "stage_perfectionnement" 
    sejour_scientifique = "sejour_scientifique" 

class CSDecision(str,enum.Enum):
    approved = "approved"
    rejected = "rejected"


class Documents_type(str, enum.Enum):
    invitation="invitation"
    passport="passport"
    cv="cv"
    programme="programme"
    accord_labo="accord_labo"
    ordre_mission="ordre_mission"
    report="report"
    attestation="attestation"
    visa="visa"
