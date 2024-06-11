from flask import Flask, request, jsonify, render_template
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
# import numpy as np
import settings

MONGO_URI = settings.MONGODB_URI
DB_NAME = settings.DB
COLLECTION_NAME = settings.COLLECTION

app = Flask(__name__)

# Initialize the model and MongoDB client
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def run_query(query_embedding):
    search = {  '$vectorSearch': {
                    'index': 'vectorIndex', 
                    'path': 'embedding', 
                    'queryVector': query_embedding.tolist(),
                    'numCandidates': 20, 
                    'limit': 10,
                }
            }
    # print('search query: ', search)
    pipeline = [
        search,
        {
            '$project': {
                '_id': 0,
                'name': 1,
                'page_number': 1,
                'score': {
                    '$meta': 'vectorSearchScore',
                },
                'highlight': {'$meta': 'searchHighlights'},
            }
        },
        {'$limit': 20}
    ]
    
    results = list(collection.aggregate(pipeline))
    return results

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query', '')
    
    if not query:
        return jsonify({"error": "Query text is required"}), 400
    
    # Generate the embedding for the query
    query_embedding = model.encode(query)
    
    # run vector search 
    results = run_query(query_embedding)
    
    # Format the response
    print('results: ', results)
    # formatted_results = [{"pdf_name": r[0], "page_number": r[1], "score": round(r[2], 4)} for r in results]
    return render_template('results.html', query=query, results=results)

if __name__ == "__main__":
    app.run(debug=True)
