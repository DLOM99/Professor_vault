from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
import shutil 

from sqlmodel import Session, select 
import os

import mimetypes




from models import Folder, Document 
from database import engine, create_db_and_tables, get_session
from contextlib import asynccontextmanager

async def lifespan(app: FastAPI):
    create_db_and_tables()
    os.makedirs("storage", exist_ok=True)
    yield


app = FastAPI(lifespan=lifespan)

@app.post("/folders/")
def create_folder(folder_name : str, session : Session = Depends(get_session)):
    new_folder = Folder(name = folder_name)
    session.add(new_folder)
    session.commit()
    session.refresh(new_folder)

    physical_path =os.path.join("storage",folder_name)
    os.makedirs(physical_path, exist_ok=True)

    return {"message": "Folder created successfully", "folder": new_folder}


@app.post("/folders/{folder_id}/upload")
def upload_file_to_folder(
    folder_id: int,
    title : str,
    file : UploadFile = File(...),
    session : Session = Depends(get_session)
):
    # STEP 1: Verification (Find the folder)
    db_folder = session.get(Folder, folder_id)
    if not db_folder :
        raise HTTPException(status_code=404, detail="Folder not found")
    

    # STEP 2: Map Making (Define the path)
    file_path = os.path.join("storage", db_folder.name, file.filename)

    # STEP 3: Physical Move (Save to Disk)

    with open(file_path, "wb") as buffer :
        shutil.copyfileobj(file.file, buffer)

    # STEP 4: Recording (The Banker's Job)
    new_doc = Document(
        title = file.filename,
        file_path = file_path,
        folder_id = folder_id

    )
    session.add(new_doc)
    session.commit()
    session.refresh(new_doc)

    return {"info": f"File '{file.filename}' saved to {db_folder.name}"}


@app.get("/folders/")
def get_all_folders(session: Session = Depends(get_session)):
    # 1. Ask the Banker to find all Folder records
    #session.exec(select(Folder)).all()

    statement  = select(Folder)

    result = session.exec(statement)

    all_folders = result.all()

    return all_folders

@app.get("/folders/{folder_id}/files/")
def get_all_files(folder_id: int, session: Session = Depends(get_session)):

    db_folder = session.get(Folder,folder_id)

    if not db_folder :
        raise HTTPException(status_code=404, detail="Folder not found")

    

    statement = select(Document).where( Document.folder_id == folder_id)

    result = session.exec(statement)

    folder_files = result.all()

    return folder_files

@app.post("/folders/{folder_id}/delete")
def delete_folder(folder_id: int, session: Session = Depends(get_session)):
    
    db_folder = session.get(Folder, folder_id)
    if not db_folder :
        raise HTTPException(status_code=404, detail="Folder not found")
    
    folder_path = os.path.join("storage", db_folder.name)
    if  os.path.exists(folder_path) :
       shutil.rmtree(folder_path)

    session.delete(db_folder)
    session.commit()

    return {"message": f"Folder '{db_folder.name}' and all its files have been deleted."}


@app.get("/documents/{document_id}/view")
def view_document(document_id: int, session: Session = Depends(get_session)):
    #Find document
    db_document = session.get(Document,document_id)
    if not db_document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    mime_type, _ = mimetypes.guess_type(db_document.file_path)

    if not mime_type:
        mime_type = "application/octet-stream"
    
    if not os.path.exists(db_document.file_path):
        raise HTTPException(status_code=404, detail="Physical file missing from storage")
    
    # media_type="application/pdf" helps the browser know to open it in a viewer
    return FileResponse(

        path=db_document.file_path, 
        filename=db_document.title,
        media_type=mime_type

    )
                  
