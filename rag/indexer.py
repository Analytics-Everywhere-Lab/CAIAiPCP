import uuid
from vector_db import MedicalVectorDB
from datasets import load_dataset
from tqdm import tqdm


def index_medical_dataset():
    """Index the medical dataset into the vector database."""
    print("Starting to index the MedicalRAG...")
    vector_db = MedicalVectorDB()

    # Check if already indexed
    if vector_db.is_indexed():
        print(f"Database already contains {vector_db.get_document_count()} documents.")
        reindex = input("Do you want to re-index anyway? (y/n): ").lower() == "y"
        if not reindex:
            print("Using existing database.")
            return vector_db

    print("Loading MedicalRAG dataset...")

    try:
        # Load the dataset
        ds = load_dataset("homeway/MedicalRAG")
        print(f"Dataset loaded successfully. Keys: {ds.keys()}")

        # Use train split if available
        if "train" in ds:
            data = ds["train"]
            split_name = "train"
        else:
            split_name = list(ds.keys())[0]
            data = ds[split_name]

        print(f"Using split: {split_name}")
        print(f"Total dataset size: {len(data)}")

        # Filter for category="case" only
        print("Filtering for category='case'...")
        filtered_data = []
        for item in data:
            if "category" in item and item["category"] == "case":
                filtered_data.append(item)

        print(
            f"Filtered dataset size: {len(filtered_data)} documents with category='case'"
        )

        if len(filtered_data) == 0:
            print("No documents found with category='case'")
            return None

        # Index the filtered data
        print("Starting indexing process...")
        batch_size = 100
        total_batches = (len(filtered_data) + batch_size - 1) // batch_size
        indexed_count = 0
        skipped_count = 0

        # Clear existing collection if re-indexing
        if vector_db.is_indexed():
            vector_db.chroma_client.delete_collection(vector_db.collection_name)
            vector_db.collection = vector_db.chroma_client.create_collection(
                name=vector_db.collection_name,
                metadata={"description": "Medical RAG dataset embeddings"},
            )

        for batch_idx in tqdm(range(total_batches), desc="Indexing batches"):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(filtered_data))
            batch_data = filtered_data[start_idx:end_idx]

            documents = []
            metadatas = []
            ids = []

            for i, item in enumerate(batch_data):
                # Use only the 'document' column
                if "document" not in item or not item["document"]:
                    skipped_count += 1
                    continue

                document_text = str(item["document"]).strip()
                if not document_text:
                    skipped_count += 1
                    continue

                documents.append(document_text)

                # Create metadata (all fields except document)
                metadata = {}
                for key, value in item.items():
                    if key != "document" and value is not None:
                        if isinstance(value, (str, int, float, bool)):
                            metadata[key] = str(value)
                        else:
                            metadata[key] = str(value)[:500]

                metadata["batch_id"] = batch_idx
                metadata["item_id"] = start_idx + i
                metadata["document_length"] = len(document_text)
                metadatas.append(metadata)
                ids.append(str(uuid.uuid4()))

            if not documents:
                continue

            # Generate embeddings
            try:
                embeddings = vector_db.embedding_model.encode(
                    documents, convert_to_numpy=True, show_progress_bar=False
                ).tolist()

                # Add to ChromaDB
                vector_db.collection.add(
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                )

                indexed_count += len(documents)

            except Exception as e:
                print(f"Error processing batch {batch_idx}: {e}")
                continue

        final_count = vector_db.collection.count()
        print(f"\nIndexing completed!")
        print(f"Total documents indexed: {final_count}")
        print(f"Documents processed: {indexed_count}")
        print(f"Documents skipped: {skipped_count}")

        return vector_db

    except Exception as e:
        print(f"Error loading dataset: {e}")
        return None


if __name__ == "__main__":
    """Run indexing standalone"""
    index_medical_dataset()
