


import os
import uuid
from pathlib import Path


from app.models.user import User
from app.schemas.application import ApplicationResponse
from app.schemas.user import UserResponse
from num2words import num2words
from docxtpl import DocxTemplate
from app.models.document import Document
from app.core.database import AsyncSession, AsyncSessionLocal
from datetime import datetime
async def  create_attestation(db:AsyncSessionLocal,user_id:uuid.UUID,application:ApplicationResponse):
 template_path = Path(__file__).resolve().parents[2] / "utils" / "pdf" / "Attestation1.docx"
 doc = DocxTemplate(str(template_path))
 data = {
    "id": 12,

    "username": "Abderrahmane",
    "last_name": "Hamaidi",

    "birth_day": "12/05/2002",
    "birth_place": "Alger",

    "nbr_jour": 30,

    "destination": "France",
    "etablissment": "Université Paris-Saclay",

    "begin": "01/06/2026",
    "end": "30/06/2026",

    "budget": "84 000 DA",
    "budget_words": "Quatre-vingt-quatre mille dinars algériens",

    "frais_inscription": "10 000 DA",

    "date_now": datetime.utcnow().strftime("%d/%m/%Y"),
}
 user = await db.get(User, user_id)
 data.update(build_attestation_data(user, application))
 doc.render(data) #render the daynamic data in the template
 save_dir = f"generated/attestations/{application.id}" #create a directory for the application if it doesn't exist
 os.makedirs(save_dir, exist_ok=True)
 filename = f"attestation_{uuid.uuid4()}.docx"
 output_path = os.path.join(save_dir, filename)
 doc.save(output_path)
 file_size = os.path.getsize(output_path)

 new_document = Document(
        application_id=application.id,
        document_type="attestation",
        file_path=output_path,
        file_name=filename,
        file_size=file_size,
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        user_id=user.id
    )
 db.add(new_document)
 await db.commit()
 await db.refresh(new_document)
 #update the application with the attestation information this is for the front end to know that the attestation is submitted and it can show the download button for the attestation and it can also show the date of submission of the attestation
 application.attestation_id = new_document.id
 application.attestation_submitted = True
 uploaded_at = new_document.uploaded_at
 if uploaded_at is not None and uploaded_at.tzinfo is not None:
     uploaded_at = uploaded_at.replace(tzinfo=None)
 application.attestation_submitted_at = uploaded_at
 await db.commit()
 return new_document

def dzd_to_words(amount: int) -> str:
    return num2words(amount, lang='fr').capitalize() + " dinars algériens" 
def build_attestation_data(user:UserResponse, application:ApplicationResponse):
    duration_days = (application.end_date - application.start_date).days + 1

    return {
        "id": application.id,

        "username": user.username,
        "last_name": user.lastname,

        #"birth_day": user.birth_date.strftime("%d/%m/%Y"),
        #"birth_place": user.birth_place,

        "nbr_jour": duration_days,

        "destination": application.destination_country,
        #"etablissment": application.establishment,

        "begin": application.start_date.strftime("%d/%m/%Y"),
        "end": application.end_date.strftime("%d/%m/%Y"),

        "budget": f"{application.calculated_fees:,}".replace(",", " ") + " DA",
        "budget_words": dzd_to_words(application.calculated_fees),

       # "frais_inscription": f"{application.fees:,}".replace(",", " ") + " DA",

        "date_now": datetime.utcnow().strftime("%d/%m/%Y"),
    }
