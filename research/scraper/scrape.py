from paperscraper.arxiv import get_and_dump_arxiv_papers
from paperscraper.pdf import save_pdf_from_dump
import pymupdf4llm
import os
import json
import uuid
import shutil
import logging
from .nlp import process_search_query

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def read_metadata_from_jsonl(jsonl_file):
    """
    Read metadata from a JSONL file and return as a dictionary.
    
    Args:
        jsonl_file (str): Path to JSONL file

    Returns:
        dict: Dictionary containing metadata for each paper
    """
    metadata_dict = {}
    with open(jsonl_file, 'r') as f:
        for line in f:
            paper_data = json.loads(line.strip())
            if 'doi' in paper_data:
                metadata_dict[paper_data['doi']] = paper_data
    return metadata_dict

def pdfs_to_markdown(pdf_dir, metadata_dict):
    """
    Convert PDFs in a directory to markdown, using metadata from a dictionary.
    
    Args:
        pdf_dir (str): Directory containing PDF files
        metadata_dict (dict): Dictionary containing metadata for each PDF
    
    Returns:
        list: List of dictionaries containing paper metadata and markdown content
    """
    results = []
    for pdf_file in os.listdir(pdf_dir):
        if pdf_file.endswith('.pdf'):
            pdf_path = os.path.join(pdf_dir, pdf_file)
            try:
                md_text = pymupdf4llm.to_markdown(pdf_path)
                # Extract DOI from filename (assuming filename contains DOI)
                doi = pdf_file.replace('.pdf', '').replace('_', '/')
                
                # Combine metadata with markdown content
                paper_result = metadata_dict.get(doi, {}).copy()
                paper_result.update({
                    'text': md_text
                })
                results.append(paper_result)
                logger.info(f"Processed {pdf_file} to markdown successfully.")

                # Remove PDF file after processing
                os.remove(pdf_path)
            except Exception as e:
                logger.error(f"Error processing {pdf_file}: {str(e)}")
    return results

def scrape_arxiv(query, max_papers=3):
    """
    Scrape arxiv papers based on provided query, automatically categorizing keywords
    and convert PDFs to markdown. Creates and cleans up a temporary directory for each query.
    
    Args:
        query (str): The search query to process
        max_papers (int): Maximum number of papers to retrieve
    
    Returns:
        list: List of dictionaries containing paper metadata and markdown content
    """
    # Generate unique ID for this query
    query_uuid = str(uuid.uuid4())
    pdf_dir = os.path.join("./scraper", 'pdfs')
    query_dir = os.path.join(pdf_dir, query_uuid)
    output_filepath = os.path.join(query_dir, 'results.jsonl')

    try:
        logger.info(f"Starting scrape for query: {query}")
        logger.info(f"Using temporary directory: {query_dir}")

        # Create directories
        os.makedirs(query_dir, exist_ok=True)
        os.makedirs(pdf_dir, exist_ok=True)

        keyword_groups = process_search_query(query)
        logger.info(f"Processed keyword groups: {keyword_groups}")
        
        logger.info(f"Starting arXiv scraping for {max_papers} papers...")
        get_and_dump_arxiv_papers(keyword_groups, output_filepath=output_filepath, max_results=max_papers)
        logger.info("arXiv scraping completed successfully")

        logger.info("Downloading PDFs...")
        save_pdf_from_dump(output_filepath, pdf_path=pdf_dir, key_to_save='doi')
        logger.info("PDF downloads completed")

        # Read metadata from JSONL file
        logger.info("Processing paper metadata...")
        metadata = read_metadata_from_jsonl(output_filepath)
        logger.info(f"Found metadata for {len(metadata)} papers")
        
        logger.info("Converting PDFs to markdown...")
        results = pdfs_to_markdown(pdf_dir, metadata)
        logger.info(f"Successfully processed {len(results)} papers to markdown")
        
        # Log a summary of the results
        for idx, paper in enumerate(results, 1):
            logger.info(f"\nPaper {idx}:")
            logger.info(f"Title: {paper.get('title', 'N/A')}")
            logger.info(f"Authors: {paper.get('authors', 'N/A')}")
            logger.info(f"DOI: {paper.get('doi', 'N/A')}")
            logger.info(f"Abstract: {paper.get('abstract', 'N/A')[:200]}...")

        return results
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}", exc_info=True)
        raise
    finally:
        # Clean up the temporary directory
        if os.path.exists(query_dir):
            shutil.rmtree(query_dir)
            logger.info(f"Cleaned up temporary directory: {query_dir}")
