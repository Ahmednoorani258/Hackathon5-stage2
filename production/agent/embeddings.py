import logging
from sentence_transformers import SentenceTransformer
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# Singleton model instance for efficient inference
_model = None
_executor = ThreadPoolExecutor(max_workers=1)

def get_model():
    """Load the sentence-transformer model as a singleton."""
    global _model
    if _model is None:
        # Using all-MiniLM-L6-v2 which is free, fast, and has 384 dimensions
        _model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    return _model

async def generate_embedding(text: str) -> list[float]:
    """
    Generate vector embeddings using a local sentence-transformer model.
    Runs the blocking CPU-bound encoding in a thread pool to avoid blocking the event loop.
    """
    try:
        model = get_model()
        loop = asyncio.get_running_loop()
        
        # Run model.encode in a thread pool
        # all-MiniLM-L6-v2 produces 384-dimensional vectors
        embeddings = await loop.run_in_executor(
            _executor, 
            lambda: model.encode([text])[0]
        )
        return embeddings.tolist()
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise
