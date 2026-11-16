
import os
from dotenv import load_dotenv
from pinecone import Pinecone


# -------------------------------------
# CONFIGURATION
# -------------------------------------

# Load environment variables from the .env file
load_dotenv()

# Retrieve the Pinecone API key
API_KEY = os.getenv("PINECONE_API_KEY")

# Retrieve the index name, using a default if not specified
INDEX_NAME = os.getenv(
    "PINECONE_INDEX_NAME",
    "auralisoneb-index",
)

# Ensure the API key is configured
if not API_KEY:
    raise RuntimeError(
        "PINECONE_API_KEY is missing from .env"
    )

# Ensure the index name is configured
if not INDEX_NAME:
    raise RuntimeError(
        "PINECONE_INDEX_NAME is missing from .env"
    )


# -------------------------------------
# CONNECT TO PINECONE
# -------------------------------------

# Initialize the Pinecone client
pc = Pinecone(api_key=API_KEY)


# -------------------------------------
# CHECK WHETHER THE INDEX EXISTS
# -------------------------------------

# Retrieve the names of all existing indexes
existing_indexes = pc.list_indexes().names()

# Stop execution if the specified index does not exist
if INDEX_NAME not in existing_indexes:
    print(f"Index '{INDEX_NAME}' does not exist.")
    raise SystemExit(0)


# -------------------------------------
# DISPLAY INDEX INFORMATION
# -------------------------------------

# Retrieve the index configuration
description = pc.describe_index(INDEX_NAME)

# Display the details before requesting deletion
print("\nPINECONE INDEX DELETION")
print("-" * 40)
print(f"Index name: {INDEX_NAME}")
print(f"Dimension:  {description.dimension}")
print(f"Metric:     {description.metric}")
print(f"Host:       {description.host}")
print("-" * 40)


# -------------------------------------
# CONFIRM DELETION
# -------------------------------------

# Require the user to enter the exact confirmation phrase
# before proceeding with this destructive operation
confirmation = input(
    f"Type DELETE {INDEX_NAME} to permanently delete this index: "
)

# Cancel deletion if the confirmation does not match
if confirmation != f"DELETE {INDEX_NAME}":
    print("Deletion cancelled.")
    raise SystemExit(0)


# -------------------------------------
# DELETE THE PINECONE INDEX
# -------------------------------------

# Request deletion of the specified index
pc.delete_index(INDEX_NAME)

# Report that the deletion request was submitted
print(f"Deletion requested for index '{INDEX_NAME}'.")
print("Check the Pinecone Console to verify deletion.")
