import requests
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
import time

FRIENDLI_URL = "https://api.friendli.ai/dedicated/v1/chat/completions"
FRIENDLI_TOKEN = "flp_HawdbUMpop45f4YtcyKbgy8abUqUnfDohAn2QCMgNQK98"
MODEL_ID = "dep4w7ty5uot0v4"
# ---------------------------
# Friendli API Call Function
# ---------------------------
def call_friendli(prompt: str) -> str:
    try:
        headers = {
            "Authorization": f"Bearer {FRIENDLI_TOKEN}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": MODEL_ID,
            "messages": [{"role": "user", "content": prompt}],
        }
        resp = requests.post(FRIENDLI_URL, headers=headers, json=payload, timeout=60)
        print("DEBUG Friendli Response:", resp.status_code, resp.text)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except requests.exceptions.HTTPError as e:
        return f"[ERROR] HTTP error: {str(e)}"
    except requests.exceptions.RequestException as e:
        return f"[ERROR] Request failed: {str(e)}"
    except Exception as e:
        return f"[ERROR] Unexpected API error: {str(e)}"

# ---------------------------
# Database Setup
# ---------------------------
db_uri = "mysql+mysqlconnector://root:laasya123@localhost:3306/chinook"
db = SQLDatabase.from_uri(db_uri)

def get_schema(_=None):
    try:
        return db.get_table_info()
    except Exception as e:
        return f"[ERROR] Could not fetch schema: {str(e)}"

def run_query_sql(query, retries=2):
    if isinstance(query, dict):
        query = query.get("query", "")
    query = query.replace("```sql", "").replace("```", "").strip()

    for attempt in range(retries):
        try:
            return db.run(query)
        except Exception as e:
            if "1064" in str(e) or "syntax" in str(e).lower():
                print(f"[WARNING] SQL syntax error. Retrying... (Attempt {attempt+1})")
                correction_prompt = f"The previous SQL failed with error: {e}. Please correct it and return only the fixed SQL."
                query = call_friendli(correction_prompt)
            else:
                return f"[ERROR] SQL Execution failed: {str(e)}"
    return f"[ERROR] Could not execute query after {retries} retries."


# ---------------------------
# Prompts
# ---------------------------
sql_prompt = ChatPromptTemplate.from_template(
    """You are a helpful assistant generating SQL queries for a MySQL database.
Use only the tables and columns listed below. Do not guess table or column names. 
Join tables using appropriate foreign keys. Always prefer explicit joins and complete column names.
Avoid using aliases or abbreviations. The query should be complete and executable.

--- SCHEMA ---
Artist(ArtistId, Name)
Album(AlbumId, Title, ArtistId)
Track(TrackId, Name, AlbumId, MediaTypeId, GenreId, Composer, Milliseconds, Bytes, UnitPrice)
InvoiceLine(InvoiceLineId, InvoiceId, TrackId, UnitPrice, Quantity)
Genre(GenreId, Name)
MediaType(MediaTypeId, Name)
Customer(CustomerId, FirstName, LastName, Email, SupportRepId)
Employee(EmployeeId, FirstName, LastName, Title, ReportsTo)
Invoice(InvoiceId, CustomerId, InvoiceDate, BillingAddress, BillingCity, BillingState, BillingCountry, BillingPostalCode, Total)

--- EXAMPLES ---
Q: What genre has the most tracks?
A: SELECT g.Name, COUNT(*) AS TrackCount 
   FROM Track t 
   JOIN Genre g ON t.GenreId = g.GenreId 
   GROUP BY g.GenreId 
   ORDER BY TrackCount DESC 
   LIMIT 1;

Q: What album is the most popular?
A: SELECT alb.Title, COUNT(*) AS Purchases 
   FROM InvoiceLine il 
   JOIN Track t ON il.TrackId = t.TrackId 
   JOIN Album alb ON t.AlbumId = alb.AlbumId 
   GROUP BY alb.AlbumId 
   ORDER BY Purchases DESC 
   LIMIT 1;

QUESTION : 
{question}

SQL QUERY:
"""
)

final_prompt = ChatPromptTemplate.from_template(
    """You are a helpful assistant. Given the database schema, a user question, the SQL query used to answer it, and the response from the database, generate a concise and accurate natural language answer. 
Use only the information provided in the SQL response. Do not make assumptions.
Database name: chinook
Artist(ArtistId, Name)
Album(AlbumId, Title, ArtistId)
Track(TrackId, Name, AlbumId, MediaTypeId, GenreId, Composer, Milliseconds, Bytes, UnitPrice)
InvoiceLine(InvoiceLineId, InvoiceId, TrackId, UnitPrice, Quantity)
Genre(GenreId, Name)
MediaType(MediaTypeId, Name)
Customer(CustomerId, FirstName, LastName, Email, SupportRepId)
Employee(EmployeeId, FirstName, LastName, Title, ReportsTo)
Invoice(InvoiceId, CustomerId, InvoiceDate, BillingAddress, BillingCity, BillingState, BillingCountry, BillingPostalCode, Total)

QUESTION : {question}
SQL QUERY : {query}
SQL RESPONSE : {response}
ANSWER : 
"""
)

# ---------------------------
# Chains
# ---------------------------
generate_sql_chain = (
    {"schema": RunnableLambda(get_schema), "question": RunnablePassthrough()}
    | sql_prompt
    | RunnableLambda(lambda pv: call_friendli(pv.to_string()))
    | StrOutputParser()
    | RunnableLambda(lambda sql: {"query": sql})
)

full_chain = (
    {
        "question": RunnablePassthrough(),
        "schema": RunnableLambda(get_schema),
        "query": generate_sql_chain,
    }
    | RunnableLambda(lambda d: {**d, "response": run_query_sql(d["query"]["query"])})
    | final_prompt
    | RunnableLambda(lambda pv: call_friendli(pv.to_string()))
    | StrOutputParser()
)
