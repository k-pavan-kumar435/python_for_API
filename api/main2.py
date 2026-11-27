# import os
# from datetime import date, datetime
# import json
# from typing import Literal

# from fastapi import Depends, FastAPI, HTTPException, Query, Response
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel, ConfigDict, EmailStr, Field

# from db import connect, fetch_all, execute
# from github import router as github_router
# from security import required_owner

# app = FastAPI(
#     title="Future Portfolio API",
#     version="1.0",
# )

# # ---------- CORS (must allow every method you use, incl. PUT) ----------
# ALLOWED_ORIGINS = [
#     origin.strip()
#     for origin in os.getenv(
#         "CORS_ORIGINS", "http://127.0.0.1:5500,http://localhost:5500"
#     ).split(",")
# ]
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=ALLOWED_ORIGINS,
#     allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
#     allow_headers=["Content-Type", "X-API-Key"],
#     expose_headers=["X-Total-Count", "Location"],
# )

# app.include_router(github_router)

# OWNER = [Depends(required_owner)]
# category = Literal["company", "industry", "community"]


# # ---------- Simple demo endpoints ----------

# @app.get("/api/hello")
# def hello():
#     return {"message": "Hello from the Future Portfolio API"}


# @app.get("/api/greet")
# def greet():
#     return {"greeting1": "Good morning", "greeting2": "Good afternoon"}


# # ---------- Shared helpers ----------

# def list_from_view(response: Response, view: str, where: list[str], params: list,
#                    order: str, page: int, limit: int):
#     """One page of rows from a view, with X-Total-Count for the whole filter.

#     view, where and order are fixed text from this file; params carries every value.
#     """
#     where_sql = f" WHERE {' AND '.join(where)}" if where else ""
#     with connect() as conn:
#         total = fetch_all(conn, f"SELECT COUNT(*) AS total FROM {view}{where_sql}", params)[0]["total"]
#         rows = fetch_all(
#             conn,
#             f"SELECT * FROM {view}{where_sql} ORDER BY {order} LIMIT %s, %s",
#             [*params, (page - 1) * limit, limit],
#         )
#         response.headers["X-Total-Count"] = str(total)
#         return rows


# def parse_skills(rows):
#     """The skills column is JSON text (JSON_ARRAYAGG); turn it into a list."""
#     for row in rows:
#         row["skills"] = json.loads(row["skills"]) if row.get("skills") else []
#     return rows


# def build_resume(conn):
#     """Assemble the WHOLE resume as one dictionary (one request instead of seven)."""
#     projects = parse_skills(fetch_all(conn, "SELECT * FROM v_api_projects ORDER BY project_id"))

#     return {
#         "generated_at": date.today().isoformat(),
#         "profile": fetch_all(conn, "SELECT * FROM v_api_profile")[0],
#         "summary": fetch_all(conn, "SELECT * FROM v_api_summary")[0],
#         "experience": fetch_all(conn, "SELECT * FROM v_api_experience ORDER BY start_date DESC"),
#         "projects": projects,
#         "skills": fetch_all(conn, "SELECT * FROM v_api_skills ORDER BY project_count DESC, skill"),
#         "education": fetch_all(conn, "SELECT * FROM v_api_education ORDER BY start_year DESC"),
#         "awards": fetch_all(conn, "SELECT * FROM v_api_awards ORDER BY year DESC, id"),
#     }


# # ---------- Resume (GET) ----------

# @app.get(
#     "/api/resume",
#     tags=["Resume"],
#     summary="Get the complete resume document",
#     description="Builds the whole resume (profile, summary, experience, projects, skills, "
#                 "education, awards) from the views on every request, so it is always current.",
#     responses={200: {"description": "The full resume JSON document."},
#                500: {"description": "Database unreachable or a view is missing."}},
# )
# def get_resume():
#     with connect() as conn:
#         return build_resume(conn)


# @app.get("/api/profile", tags=["Resume"])
# def get_profile():
#     """The resume header: name, headline, location, summary. No email."""
#     with connect() as conn:
#         return fetch_all(conn, "SELECT * FROM v_api_profile")[0]


# @app.get("/api/summary", tags=["Resume"])
# def get_summary():
#     """Career at a glance: counts and career years."""
#     with connect() as conn:
#         return fetch_all(conn, "SELECT * FROM v_api_summary")[0]


# @app.get(
#     "/api/experience",
#     tags=["Experience"],
#     summary="List the work experience.",
#     description="Returns the experience section of the resume, newest first.",
#     responses={200: {"description": "The experience section of the resume."},
#                500: {"description": "Database unreachable or a view is missing."}},
# )
# def get_experience():
#     with connect() as conn:
#         return fetch_all(conn, "SELECT * FROM v_api_experience ORDER BY start_date DESC, id")


# @app.get(
#     "/api/skills",
#     tags=["Skills"],
#     summary="List the skills.",
#     description="Returns the skills section, most-used first.",
#     responses={200: {"description": "The skills section of the resume."},
#                500: {"description": "Database unreachable or a view is missing."}},
# )
# def get_skills():
#     with connect() as conn:
#         return fetch_all(conn, "SELECT * FROM v_api_skills ORDER BY project_count DESC, skill")


