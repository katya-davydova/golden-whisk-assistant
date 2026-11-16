
import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

# Load environment variables from the .env file
load_dotenv()

# Retrieve the Pinecone API key from environment variables
api_key = os.getenv("PINECONE_API_KEY")

# Retrieve the index name, using a default if not specified
index_name = os.getenv("PINECONE_INDEX_NAME", "rag-openai-index")

# Validate that the Pinecone API key is available
if not api_key:
    raise RuntimeError("PINECONE_API_KEY is missing")

# Initialize the Pinecone client
pc = Pinecone(api_key=api_key)

# Check whether the specified index already exists
if index_name not in pc.list_indexes().names():

    # Create a new serverless Pinecone index if it does not exist
    pc.create_index(
        name=index_name,

        # Vector dimension must match your embedding model
        dimension=1536,

        # Use cosine similarity to compare vectors
        metric="cosine",

        # Configure the serverless deployment
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1",
        ),
    )

    # Inform the user that index creation has started
    print(f"Creating index: {index_name}")

else:
    # Inform the user that the index already exists
    print(f"Index already exists: {index_name}")

# Retrieve and inspect the index configuration
index_info = pc.describe_index(index_name)

# Display the index configuration
print(index_info)
print("Index configuration checked.")
