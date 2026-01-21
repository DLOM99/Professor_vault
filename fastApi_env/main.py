from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
import shutil 
from sqlmodel import Session
import os



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
        title = title,
        file_path = file_path,
        folder_id = folder_id

    )
    session.add(new_doc)
    session.commit()
    session.refresh(new_doc)

    return {"info": f"File '{file.filename}' saved to {db_folder.name}"}