# @app.get("/api/projects", tags=["Projects"])
# def get_projects(response: Response,
#                  skill: str | None = Query(None, min_length=1, max_length=100),
#                  company: str | None = Query(None, min_length=1, max_length=100),
#                  page: int = Query(1, ge=1),
#                  limit: int = Query(10, ge=1, le=50)):
#     """Project-role pairs with their skills; filter by skill or company."""
#     where, params = [], []
#     if skill is not None:
#         where.append("JSON_CONTAINS(skills, JSON_QUOTE(%s))")
#         params.append(skill)
#     if company is not None:
#         where.append("company = %s")
#         params.append(company)
#     rows = list_from_view(response, "v_api_projects", where, params, "project_id", page, limit)
#     return parse_skills(rows)


# # (the duplicate /api/projects/{project_id} that was further down has been removed)
# @app.get("/api/projects/{project_id}", tags=["Projects"])
# def get_project(project_id: int):
#     """One project by its id."""
#     with connect() as conn:
#         rows = fetch_all(conn, "SELECT * FROM v_api_projects WHERE id = %s", (project_id,))
#     if not rows:
#         raise HTTPException(status_code=404, detail=f"No project with id {project_id}.")
#     return parse_skills(rows)[0]


# @app.get("/api/awards/{award_id}", tags=["Awards"])
# def get_award(award_id: int):
#     """One award by its id."""
#     with connect() as conn:
#         rows = fetch_all(conn, "SELECT * FROM v_api_awards WHERE id = %s", (award_id,))
#     if not rows:
#         raise HTTPException(status_code=404, detail=f"No award with id {award_id}.")
#     return rows[0]


# # =========================== POST ===========================

# class ProductCreate(BaseModel):
#     name: str = Field(min_length=3, max_length=180)
#     stock: int = Field(ge=0)


# @app.post("/api/products")
# def create_products(product: ProductCreate):
#     return {"message": "Valid data!", "product": product}


# class MessageIn(BaseModel):
#     """What the contact form sends."""
#     model_config = ConfigDict(str_strip_whitespace=True)

#     name: str = Field(min_length=1, max_length=100)
#     email: EmailStr  # needs: pip install email-validator
#     message: str = Field(min_length=1, max_length=2000)


# @app.post("/api/messages", status_code=201, tags=["Messages"])
# def create_message(body: MessageIn):
#     """Send a message from the contact form."""
#     with connect(write=True) as conn:
#         _, new_id = execute(
#             conn,
#             "INSERT INTO contact_messages (name, email, message) VALUES (%s, %s, %s)",
#             (body.name, body.email, body.message),
#         )
#         conn.commit()  # autocommit is OFF in the Python connector: no commit, no row
#     return {"id": new_id, "message": "Message sent successfully."}


# # =========================== owner: read / update / delete ===========================

# class MessageOut(BaseModel):
#     """What the owner reads back."""
#     id: int
#     name: str
#     email: str
#     message: str
#     sent_at: datetime   # was "sent_st" (typo): must match the view's column
#     is_read: bool


# class MessagePatch(BaseModel):
#     """The only thing the owner changes on a message."""
#     is_read: bool


# def _set_read(message_id: int, is_read: bool):
#     with connect(write=True) as conn:
#         execute(
#             conn,
#             "UPDATE contact_messages SET is_read = %s WHERE message_id = %s",  # table name fixed (was contact_message)
#             (is_read, message_id),
#         )
#         conn.commit()
#         # Look it up instead of trusting rowcount: UPDATE counts rows CHANGED, not rows FOUND.
#         rows = fetch_all(conn, "SELECT * FROM v_owner_messages WHERE id = %s", (message_id,))
#     if not rows:
#         raise HTTPException(status_code=404, detail=f"No message with id {message_id}.")
#     return rows[0]


# @app.get("/api/messages", response_model=list[MessageOut], tags=["Messages"], dependencies=OWNER)
# def list_messages(
#     response: Response,
#     page: int = Query(1, ge=1),
#     limit: int = Query(50, ge=1, le=50),
# ):
#     """Owner only: newest first."""
#     return list_from_view(response, "v_owner_messages", [], [], "sent_at DESC, id DESC", page, limit)


# @app.patch("/api/messages/{message_id}", response_model=MessageOut, tags=["Messages"], dependencies=OWNER)
# def patch_message(message_id: int, body: MessagePatch):
#     """Mark a message read or unread."""
#     return _set_read(message_id, body.is_read)


# @app.put("/api/messages/{message_id}", response_model=MessageOut, tags=["Messages"], dependencies=OWNER)
# def put_message(message_id: int, body: MessagePatch):
#     """Same change via PUT (kept for practice)."""
#     return _set_read(message_id, body.is_read)


# @app.delete("/api/messages/{message_id}", status_code=204, tags=["Messages"], dependencies=OWNER)
# def delete_message(message_id: int):
#     """Delete a message."""
#     with connect(write=True) as conn:                       # was Write=True
#         deleted, _ = execute(
#             conn,
#             "DELETE FROM contact_messages WHERE message_id = %s",
#             (message_id,),                                  # was (message_id) - not a tuple
#         )
#         conn.commit()
#     if deleted == 0:
#         raise HTTPException(status_code=404, detail=f"No message with id {message_id}.")
#     return Response(status_code=204)