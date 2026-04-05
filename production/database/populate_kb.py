import asyncio
import os
import re
import logging
from typing import List, Dict

# Assuming you have set up python-dotenv or are setting env vars externally
from dotenv import load_dotenv
import asyncpg

# Make sure we use the same embedding function the tools use
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from production.agent.embeddings import generate_embedding

load_dotenv()
logger = logging.getLogger(__name__)

DOCS_PATH = os.path.join(os.path.dirname(__file__), '../../context/product-docs.md')

def chunk_markdown(content: str) -> List[Dict[str, str]]:
    """
    Split markdown content into semantic chunks based on headers.
    Returns a list of dicts with 'title', 'category', and 'content'.
    """
    chunks = []
    
    # Split by level 2 and level 3 headers
    # regex matches: "## ", "### ", followed by text
    sections = re.split(r'(?m)^(## |### )', content)
    
    current_title = "General Context"
    current_category = "general"
    
    # Handle any content before the first header
    if sections[0].strip():
        chunks.append({
            "title": "FlowSync Overview",
            "category": "overview",
            "content": sections[0].strip()
        })
        
    # Iterate through split parts (pattern matches act as delimiters)
    # sections looks like: [pre-content, "## ", "1) Getting Started\n...", "### ", "Create an Account\n..."]
    for i in range(1, len(sections), 2):
        header_level = sections[i]
        text_block = sections[i+1].strip()
        
        # Extract title (first line) and content (rest)
        lines = text_block.split('\n', 1)
        if not lines:
            continue
            
        title = lines[0].strip()
        content = lines[1].strip() if len(lines) > 1 else ""
        
        # Basic category derivation
        category_lower = title.lower()
        if "getting started" in category_lower or "onboard" in category_lower:
            current_category = "onboarding"
        elif "troubleshoot" in category_lower or "issues" in category_lower:
            current_category = "troubleshooting"
        elif "integration" in category_lower:
            current_category = "integrations"
        elif "billing" in category_lower:
            current_category = "billing"
        elif "security" in category_lower or "export" in category_lower:
            current_category = "security_compliance"
        else:
            current_category = "features"
            
        if content:
            # Reconstruct the full chunk text for the embedding
            full_content = f"{header_level}{title}\n\n{content}"
            chunks.append({
                "title": title,
                "category": current_category,
                "content": full_content
            })
            
    return chunks

async def populate_db():
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("Error: DATABASE_URL environment variable is not set.")
        return
        
    try:
        with open(DOCS_PATH, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
    except FileNotFoundError:
        print(f"Error: Could not find {DOCS_PATH}")
        return

    print("Chunking markdown document...")
    chunks = chunk_markdown(markdown_content)
    print(f"Created {len(chunks)} document chunks.")

    print("Connecting to database...")
    try:
        conn = await asyncpg.connect(dsn)
        
        # Clear existing knowledge base entries to avoid duplicates on re-runs
        await conn.execute("TRUNCATE TABLE knowledge_base")
        print("Cleared existing knowledge base entries.")
        
        for idx, chunk in enumerate(chunks):
            print(f"Processing chunk {idx+1}/{len(chunks)}: {chunk['title']}")
            
            # In a production app, generate_embedding calls an LLM.
            # Here we are using our stub from production/agent/embeddings.py
            embedding = await generate_embedding(chunk['content'])
            
            # Since the dummy embedding is a list of floats, we format it as a string for pgvector '[1.0, 2.0, ...]'
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'
            
            await conn.execute("""
                INSERT INTO knowledge_base (title, content, category, embedding)
                VALUES ($1, $2, $3, $4::vector)
            """, chunk['title'], chunk['content'], chunk['category'], embedding_str)
            
        print("\nSuccessfully populated knowledge base!")
        
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        if 'conn' in locals():
            await conn.close()

if __name__ == "__main__":
    asyncio.run(populate_db())
