from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Request
from fastapi.responses import FileResponse ,HTMLResponse
from fastapi.templating import Jinja2Templates
import shutil 

from sqlmodel import Session, select 
import os

import mimetypes
import logging

from models import Folder, Document 
from database import engine, create_db_and_tables, get_session
from contextlib import asynccontextmanager

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger("vault_logger")

templates = Jinja2Templates(directory="templates")


async def lifespan(app: FastAPI):
    create_db_and_tables()
    os.makedirs("storage", exist_ok=True)
    yield


app = FastAPI(lifespan=lifespan)

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, session: Session = Depends(get_session)):
    # 1. Get all folders from the database
    folders = session.exec(select(Folder)).all()
    
    # 2. Hand the folders over to the HTML file
    return templates.TemplateResponse("index.html", {"request": request, "folders": folders})


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
    file : UploadFile = File(...), # Removed 'title: str' as it was redundant
    session : Session = Depends(get_session)
):
    db_folder = session.get(Folder, folder_id)
    if not db_folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # 1. Construct path using os.path.join for cross-platform compatibility
    file_path = os.path.join("storage", db_folder.name, file.filename)

    # 2. Save the physical file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 3. Create the Database Record (The Theory of Persistence)
    new_doc = Document(
        title = file.filename, # Using the original filename as the display title
        file_path = file_path,
        folder_id = folder_id
    )
    
    try:
        session.add(new_doc)
        session.commit()
        session.refresh(new_doc)
    except Exception as e:
        # If the DB fails, we should remove the file we just saved to stay in sync
        if os.path.exists(file_path):
            os.remove(file_path)
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database save failed")

    return {"info": f"File '{file.filename}' saved successfully"}


@app.post("/documents/{document_id}/delete")
def delete_document(document_id: int, session: Session = Depends(get_session)):
    # 1. Fetch metadata from the database
    db_document = session.get(Document, document_id)
    if not db_document:
        logger.warning(f"❌ Delete failed: Document {document_id} not found.")
        raise HTTPException(status_code=404, detail="Document not found")

    # 2. Theory: Physical Asset Cleanup
    # Before removing the record, we must delete the file from the OS storage.
    if os.path.exists(db_document.file_path):
        try:
            os.remove(db_document.file_path)
            logger.info(f"🗑️ Deleted physical file: {db_document.file_path}")
        except Exception as e:
            logger.error(f"Error removing file: {e}")
            # We continue anyway to keep the DB in sync with the missing file
    
    # 3. Theory: Persistence Layer Removal
    # This removes the metadata row from your SQLite table.
    session.delete(db_document)
    session.commit()
    
    logger.info(f"✅ Successfully deleted document record {document_id}")
    return {"message": f"Document '{db_document.title}' has been deleted."}


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
        logger.warning(f"❌ Delete failed: Folder {folder_id} not found.")
        raise HTTPException(status_code=404, detail="Folder not found")
    
    logger.info(f"🗑️ Deleting folder: {db_folder.name}")
    
    folder_path = os.path.join("storage", db_folder.name)
    if  os.path.exists(folder_path) :
       shutil.rmtree(folder_path)

    session.delete(db_folder)
    session.commit()
    logger.info(f"✅ Successfully deleted folder {folder_id}")

    return {"message": f"Folder '{db_folder.name}' and all its files have been deleted."}


@app.get("/documents/{document_id}/view")
def view_document(document_id: int, session: Session = Depends(get_session)):
    db_document = session.get(Document, document_id)
    if not db_document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if not os.path.exists(db_document.file_path):
        raise HTTPException(status_code=404, detail="Physical file missing")

    # 1. Precise MIME Detection
    mime_type, _ = mimetypes.guess_type(db_document.file_path)
    mime_type = mime_type or "application/octet-stream"
    
    # 2. Get file size for the Content-Length header
    file_size = os.path.getsize(db_document.file_path)

    # 3. Explicit Header Control
    # We use 'headers' to provide extra metadata to the browser
    headers = {
        "Content-Disposition": f'inline; filename="{db_document.title}"',
        "Content-Length": str(file_size),
        "Accept-Ranges": "bytes"  # Tells browser we support skipping through pages
    }

    return FileResponse(
        path=db_document.file_path, 
        media_type=mime_type,
        headers=headers
    )
                  
@app.get("/folders/{folder_id}", response_class=HTMLResponse)
def view_folder_page(folder_id: int, request: Request, session: Session = Depends(get_session)):
    # 1. Fetch the folder
    db_folder = session.get(Folder, folder_id)
    if not db_folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    # 2. Fetch all documents belonging to this folder
    statement = select(Document).where(Document.folder_id == folder_id)
    db_documents = session.exec(statement).all()

    # 3. Render the template
    return templates.TemplateResponse(
        "folder_detail.html", 
        {"request": request, "folder": db_folder, "documents": db_documents}
    )