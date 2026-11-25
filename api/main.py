from fastapi import FastAPI
app = FastAPI(
    title="Future Portfolio API",
    version="1.0",
)


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the Future Portfolio API"}


@app.get("/api/greet")
def greet():
    return {"greeting1": "Good morning",
            "greeting2": "Good afternoon"}


import json
from datetime import datetime, date
from typing import Literal


from fastapi import FastAPI, HTTPException, Query, Response


from db import connect, fetch_all, execute


app = FastAPI(
    title="Future Portfolio API",
    version="2.0",
    description="Ananya Rao's career from future_portfolio_db.",
)


category = Literal["company","industry","community"]


#shared function


def list_from_view(response: Response, view: str, where: list[str], params: list,
                   order: str, page: int, limit:int):
    """One page of rows from a view, with X-Total-Count for the whole filter.


    view, where and order are fixed text from this file; params carries every value.
    """
    where_sql = f" WHERE {' AND '.join(where)}" if where else ""
    with connect() as conn:
        total = fetch_all(conn, f"SELECT COUNT(*) AS total FROM {view}{where_sql}", params) [0]["total"]
        rows = fetch_all(
            conn,
            f"SELECT * FROM {view}{where_sql} ORDER BY {order} LIMIT %s",
            [*params, limit, (page - 1) * limit],
        )


        response.headers["X-Total-Count"] = str(total)
        return rows


def parse_skills(rows):
    """The skill cloumn is JSON text (JSON_ARRAYAGG); turn it into a list."""
    for row in rows:
        row["skills"] = json.loads(row["skills"]) if row["skills"] else []
        return rows


# @app.get("/api/resume", tags=["Resume"])
# def get_resume():
#     """The whole resume.json document, built from the views on every request."""
#     with connect() as conn:
#         return build_resume(conn)
        


@app.get("/api/profile", tags=["Resume"])
def get_profile():
    """The resume header: name, headline, location, summary, No email."""
    with connect() as conn:
        return fetch_all(conn, "SELECT * FROM v_api_profile")[0]


@app.get("/api/summary", tags=["Resume"])
def get_summary():
    """Carrier at a glance: counts and career years"""
    with connect() as conn:
        return fetch_all(conn, "SELECT * FROM v_api_summary")[0]


# stagger is used ofr api documentation




@app.get("/api/projects", tags=["Projects"])
def get_projects(response: Response, 
                 skill: str | None = Query(None, min_length=1, max_length=100),
                 company: str | None = Query(None, min_length=1, max_length=100),
                 page: int = Query(1, ge=1),
                 limit: int = Query(10, ge=1, le=50)):

    """Project-role pairs with their skills; filter by skill, company or text in the name.
    """

    where, params = [], []
    if skill is not None:
        where.append("JSON_CONTAINS(SKILLS, JSON_QUOTE(%s))")
        params.append(skill)
    if company is not None:
        where.append("company = %s")
        params.append(company)
        rows = list_from_view(response, "v_api_projects", where, params, "project_id, page", page, list)
        return parse_skills(rows)

def build_resume(conn):
    """Assemble the WHOLE resume as one dictionary.

    WHAT: profile + summary + experience + projects + skills + education + awards
          together, plus today's date.
    WHY:  a client (for example a resume web page) can then make ONE request
          instead of seven.
    HOW:  run one query per section against its view and put each result
          under its own key. The same logic as the Module 5 script
          scripts/db_to_json.py, but live from the database.

    Argument:
        conn - an already-open database connection (the caller opens and closes it).
    """
    # Projects need the extra step of turning their skills text into a list.
    projects = parse_skills(fetch_all(conn, "SELECT * FROM v_api_projects ORDER BY project_id"))

    return {
        # date.today().isoformat() -> "2026-11-24". Tells readers how fresh the data is.
        "generated_at": date.today().isoformat(),

        # [0] = "take the first row". profile and summary have only one row each,
        # so we return that single row (a dictionary), not a list of one.
        "profile":    fetch_all(conn, "SELECT * FROM v_api_profile")[0],
        "summary":    fetch_all(conn, "SELECT * FROM v_api_summary")[0],

        # DESC = descending = newest first.
        "experience": fetch_all(conn, "SELECT * FROM v_api_experience ORDER BY start_date DESC"),
        "projects":   projects,

        # Most-used skills first; if tied, A-to-Z. A second sort column keeps
        # the order the same every time.
        "skills":     fetch_all(conn, "SELECT * FROM v_api_skills ORDER BY project_count DESC, skill"),
        "education":  fetch_all(conn, "SELECT * FROM v_api_education ORDER BY start_year DESC"),
        "awards":     fetch_all(conn, "SELECT * FROM v_api_awards ORDER BY year DESC, id"),
    }


