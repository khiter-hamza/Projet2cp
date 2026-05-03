import os
import uuid
import datetime
import tempfile
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
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
    try:
        app=await db.get(Application,application_id)
        if not app:
            raise HTTPException(status_code=404,detail="Application not found")
        if app.status == Status.CANCELLED:
            raise HTTPException(status_code=400,detail="You can't upload a document for a cancelled application")
        
        if document_type == Documents_type.report:# this set the stage_report_submitted to true and set the stage_report_id to the new document id and set the stage_report_submitted_at to the current date and time this is for the front end to know that the report is submitted and it can show the download button for the report and it can also show the date of submission of the report
           if app.status != Status.APPROVED and app.status != Status.CORRECTION_NEEDED:
               raise HTTPException(status_code=400,detail="You can't submit a report for an application that is not approved")
           if app.stage_report_submitted:
               raise HTTPException(status_code=400,detail="You have already submitted a report for this application")
      
        document = await db.execute(select(Document).where(Document.application_id == application_id, Document.document_type == document_type))
        document_exists = document.scalar_one_or_none()
        if document_exists :
            raise HTTPException(status_code=400, detail=f"A document of type {document_type} already exists for this application")
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        if len(contents) > 10 * 1024 * 1024:  # Limit file size to 10MB
            raise HTTPException(status_code=400, detail="File size exceeds the 10MB limit")
        ext = os.path.splitext(file.filename)[1]
        unique_name = f"{uuid.uuid4()}{ext}"
        save_dir = os.path.join(UPLOAD_DIR, str(application_id))
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, unique_name)
        file_name= f"{document_type.value}_of_{user.username}_{user.lastname}{ext}"
        with open(file_path, "wb") as f:
            f.write(contents)
        new_document = Document(
            application_id=application_id,
            document_type=document_type,
            file_path=file_path,
            file_name=file_name,
            file_size=len(contents),
            mime_type=file.content_type,
            user_id=user.id
        )
        db.add(new_document)
        await db.commit()
        await db.refresh(new_document)
        if document_type == Documents_type.report:# this set the stage_report_submitted to true and set the stage_report_id to the new document id and set the stage_report_submitted_at to the current date and time this is for the front end to know that the report is submitted and it can show the download button for the report and it can also show the date of submission of the report
           uploaded_at = new_document.uploaded_at
           if uploaded_at is not None and uploaded_at.tzinfo is not None:
               uploaded_at = uploaded_at.replace(tzinfo=None)
           app.stage_report_submitted_at = uploaded_at
           app.stage_report_id = new_document.id
           app.stage_report_submitted = True
           app.status = Status.COMPLETED
           app.completed_at = datetime.utcnow()
           await db.commit()

        return new_document
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/applications/{application_id}/documents',response_model=list[DocumentResponse])
async def get_documents(application_id:uuid.UUID,db:AsyncSession=Depends(get_db),user=Depends(get_current_user)):
    try:
        application = await db.get(Application, application_id)
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        can_view = (
            application.user_id == user.id
            or user.role.value in ["assistant_dpgr", "admin_dpgr"]
        )
        if not can_view:
            raise HTTPException(status_code=403, detail="Not authorized")

        res = await db.execute(select(Document).where(Document.application_id == application_id).order_by(Document.uploaded_at.desc()))
        documents = res.scalars().all()
        if not documents:
            raise HTTPException(status_code=404, detail='No document found with this demmende_id')
        return documents
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
   
@router.delete('/document/{idd}')
async def delete_document(idd:uuid.UUID,db:AsyncSession=Depends(get_db),user:User=Depends(get_current_user)):
    try:
        res=await db.execute(select(Document).where(Document.id==idd,Document.user_id==user.id))
        document=res.scalar_one_or_none()
        if not document:
            raise HTTPException(status_code=404,detail='document not found')
        file_path = document.file_path
        if document.document_type == Documents_type.report:# this set the stage_report_submitted to true and set the stage_report_id to the new document id and set the stage_report_submitted_at to the current date and time this is for the front end to know that the report is submitted and it can show the download button for the report and it can also show the date of submission of the report
             app=await db.get(Application,document.application_id)
             if app.status != Status.CORRECTION_NEEDED and app.status != Status.COMPLETED:
                  raise HTTPException(status_code=400,detail="You can't delete a report for an application that is not in correction needed status")
             app.stage_report_submitted = False
             app.stage_report_id = None
             app.stage_report_submitted_at = None
             if app.status == Status.COMPLETED:# if the status is completed it means that the report was submitted and the cs approved the application but now the user want to delete the report so we need to change the status back to approved because the report is deleted and we need to wait for the user to submit a new report and for the cs to approve it again
                 app.status = Status.APPROVED
                 app.completed_at = None
             await db.commit()
        if document.document_type == Documents_type.attestation:# this set the attestation_submitted to true and set the attestation_id to the new document id and set the attestation_submitted_at to the current date and time this is for the front end to know that the attestation is submitted and it can show the download button for the attestation and it can also show the date of submission of the attestation
             if user.role.value != "admin_dpgr":
                 raise HTTPException(status_code=403,detail="Not authorized to delete this document")
             app=await db.get(Application,document.application_id)
             app.attestation_submitted = False
             app.attestation_id = None
             app.attestation_submitted_at = None
             await db.commit()
        await db.delete(document)
        await db.commit()
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass
        return  {"details":"Document deleted succussfuly"}
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/document/{idd}',response_model=DocumentResponse)
async def get_document(idd:uuid.UUID,db:AsyncSession=Depends(get_db),user:User=Depends(get_current_user)):
    try:
        res=await db.execute(select(Document).where(Document.id==idd,Document.user_id==user.id))
        document=res.scalar_one_or_none()
        if not document:
            raise HTTPException(status_code=404,detail='document not found')
        return document
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/document/{idd}/download")
async def download_document(idd:uuid.UUID,db:AsyncSession=Depends(get_db),user:User=Depends(get_current_user)):
    try:
        res=await db.execute(
            select(Document)
            .options(joinedload(Document.application))
            .where(Document.id==idd)
        )
        document=res.scalar_one_or_none()
        if not document:
            raise HTTPException(status_code=404,detail='document not found')
        can_download = (
            document.user_id == user.id
            or user.role.value in ["assistant_dpgr", "admin_dpgr"]
        )
        if not can_download:
            raise HTTPException(status_code=403, detail="Not authorized")
        if not os.path.exists(document.file_path):
              raise HTTPException(status_code=404, detail="file missing on server")
        media_type = document.mime_type or "application/octet-stream"
        return FileResponse(
            path=document.file_path,
            filename=document.file_name,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{document.file_name}"'}
        )
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))




@router.get('/applications/{application_id}/documents/downloads')
async def downlods_demende_documents(application_id:uuid.UUID,db:AsyncSession=Depends(get_db),user:User=Depends(get_current_user)):
    try:
        application_result = await db.execute(
            select(Application)
            .options(joinedload(Application.user))
            .where(Application.id == application_id)
        )
        application = application_result.scalars().first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        can_download = (
            application.user_id == user.id
            or user.role.value in ["assistant_dpgr", "admin_dpgr"]
        )
        if not can_download:
            raise HTTPException(status_code=403, detail="Not authorized")

        res = await db.execute(
            select(Document).options(
                joinedload(Document.application).joinedload(Application.user)
            ).where(
                Document.application_id == application_id
            ).order_by(Document.uploaded_at.desc())
        )
        documents = res.scalars().all()

        if not documents:
            raise HTTPException(status_code=404, detail='No document found with this demmende_id')

        zip_path = os.path.join(tempfile.gettempdir(), f"{application_id}_{uuid.uuid4()}.zip")
        with zipfile.ZipFile(zip_path, "w") as zipf:
            for doc in documents:
                if os.path.exists(doc.file_path):
                    zipf.write(doc.file_path, arcname=doc.file_name)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"documents_{application.user.username}_{application.user.lastname}_{timestamp}.zip"
        return FileResponse(zip_path, filename=filename)

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
   

@router.get('/application/documents')
async def downlaod_all_user_docs(
    session_id: uuid.UUID | None = Query(None),
    db:AsyncSession=Depends(get_db),
    user:User=Depends(get_current_user)
):
   try:
     if user.role.value not in ["admin_dpgr", "assistant_dpgr", "super_admin"]:
        raise HTTPException(status_code=403, detail='Unauthorized')
     
     query = select(Document).options(
        joinedload(Document.application).options(
            joinedload(Application.user),
            joinedload(Application.session)
        )
     )
     
     if session_id:
         query = query.join(Document.application).where(Application.session_id == session_id)

     result = await db.execute(query)

     documents = result.scalars().all()
     if not documents:
         raise HTTPException(status_code=404, detail="No documents found")

     year = datetime.utcnow().year

     z = zipstream.ZipFile(mode="w", compression=zipstream.ZIP_DEFLATED)

     for doc in documents:
         user = doc.application.user
         session=doc.application.session

         folder = f"{user.username}_{user.lastname}"
         arcname = f"{folder}/{doc.file_name}"

         if os.path.exists(doc.file_path):
             z.write(doc.file_path, arcname)

     return StreamingResponse(
         z,
         media_type="application/zip",
         headers={
            "Content-Disposition": f'attachment; filename="{session.name}.zip" if session_id and session else "all_documents.zip"'
         }
      )
   except HTTPException:
     await db.rollback()
     raise
   except Exception as e:
     await db.rollback()
     raise HTTPException(status_code=500, detail=str(e))
