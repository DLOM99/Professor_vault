from sqlmodel import SQLModel, Field , Relationship
from datetime import date
from typing import List, Optional 


class Folder(SQLModel, table=True):
    id : Optional[int] = Field(default=None, primary_key=True)

    name : str = Field(index=True)
    created_at : date = Field(default_factory=date.today)


    documents:List["Document"] = Relationship(back_populates="folder")
class Document(SQLModel, table=True):
    # Primary key
    id : Optional[int] = Field(default=None, primary_key=True)


    # metadata 
    title : str = Field(index=True)
    file_path : str 
# The "Link" to the folder
    folder_id: int = Field(foreign_key="folder.id")
    folder: Folder = Relationship(back_populates="documents")
