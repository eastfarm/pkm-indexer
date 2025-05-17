from fastapi import FastAPI
from pydantic import BaseModel
# Fix the import for WsgiDAVApp
from wsgidav import WsgiDAVApp  # Changed from wsgidav.wsgidav_app import WSGIDavApp
from fastapi.middleware.wsgi import WSGIMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from organize import organize_files
from index import indexKB, searchKB
import os
import frontmatter
import shutil
import re

app = FastAPI()
scheduler = AsyncIOScheduler()

class Query(BaseModel):
    query: str

class File(BaseModel):
    file: dict

@app.post("/search")
async def search(query: Query):
    results = await searchKB(query.query)
    return {"response": results}

@app.get("/staging")
async def get_staging():
    staging = "pkm/Staging"
    os.makedirs(staging, exist_ok=True)
    files = []
    for md_file in [f for f in os.listdir(staging) if f.endswith(".md")]:
        with open(os.path.join(staging, md_file), "r", encoding="utf-8") as f:
            post = frontmatter.load(f)
            files.append({
                "name": md_file,
                "content": post.content,
                "metadata": post.metadata
            })
    return {"files": files}

@app.post("/approve")
async def approve(file: File):
    staging = "pkm/Staging"
    areas = "pkm/Areas"
    inbox = "pkm/Inbox"
    file_data = file.file
    md_file = file_data["name"]
    content = file_data["content"]
    metadata = file_data["metadata"]
    category = metadata.get("category", "General")
    pdf_name = metadata.get("pdf", "")
    pdf_path = os.path.join(staging, pdf_name) if pdf_name else ""
    if re.search(r"# Reviewed: true", content, re.IGNORECASE):
        dest_dir = os.path.join(areas, category)
        os.makedirs(dest_dir, exist_ok=True)
        dest_md_file = os.path.join(dest_dir, md_file)
        post = frontmatter.Post(content=content, **metadata)
        with open(os.path.join(staging, md_file), "w", encoding="utf-8") as f:
            frontmatter.dump(post, f)
        shutil.move(os.path.join(staging, md_file), dest_md_file)
        if pdf_name and os.path.exists(pdf_path):
            dest_pdf_file = os.path.join(dest_dir, pdf_name)
            shutil.move(pdf_path, dest_pdf_file)
        inbox_pdf = os.path.join(inbox, pdf_name)
        if pdf_name and os.path.exists(inbox_pdf):
            os.remove(inbox_pdf)
        return {"status": f"Approved {md_file}"}
    return {"status": "Not approved: # Reviewed: false"}

@app.post("/organize")
async def manual_organize():
    await organize_files()
    return {"status": "Organized"}

@app.on_event("startup")
async def startup_event():
    await indexKB()
    scheduler.add_job(organize_files, "cron", hour=2)
    scheduler.start()

dav_config = {
    "host": "0.0.0.0",
    "port": 8001,
    "root": "pkm",
    "provider_mapping": {"/": "pkm"},
    "simple_dc": {
        "user_mapping": {
            "*": {
                os.getenv("WEBDAV_USERNAME", "pkmuser"): {
                    "password": os.getenv("WEBDAV_PASSWORD", "secret"),
                    "roles": ["admin"]
                }
            }
        }
    }
}
# Use correct class name WsgiDAVApp instead of WSGIDavApp
dav_app = WsgiDAVApp(dav_config)
app.mount("/dav", WSGIMiddleware(dav_app))
