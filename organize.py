import os
import shutil
import time
import frontmatter
from openai import AsyncOpenAI
import re
import asyncio

client = AsyncOpenAI()

async def get_metadata(content):
    try:
        prompt = f"Summarize this content in 1 sentence:\n{content}\n\nProvide 2-5 tags for this content."
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes content and generates metadata."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100
        )
        result = response.choices[0].message.content
        summary = result.split("\n")[0]
        tags = [tag.strip() for tag in result.split("\n")[1].split(",") if tag.strip()]
        return summary, tags
    except Exception as e:
        # Log the error
        logs = "pkm/Logs"
        os.makedirs(logs, exist_ok=True)
        log_file = os.path.join(logs, f"log_organize_{int(time.time())}.md")
        with open(log_file, "a", encoding="utf-8") as log_f:
            log_f.write(f"# Error in get_metadata at {time.time()}\n")
            log_f.write(f"Message: {str(e)}\n")
            log_f.write(f"Content: {content[:100]}...\n\n")
        return "Summary not available", []

async def organize_files():
    inbox = "pkm/Inbox"
    staging = "pkm/Staging"
    logs = "pkm/Logs"
    os.makedirs(inbox, exist_ok=True)
    os.makedirs(staging, exist_ok=True)
    os.makedirs(logs, exist_ok=True)

    log_file = os.path.join(logs, f"log_organize_{int(time.time())}.md")
    with open(log_file, "a", encoding="utf-8") as log_f:
        log_f.write(f"# Organize run at {time.time()}\n\n")

    files = [f for f in os.listdir(inbox) if f.endswith(".md")]
    with open(log_file, "a", encoding="utf-8") as log_f:
        log_f.write(f"Found files in Inbox: {files}\n")

    for md_file in files:
        try:
            with open(log_file, "a", encoding="utf-8") as log_f:
                log_f.write(f"Processing {md_file}\n")
            
            # Read the file
            with open(os.path.join(inbox, md_file), "r", encoding="utf-8") as f:
                content = f.read()
            
            # Parse existing frontmatter
            post = frontmatter.loads(content)
            if not post.metadata:
                post.metadata = {
                    "title": md_file.replace(".md", ""),
                    "date": time.strftime("%Y-%m-%d"),
                    "tags": [],
                    "category": "General",
                    "pdf": ""
                }
            
            # Generate summary and tags if not already present
            if "summary" not in post.metadata or "tags" not in post.metadata:
                summary, tags = await get_metadata(post.content)
                post.metadata["summary"] = summary
                post.metadata["tags"] = tags
            
            # Add Reviewed: false if not present
            if not re.search(r"# Reviewed: (true|false)", post.content, re.IGNORECASE):
                post.content += "\n\n# Reviewed: false"
            
            # Write to Staging
            with open(os.path.join(staging, md_file), "w", encoding="utf-8") as f:
                frontmatter.dump(post, f)
            
            with open(log_file, "a", encoding="utf-8") as log_f:
                log_f.write(f"Wrote {md_file} to Staging\n")
            
            # Move the file (delete from Inbox)
            os.remove(os.path.join(inbox, md_file))
            with open(log_file, "a", encoding="utf-8") as log_f:
                log_f.write(f"Removed {md_file} from Inbox\n")
        
        except Exception as e:
            with open(log_file, "a", encoding="utf-8") as log_f:
                log_f.write(f"# Error processing {md_file} at {time.time()}\n")
                log_f.write(f"Message: {str(e)}\n\n")
            continue

if __name__ == "__main__":
    asyncio.run(organize_files())