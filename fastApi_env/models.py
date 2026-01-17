from sqlmodel import SQLModel, Field 
from datetime import date
from typing import Optional 

class Document(SQLModel, table=True):
    # Primary key
    id : Optional[int] = Field(default=None, primary_key=True)


    # metadata 
    title : str = Field(index=True)
    category: str 
    author_type: str 

    # info tracking 
    upload_date : date

    #file management 
    file_name: str 
    file_path : str 
