from paperscraper.arxiv import get_and_dump_arxiv_papers
from paperscraper.pdf import save_pdf_from_dump
import pymupdf4llm
import os
import json
import uuid
import shutil
from .nlp import process_search_query

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
                print(f"Processed {pdf_file} to markdown successfully.")

                # Remove PDF file after processing
                os.remove(pdf_path)
            except Exception as e:
                print(f"Error processing {pdf_file}: {str(e)}")
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
    query_dir = os.path.join("./scraper", query_uuid)
    pdf_dir = os.path.join(query_dir, 'pdfs')
    output_filepath = os.path.join(query_dir, 'results.jsonl')

    try:
        # Create directories
        os.makedirs(query_dir, exist_ok=True)
        os.makedirs(pdf_dir, exist_ok=True)

        keyword_groups = process_search_query(query)
        print(f"Categorized keyword groups: {keyword_groups}")
        
        get_and_dump_arxiv_papers(keyword_groups, output_filepath=output_filepath, max_results=max_papers)
        print("arXiv scraping completed successfully.")

        save_pdf_from_dump(output_filepath, pdf_path=pdf_dir, key_to_save='doi')

        # Read metadata from JSONL file
        metadata = read_metadata_from_jsonl(output_filepath)
        
        results = pdfs_to_markdown(pdf_dir, metadata)
        
        return results
    finally:
        # Clean up the temporary directory
        if os.path.exists(query_dir):
            shutil.rmtree(query_dir)
            print(f"Cleaned up temporary directory: {query_dir}")
