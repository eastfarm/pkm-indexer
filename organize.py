import os
import frontmatter
import pdfplumber
import shutil
from datetime import datetime
from openai import OpenAI

def log_error(message, file_name=""):
    logs = "pkm/Logs"
    os.makedirs(logs, exist_ok=True)
    log_file = os.path.join(logs, f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"# Error at {datetime.now().isoformat()}\n")
        f.write(f"File: {file_name}\n")
        f.write(f"Message: {message}\n")
        f.write("Action: Review file in PKM/Staging or retry processing.\n\n")

def extract_pdf_text(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "".join(page.extract_text() or "" for page in pdf.pages)
            if len(text) < 100:
                log_error("Low text yield; possible scanned PDF", pdf_path)
            return text
    except Exception as e:
        log_error(f"PDF extraction failed: {e}", pdf_path)
        return ""

def chunk_text(text, max_length=2000):
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]

def call_openai_api(prompt):
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for a PKM system. Summarize text, generate tags, and suggest a category."},
                {"role": "user", "content": f"Summarize and tag: {prompt}\nReturn JSON: {{'summary': str, 'tags': list, 'category': str}}"}
            ],
            max_tokens=500,
            temperature=0.7
        )
        result = response.choices[0].message.content
        import json
        return json.loads(result)
    except Exception as e:
        log_error(f"OpenAI API failed: {e}")
        return {"summary": "TODO", "tags": [], "category": ""}

def create_markdown(pdf_path, base_name):
    return frontmatter.Post(
        content=f"# {base_name}\nPDF report saved at: [{os.path.basename(pdf_path)}]({os.path.basename(pdf_path)})",
        **{
            "title": base_name,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "tags": [],
            "category": "Unassigned",
            "pdf": os.path.basename(pdf_path)
        }
    )

async def organize_files():
    inbox = "pkm/Inbox"
    staging = "pkm/Staging"
    os.makedirs(inbox, exist_ok=True)
    os.makedirs(staging, exist_ok=True)
    files = os.listdir(inbox)
    markdown_files = [f for f in files if f.endswith(".md")]
    pdf_files = [f for f in files if f.endswith(".pdf")]
    processed = set()
    for md_file in markdown_files:
        if md_file in processed:
            continue
        try:
            with open(os.path.join(inbox, md_file), "r", encoding="utf-8") as f:
                post = frontmatter.load(f)
                content = post.content
                pdf_name = post.metadata.get("pdf", "")
                pdf_path = os.path.join(inbox, pdf_name) if pdf_name else ""
                pdf_text = ""
                if pdf_name and os.path.exists(pdf_path):
                    pdf_text = extract_pdf_text(pdf_path)
                    processed.add(pdf_name)
                text_to_process = pdf_text or content
                chunks = chunk_text(text_to_process, max_length=2000)
                summaries = []
                tags = set()
                category = post.metadata.get("category", "General")
                for chunk in chunks:
                    response = call_openai_api(chunk)
                    summaries.append(response.get("summary", "TODO"))
                    tags.update(response.get("tags", []))
                    if response.get("category"):
                        category = response.get("category")
                post.metadata["tags"] = list(tags)
                post.metadata["category"] = category
                summary = "\n\n## Summary\n" + "\n".join(summaries)
                post.content = content + summary + "\n\n# Reviewed: false"
                dest_md_file = os.path.join(staging, md_file)
                with open(dest_md_file, "w", encoding="utf-8") as f:
                    frontmatter.dump(post, f)
                if pdf_name and os.path.exists(pdf_path):
                    dest_pdf_file = os.path.join(staging, pdf_name)
                    shutil.copy2(pdf_path, dest_pdf_file)
                processed.add(md_file)
                print(f"Staged {md_file} to {staging}")
        except Exception as e:
            log_error(f"Processing failed: {e}", md_file)
    for pdf_file in pdf_files:
        if pdf_file in processed:
            continue
        try:
            base_name = os.path.splitext(pdf_file)[0]
            md_file = f"{base_name}.md"
            if md_file not in markdown_files:
                post = create_markdown(os.path.join(inbox, pdf_file), base_name)
                pdf_text = extract_pdf_text(os.path.join(inbox, pdf_file))
                chunks = chunk_text(pdf_text, max_length=2000)
                summaries = []
                tags = set()
                category = "General"
                for chunk in chunks:
                    response = call_openai_api(chunk)
                    summaries.append(response.get("summary", "TODO"))
                    tags.update(response.get("tags", []))
                    if response.get("category"):
                        category = response.get("category")
                post.metadata["tags"] = list(tags)
                post.metadata["category"] = category
                summary = "\n\n## Summary\n" + "\n".join(summaries)
                post.content += summary + "\n\n# Reviewed: false"
                dest_md_file = os.path.join(staging, md_file)
                with open(dest_md_file, "w", encoding="utf-8") as f:
                    frontmatter.dump(post, f)
                dest_pdf_file = os.path.join(staging, pdf_file)
                shutil.copy2(os.path.join(inbox, pdf_file), dest_pdf_file)
                print(f"Staged {pdf_file} and {md_file} to {staging}")
        except Exception as e:
            log_error(f"Processing failed: {e}", pdf_file)