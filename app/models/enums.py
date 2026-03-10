import enum


class UserRole(str, enum.Enum):
    chercheur = "chercheur"
    asistant_dpgr = "asistant_dpgr"
    admin_dpgr = "admin_dpgr"
    super_admin = "super_admin"


class UserGrade(str, enum.Enum):
    professeur = "professeur"
    mca_a = "mca_a"
    mca_b = "mca_b"
    doctorant_salarie = "doctorant_salarie"
    doctorant_non_salarie = "doctorant_non_salarie"
    
class Status(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    CS_PREPARATION = "cs_preparation"
    APPROVED = "approved"
    COMPLETED = "completed"
    CLOSED = "closed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class Countries(str, enum.Enum):
    algerie = "algerie"
    france = "france"
    allemagne = "allemagne"
    tunisie = "tunisie"

class StageType(str,enum.Enum):
    stage_perfectionnement = "stage_perfectionnement" 
    sejour_scientifique = "sejour_scientifique" 

class CSDecision(str,enum.Enum):
    approuve = "approuve"
    rejete = "rejete"