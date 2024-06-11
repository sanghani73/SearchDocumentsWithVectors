import settings
import os
import pymupdf
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient

MONGO_URI = settings.MONGODB_URI
DB_NAME = settings.DB
COLLECTION_NAME = settings.COLLECTION
SOURCE_DIR = 'files2load'

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def extract_text_from_file(file_path):
    document = pymupdf.open(file_path)
    pages_text = []
    page_num = 0
    for page in document:
        text = page.get_text()
        page_num += 1
        pages_text.append((page_num, text))
    return pages_text, document.metadata

def generate_embeddings(text, model_name='sentence-transformers/all-MiniLM-L6-v2'):
    model = SentenceTransformer(model_name)
    embeddings = model.encode(text)
    return embeddings

def cleanupDB(filename):
    collection.delete_many({'name': filename})
    print(f"Deleted {filename} documents in the collection")

def store_embeddings_in_DB(pdf_name, pages_embeddings, metadata):
    for page_num, embedding in pages_embeddings:
        document = {
            'name': pdf_name,
            'page_number': page_num,
            'metadata': metadata,
            'embedding': embedding.tolist()  # Convert numpy array to list for storage
        }
        collection.insert_one(document)

def main(filename):
    cleanupDB(filename)
    f = os.path.join(SOURCE_DIR, filename)
    # Step 2: Extract text from PDF
    pages_text, metadata = extract_text_from_file(f)
    print(f"Extracted text from {filename}")

    # Step 3: Generate embeddings for each page
    pages_embeddings = [(page_num, generate_embeddings(text)) for page_num, text in pages_text]
    print("Generated embeddings for each page")

    # Step 4: Store embeddings in MongoDB
    store_embeddings_in_DB(filename, pages_embeddings, metadata)
    print("Stored embeddings in MongoDB")

if __name__ == "__main__":
    print("Enter the file name and make sure it is in the `files2load` directory:")
    filename = input()
    main(filename)
