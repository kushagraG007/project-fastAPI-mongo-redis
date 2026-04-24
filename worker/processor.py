"""
Background worker that processes queued documents.

Flow:
1. Poll MongoDB for queued documents
2. Mark as processing (atomic update to prevent race conditions)
3. Simulate AI processing (sleep 10-30 seconds)
4. Generate mock summary (10% chance of failure)
5. Update document status and cache result
6. Decrement rate limiter
"""

import time
import random
import hashlib
from datetime import datetime
from pymongo import MongoClient
import redis
from loguru import logger
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import settings
from app.models import DocumentStatus


class DocumentProcessor:
    """Background worker for processing documents"""
    
    def __init__(self):
        # MongoDB client (sync)
        self.mongo_client = MongoClient(settings.mongodb_url)
        self.db = self.mongo_client[settings.mongodb_db_name]
        self.collection = self.db.documents
        
        # Redis client
        self.redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True
        )
        
        logger.info("Worker initialized")
        logger.info(f"MongoDB: {settings.mongodb_url}")
        logger.info(f"Redis: {settings.redis_url}")
        logger.info(f"Poll interval: {settings.worker_poll_interval}s")
        logger.info(f"Process time: {settings.worker_min_process_time}-{settings.worker_max_process_time}s")
        logger.info(f"Failure rate: {settings.worker_failure_rate * 100}%")
    
    def get_next_document(self):
        """
        Get next queued document and mark as processing atomically.
        
        Uses findOneAndUpdate with returnDocument=AFTER to prevent
        race conditions when multiple workers are running.
        
        Returns:
            Document dict if found, None otherwise
        """
        result = self.collection.find_one_and_update(
            {"status": DocumentStatus.QUEUED.value},
            {
                "$set": {
                    "status": DocumentStatus.PROCESSING.value,
                    "processing_started_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            },
            return_document=True  # Return updated document
        )
        
        return result
    
    def generate_mock_summary(self, content: str, title: str) -> str:
        """
        Generate a mock AI summary.
        
        In production, this would call an actual AI/LLM API.
        For this assignment, we simulate it with templated text.
        """
        word_count = len(content.split())
        char_count = len(content)
        
        summary = f"Document Summary: '{title}'\n\n"
        summary += f"This document contains {word_count} words and {char_count} characters. "
        summary += f"Key topics identified: document processing, content analysis, automated summarization. "
        summary += f"The content discusses: {content[:100]}... "
        summary += f"Generated at {datetime.utcnow().isoformat()}"
        
        return summary
    
    def process_document(self, doc):
        """
        Process a single document.
        
        Steps:
        1. Simulate processing time (10-30 seconds)
        2. Random 10% failure rate
        3. Generate summary or error
        4. Update document in MongoDB
        5. Cache summary in Redis
        6. Decrement rate limiter
        """
        doc_id = doc["_id"]
        user_id = doc["user_id"]
        title = doc["title"]
        content = doc["content"]
        content_hash = doc["content_hash"]
        
        logger.info(f"Processing document {doc_id} for user {user_id}")
        
        # Simulate processing time
        process_time = random.uniform(
            settings.worker_min_process_time,
            settings.worker_max_process_time
        )
        logger.info(f"Simulating processing for {process_time:.1f} seconds...")
        time.sleep(process_time)
        
        # Random failure (10% chance)
        should_fail = random.random() < settings.worker_failure_rate
        
        now = datetime.utcnow()
        
        if should_fail:
            # Simulate failure
            logger.warning(f"Document {doc_id} processing FAILED (simulated)")
            
            self.collection.update_one(
                {"_id": doc_id},
                {
                    "$set": {
                        "status": DocumentStatus.FAILED.value,
                        "error_message": "Processing failed: Simulated random failure for testing",
                        "processing_completed_at": now,
                        "updated_at": now
                    }
                }
            )
        else:
            # Success - generate summary
            logger.info(f"Document {doc_id} processing COMPLETED")
            
            summary = self.generate_mock_summary(content, title)
            
            self.collection.update_one(
                {"_id": doc_id},
                {
                    "$set": {
                        "status": DocumentStatus.COMPLETED.value,
                        "summary": summary,
                        "processing_completed_at": now,
                        "updated_at": now
                    }
                }
            )
            
            # Cache the summary
            try:
                cache_key = f"cache:summary:{content_hash}"
                self.redis_client.setex(
                    cache_key,
                    settings.redis_cache_ttl,
                    summary
                )
                logger.info(f"Cached summary for content_hash: {content_hash[:16]}...")
            except Exception as e:
                logger.error(f"Failed to cache summary: {str(e)}")
        
        # Decrement rate limiter
        try:
            rate_limit_key = f"rate_limit:user:{user_id}:active_jobs"
            current = self.redis_client.get(rate_limit_key)
            if current and int(current) > 0:
                self.redis_client.decr(rate_limit_key)
                logger.info(f"Decremented rate limit for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to decrement rate limit: {str(e)}")
    
    def run(self):
        """
        Main worker loop.
        
        Continuously polls for queued documents and processes them.
        """
        logger.info("Worker started - polling for documents...")
        
        while True:
            try:
                # Get next document
                doc = self.get_next_document()
                
                if doc:
                    # Process it
                    self.process_document(doc)
                else:
                    # No documents - wait before polling again
                    logger.debug("No queued documents, sleeping...")
                    time.sleep(settings.worker_poll_interval)
                    
            except KeyboardInterrupt:
                logger.info("Worker stopped by user")
                break
            except Exception as e:
                logger.error(f"Worker error: {str(e)}")
                time.sleep(settings.worker_poll_interval)
        
        # Cleanup
        self.mongo_client.close()
        self.redis_client.close()
        logger.info("Worker shutdown complete")


if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=settings.log_level
    )
    
    # Start worker
    processor = DocumentProcessor()
    processor.run()