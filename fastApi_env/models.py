from sqlmodel import SQLModel, Field, Relationship
from datetime import date
from typing import List, Optional 

class Folder(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    created_at: date = Field(default_factory=date.today)

    # THEORY: The 'cascade_delete' parameter tells SQLAlchemy to 
    # emit DELETE commands for all related documents when this folder is deleted.
    documents: List["Document"] = Relationship(
        back_populates="folder", 
        cascade_delete=True
    )

class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    file_path: str 
    
    # THEORY: 'ondelete="CASCADE"' is a database-level instruction.
    # It tells SQLite: "If the parent row is deleted, wipe this row too."
    folder_id: int = Field(
        foreign_key="folder.id", 
        ondelete="CASCADE",
        nullable=False  # Ensures a document cannot exist without a folder
    )
    
    folder: "Folder" = Relationship(back_populates="documents")