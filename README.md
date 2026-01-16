# 🏛️ Professor Vault

A streamlined, private document management system built for university professors to classify, archive, and retrieve academic work.

## 🎯 Overview
Professor Vault is a "local-first" software solution designed to help academics manage the vast amounts of data they handle daily. Instead of a complex cloud system, this tool allows for manual classification of documents (PDFs, PPTs, and Papers) by authorship and date, ensuring that research and student work are never mixed and are always easy to find.

## ✨ Features
- **Manual Classification:** Categorize files as *Memoire*, *Dissertation*, *Peer-Reviewed Paper*, or *Presentation*.
- **Ownership Tracking:** Tag files as "Self" (Professor's own research) or "Student" work.
- **Chronological Access:** Built-in logic to filter and view files by **Year**, **Month**, or **Day**.
- **Metadata Search:** Search through your library by title or category.
- **Local Storage:** Files remain on your machine for maximum privacy and security.

## 🛠️ Tech Stack
| Layer | Technology |
| :--- | :--- |
| **Backend** | FastAPI (Python) |
| **Database** | SQLite + SQLModel (ORM) |
| **Frontend** | Next.js + Tailwind CSS |
| **File Handling** | Python Multi-part + Shutil |

## 📂 Project Structure
```text
professor_vault/
├── backend/
│   ├── main.py          # FastAPI endpoints and file logic
│   ├── database.py      # SQLite connection & session management
│   ├── models.py        # SQLModel schemas
│   └── storage/         # Physical file archive (Local)
├── frontend/            # Next.js Dashboard
└── README.md
