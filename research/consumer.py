"""
Kafka consumer for processing research paper requests.
"""
from kafka import KafkaConsumer, KafkaProducer
import json
import os
from dotenv import load_dotenv
from scraper.scrape import scrape_arxiv
from rag import rag_chain
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Kafka components
consumer = KafkaConsumer( # Consumer for scrape requests
    'scrape-requests',
    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='research-consumer-group',
    max_poll_interval_ms=600000,  # 10 minutes instead of default 5 minutes
    max_poll_records=1,           # Process one record at a time
    session_timeout_ms=60000      # 1 minute session timeout
)

producer = KafkaProducer( # Producer to return research results
    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def process_message(message):
    """Process a Kafka message, performing scraping and RAG."""
    try:
        data = message.value
        query = data.get('query')
        job_id = data.get('job_id')
        
        if not query:
            return
            
        logger.info(f"Processing scrape request for job {job_id}: {query}")
        
        # Scrape papers
        papers = scrape_arxiv(query, max_papers=3)
        logger.info(f"Scraped {len(papers)} results for job {job_id}")


        # Web search
        
        #########################################################
        
        # Add papers to vector store (job_id is kept for logging/tracking only)
        rag_chain.add_papers(papers, job_id=job_id)
        logger.info(f"Added papers to vector store for job {job_id}")
        
        # Generate a research summary using RAG (no filtering)
        #summary_question = f"Based on the recent papers about {query}, what are the key findings and developments in this area?"
        summary = rag_chain.query(query)
        
        # Prepare response with summary and job ID
        response = {
            "job_id": job_id,
            "query": query,
            "summary": summary
        }
        
        # Send response to results topic
        producer.send('research-results', key=job_id.encode('utf-8'), value=response)
        producer.flush()
        logger.info(f"Sent research results for job {job_id}")
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        error_response = {
            "job_id": job_id if 'job_id' in locals() else None,
            "query": query if 'query' in locals() else None,
            "error": str(e)
        }
        producer.send('research-errors', value=error_response)
        producer.flush()

def run():
    """Run the consumer loop."""
    logger.info("Research consumer started, waiting for messages...")
    while True:
        try:
            # Get messages one at a time with a timeout
            message_batch = consumer.poll(timeout_ms=1000)
            
            for topic_partition, messages in message_batch.items():
                for message in messages:
                    process_message(message)
                    # Commit offset after successful processing
                    consumer.commit()
                    
        except Exception as e:
            logger.error(f"Error in consumer loop: {str(e)}", exc_info=True)
            # Sleep briefly before retrying
            time.sleep(1)

if __name__ == "__main__":
    run()