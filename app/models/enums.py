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
    

