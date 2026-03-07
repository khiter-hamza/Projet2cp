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
    
class NotificationType(str, enum.Enum):
    status_change = "status_change"
    cs_decision = "cs_decision"
    reminder = "reminder"
    deadline = "deadline"
    system_update = "system_update"

class Status(str,enum.Enum):
    brouillon ="brouillon" 
    soumise ="soumise" 
    verification ="verification"
    preparation_cs = "preparation_cs"
    deliberation_cs ="deliberation_cs"
    approuve = "approuve"
    rejete = "rejete"
    en_attente = "en_attente"
    termine = "termine"
    demande_annulation = "demande_annulation"
    deliberation_finale = "deliberation_finale"
    cloture = "cloture" 
    annule = "annule"

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
    en_attente ="en_attente"


class Documents_type(str, enum.Enum):
    invitation="invitation"
    passport="passport"
    cv="cv"
    programme="programme"
    accord_labo="accord_labo"
    ordre_mission="ordre_mission"
    report="report"
    attestation="attestation"