@app.get(
    "/api/resume",
    tags=["Resume"],
    summary="Get the complete resume document",
    description="Builds the whole resume (profile, summary, experience, projects, skills, education, awards) from the views on every request, so it is always current. The response can be large; prefer the specific endpoints when you need one section.",
    responses={200: {"description": "The full resume JSON document."},
               500: {"description": "Database unreachable or a view is missing."}},
)
def get_resume():
    """Return the complete resume in one go.

    WHAT: every section of the portfolio inside one JSON document.
    WHY:  convenient for a client that wants everything with a single request.
    HOW:  open the database and let build_resume() assemble the document.
    """
    with connect() as conn:
        return build_resume(conn)   


@app.get(
    "/api/summary",
    tags=["Summary"],
    summary="Get the complete resume document",
    description="Builds the whole resume (profile, summary, experience, projects, skills, education, awards) from the views on every request, so it is always current. The response can be large; prefer the specific endpoints when you need one section.",
    responses={200: {"description": "The full resume JSON document."},
               500: {"description": "Database unreachable or a view is missing."}},
)
def get_summary():
    """Return the complete resume in one go.

    WHAT: every section of the portfolio inside one JSON document.
    WHY:  convenient for a client that wants everything with a single request.
    HOW:  open the database and let build_resume() assemble the document.
    """
    with connect() as conn:
        return fetch_all(conn)  


@app.get(
    "/api/experience",
    tags=["Experience"],
    summary="lists the work experience.",
    description="returns the experience section of resume ordered by start date desc group by id.",
    responses={200: {"description": "The experience section of resume."},
               500: {"description": "Database unreachable or a view is missing."}},
               )
def get_experience():
    with connect() as conn:
        return fetch_all(conn, "SELECT * FROM v_api_experience ORDER BY start_date DESC, id")


@app.get(
    "/api/skills",
    tags=["skills"],
    summary="lists the work experience.",
    description="returns the experience section of resume ordered by start date desc group by id.",
    responses={200: {"description": "The experience section of resume."},
               500: {"description": "Database unreachable or a view is missing."}},
               )
def get_skills():
    with connect() as conn:
        return fetch_all(conn, "SELECT * FROM v_api_experience ORDER BY start_date DESC, id")


@app.get("/api/awards/{award_id}", tags=["Awards"])
def get_award(awards_id: int):
    """One award by it's id,"""
    with connect() as conn:
        rows = fetch_all(conn, "SELECT * FROM v_api_awards WHERE id = %s", (awards_id,))
    if not rows:
        raise HTTPException(status_code=404, detail=f"No award with id (award_id),")
    return rows[0]


@app.get("/api/projects/{project_id}", tags=["Projects"])
def get_project(project_id: int):
    """One project by it's id,"""
    with connect() as conn:
        rows = fetch_all(conn, "SELECT * FROM v_api_projects WHERE id = %s", (project_id,))
    if not rows:
        raise HTTPException(status_code=404, detail=f"No project with id (project_id),")
    return rows[0]
#==============================================================================================================================================================================
#                                                                     >> // POST // <<
#=============================================================================================================================================================================

from fastapi import FastAPI
from pydantic import BaseModel, Field, ConfigDict, EmailStr

app = FastAPI()

class ProductCreate(BaseModel):
    name: str = Field(min_length=3, max_length=180)
    stock: int = Field(ge=0)

