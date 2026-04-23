import os
import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.models.document import Document
from app.models.application import Application
from app.models.enums import Documents_type, Status
from app.schemas.document import DocumentResponse
from app.core.dependencies import get_current_user
from app.models.user import User
import zipstream
import zipfile
from datetime import datetime
from fastapi.responses import StreamingResponse


router = APIRouter()

UPLOAD_DIR = "uploads/documents"


@router.post('/applications/{application_id}/documents', response_model=DocumentResponse)
async def upload_document(    application_id: uuid.UUID,    document_type: Documents_type = Form(...),    file: UploadFile = File(...),    user=Depends(get_current_user),    db: AsyncSession = Depends(get_db),):
   
    contents = await file.read()

   
    ext = os.path.splitext(file.filename)[1]  
    unique_name = f"{uuid.uuid4()}{ext}"
    save_dir = os.path.join(UPLOAD_DIR, str(application_id))
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, unique_name)
    with open(file_path, "wb") as f:
        f.write(contents)
    new_document = Document(
        application_id=application_id,
        document_type=document_type,
        file_path=file_path,
        file_name=file.filename,
        file_size=len(contents),
        mime_type=file.content_type,
        user_id=user.id
    )
    db.add(new_document)
    await db.commit()
    await db.refresh(new_document)

    return new_document


@router.get('/applications/{application_id}/documents',response_model=list[DocumentResponse])
async def get_documents(application_id:uuid.UUID,db:AsyncSession=Depends(get_db),user=Depends(get_current_user)):
    try:
        res = await db.execute(select(Document).where(Document.application_id == application_id, Document.user_id == user.id).order_by(Document.uploaded_at.desc()))
        documents = res.scalars().all()
        if not documents:
            raise HTTPException(status_code=404, detail='No document found with this demmende_id')
        return documents
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
   
@router.delete('/document/{idd}')
async def delete_document(idd:uuid.UUID,db:AsyncSession=Depends(get_db),user:User=Depends(get_current_user)):
   res=await db.execute(select(Document).where(Document.id==idd,Document.user_id==user.id))
   document=res.scalar_one_or_none()
   if not document:
      raise HTTPException(status_code=404,detail='document not found')
   if document.document_type == Documents_type.report:# this set the stage_report_submitted to true and set the stage_report_id to the new document id and set the stage_report_submitted_at to the current date and time this is for the front end to know that the report is submitted and it can show the download button for the report and it can also show the date of submission of the report
       app=await db.get(Application,document.application_id)
       app.stage_report_submitted = False
       app.stage_report_id = None
       app.stage_report_submitted_at = None
       await db.commit()
   if document.document_type == Documents_type.attestation:# this set the attestation_submitted to true and set the attestation_id to the new document id and set the attestation_submitted_at to the current date and time this is for the front end to know that the attestation is submitted and it can show the download button for the attestation and it can also show the date of submission of the attestation
       app=await db.get(Application,document.application_id)
       app.attestation_submitted = False
       app.attestation_id = None
       app.attestation_submitted_at = None
       await db.commit()    
   await db.delete(document)
   await db.commit()
   return  {"details":"Document deleted succussfuly"} 

@router.get('/document/{idd}',response_model=DocumentResponse)
async def get_document(idd:uuid.UUID,db:AsyncSession=Depends(get_db),user:User=Depends(get_current_user)):
   res=await db.execute(select(Document).where(Document.id==idd,Document.user_id==user.id))
   document=res.scalar_one_or_none()
   if not document:
      raise HTTPException(status_code=404,detail='document not found')
   return document



@router.get("/document/{idd}/download")
async def download_document(idd:uuid.UUID,db:AsyncSession=Depends(get_db),user:User=Depends(get_current_user)):
   res=await db.execute(select(Document).where(Document.id==idd,Document.user_id==user.id))
   document=res.scalar_one_or_none()
   if not document:
      raise HTTPException(status_code=404,detail='document not found')
   if not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="file missing on server")
   return FileResponse(path=document.file_path, filename=document.file_name)




@router.get('/applications/{application_id}/documents/downloads')
async def downlods_demende_documents(application_id:uuid.UUID,db:AsyncSession=Depends(get_db),user:User=Depends(get_current_user)):
    try:
        res = await db.execute(
            select(Document).options(
                joinedload(Document.application).joinedload(Application.user)
            ).where(
                Document.application_id == application_id,
                Document.user_id == user.id
            ).order_by(Document.uploaded_at.desc())
        )
        documents = res.scalars().all()

        if not documents:
            raise HTTPException(status_code=404, detail='No document found with this demmende_id')

        zip_path = f"/tmp/{application_id}_{uuid.uuid4()}.zip"
        with zipfile.ZipFile(zip_path, "w") as zipf:
            for doc in documents:
                if os.path.exists(doc.file_path):
                    zipf.write(doc.file_path, arcname=doc.file_name)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"documents_{user.username}_{user.lastname}_{timestamp}.zip"
        return FileResponse(zip_path, filename=filename)

    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
   

@router.get('application/documents')
async def downlaod_all_user_docs(db:AsyncSession=Depends(get_db),user:User=Depends(get_current_user)):
   if    user.role.value != "admin_dpgr":
      raise HTTPException(status_code=401,detail='Unauthaurize')
   result = await db.execute(select(Document)
        .options(
            joinedload(Document.application).joinedload(Application.user)
                    )  )

   documents = result.scalars().all()
   if not documents:
        raise HTTPException(status_code=404, detail="No documents found")

   year = datetime.utcnow().year

   z = zipstream.ZipFile(mode="w", compression=zipstream.ZIP_DEFLATED)

   for doc in documents:
        user = doc.application.user

        folder = f"{user.username}_{user.lastname}_{user.id}"
        arcname = f"{folder}/{doc.file_name}"

        z.write(doc.file_path, arcname)

   return StreamingResponse(
        z,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={year}.zip"
        }
    )
