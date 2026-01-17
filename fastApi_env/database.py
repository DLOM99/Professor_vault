from sqlmodel import SQLModel, create_engine, Session
from fastapi import Depends
import os


sqlite_file_name = "professor_vault.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"