@app.post("/api/products")
def create_products(product: ProductCreate):
    return {"message": "Valid data!", "product": product}

#=============================================================================================================================================================================
#                                                                          //  POST   //
#=============================================================================================================================================================================
from datetime import date, datetime

class MessageIn(BaseModel): 
    """What the contact form sends."""
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    message: str = Field(min_length=1, max_length=2000)




@app.post("/api/messages", status_code=201, tags=["Messages"])
def create_message(body: MessageIn, response: Response): 
    """Send a message from the contact form."""
    with connect(write=True) as conn:
        _, new_id = execute(
            conn, 
            "INSERT INTO contact_messages (name, email, message) VALUES (%s, %s, %s)",
            (body.name, body.email, body.message),
        )
        conn.commit() #autocommit is OFF in the Python connector: no commit, no row 
        sent_at = fetch_all(
            conn, "SELECT * FROM v_owner_messages WHERE id=%s", {new_id,}
        )

#===============================================================================================================================================================================
#                                                                             // PATCH //
#===============================================================================================================================================================================
class MessageOut(BaseModel):
    """What the owner reads back."""
    id: int
    name: str
    email:str
    message:str
    sent_st: datetime
    is_read: bool

class MessagePatch(BaseModel):
    """The only thing th owner changes on a message."""

    is_read: bool


@app.patch("/api/messages/{message_id}", response_model=MessageOut, tags=["Messages"])
def mark_message(message_id: int, body: MessagePatch):
    """Mark a message read or unread."""
    with connect(write=True) as conn:
        execute(
            conn,
            "UPDATE contact_message SET is_read = %s WHERE message_id = %s",
            (body.is_read, message_id),
        )
        conn.commit()
        # Look it up instead of trusting rowcount UPDATE counts rows CHANGED, not rows FOUND.
        rows = fetch_all(conn, "SELECT * FROM v_owner_messages WHERE id = %s", (message_id,))
    if not rows:
        raise HTTPException(status_code=404, detail=f"No message with id {message_id}.")
    return rows[0]
# =============================================================================================================================================================================
#                                                                     //   DELETE   //
#=============================================================================================================================================================================
@app.delete("/api/messgaes/{message_id}", status_code=204, tags=["Messages"])
def delete_message(message_id: int):
    """Delete a message."""
    with connect(Write=True) as conn:
        deleted, _ = execute(conn, "DELETE FROM contact_messages WHERE message_id = %s", (message_id))
        conn.commit()
    if deleted == 0:
        raise HTTPException(status_code=404, detail=f"No message with id {message_id}.")
    return Response(status_code=204)

#==============================================================================================================================================================================
#                                                                     //  PUT  //
#==============================================================================================================================================================================

class MessageOut(BaseModel):
    """What the owner reads back."""
    id: int
    name: str
    email:str
    message:str
    sent_st: datetime
    is_read: bool

class MessagePut(BaseModel):
    """The only thing th owner changes on a message."""

    is_read: bool

@app.put("/api/messages/{message_id}", response_model=MessageOut, tags=["Messages"])
def mark_message(message_id: int, body: MessagePut):
    """Mark a message read or unread."""
    with connect(write=True) as conn:
        execute(
            conn,
            "UPDATE contact_message SET is_read = %s WHERE message_id = %s",
            (body.is_read, message_id),
        )
        conn.commit()
        # Look it up instead of trusting rowcount UPDATE counts rows CHANGED, not rows FOUND.
        rows = fetch_all(conn, "SELECT * FROM v_owner_messages WHERE id = %s", (message_id,))
    if not rows:
        raise HTTPException(status_code=404, detail=f"No message with id {message_id}.")
    return rows[0]

@app.get("/api/projects/{project_id}", tags=["Projects"])
def get_project(project_id: int):
    """One project by it's id,"""
    with connect() as conn:
        rows = fetch_all(conn, "SELECT * FROM v_api_projects WHERE id = %s", (project_id,))
    if not rows:
        raise HTTPException(status_code=404, detail=f"No project with id (project_id),")
    return rows[0]


















    