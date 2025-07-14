"""
FastAPI Application for PDF and YouTube Video Query System with Azure OpenAI

This application provides endpoints for:
- PDF document upload and querying
- YouTube video transcript processing and querying
- Smart search across multiple document types
- Azure OpenAI-powered question answering

Author: Shreya Khattar
"""

from pydantic import BaseModel
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
import re
from collections import Counter 
from openai import AzureOpenAI
from dotenv import load_dotenv
import os

# Qdrant utilities
from app.qdrant_utils import (
    create_embeddings_and_store_qdrant, 
    qdrant_similarity_search, 
    get_available_documents,
    search_specific_document,
    smart_document_search,
    get_content_type_summary
)

# Load environment variables
load_dotenv()

app = FastAPI(
    title="PDF and YouTube Video Query API",
    description="FastAPI application for querying PDF documents and YouTube videos using Azure OpenAI",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Pydantic Models ---- #

class QueryRequest(BaseModel):
    """Base query request model"""
    query: str
    k: int = 3

class DocumentQueryRequest(BaseModel):
    """Query specific document by name"""
    query: str
    document_name: str
    k: int = 3

class SmartQueryRequest(BaseModel):
    """Smart query with strategy selection"""
    query: str
    k: int = 3
    strategy: str = "best_match"

class VideoRequestWithTranscript(BaseModel):
    """YouTube video upload with optional manual transcript"""
    video_url: str
    manual_transcript: Optional[str] = None
    use_fallback: bool = True

class VideoQueryRequest(BaseModel):
    """Query YouTube video with optional manual transcript"""
    query: str
    video_url: str
    k: int = 3
    manual_transcript: Optional[str] = None

class SmartVideoQueryRequest(BaseModel):
    """Smart query across content types"""
    query: str
    k: int = 3
    strategy: str = "best_match"
    content_type: str = "all"

# ---- Helper Functions ---- #

def validate_pdf(file: UploadFile) -> None:
    """Validate uploaded file is a PDF"""
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF files are allowed."
        )

async def extract_text_from_pdf(file: UploadFile) -> str:
    """Extract text content from uploaded PDF file"""
    file_bytes = await file.read()
    try:
        pdf_doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""
        for page in pdf_doc:
            text += page.get_text()
        pdf_doc.close()

        if not text.strip():
            raise ValueError("PDF has no extractable text.")
        return text
    except Exception as e:
        raise RuntimeError(f"PDF text extraction failed: {str(e)}")

def split_text_into_chunks(text: str, source_name: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[Document]:
    """Split text into chunks for vector storage"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    doc = Document(page_content=text, metadata={"source": source_name})
    return splitter.split_documents([doc])

def extract_video_id(url: str) -> str:
    """Extract YouTube video ID from URL"""
    try:
        parsed_url = urlparse(url)
        if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
            query_params = parse_qs(parsed_url.query)
            if "v" in query_params:
                return query_params["v"][0]
        elif parsed_url.hostname in ['youtu.be']:
            return parsed_url.path[1:]
        
        raise ValueError("Invalid YouTube URL format")
    except Exception:
        raise ValueError(f"Could not extract video ID from URL: {url}")

def ask_azure_openai(query: str, context_chunks: List[Document]) -> str:
    """
    Generate answer using Azure OpenAI based on context chunks
    """
    try:
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )

        context = "\n\n".join([doc.page_content for doc in context_chunks])
        
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context. Be accurate and concise."},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Azure OpenAI Error: {e}")
        return f"Error generating response: {str(e)}"

def get_youtube_transcript(video_url: str, use_fallback: bool = True) -> str:
    """
    Get YouTube transcript with fallback strategies for cloud deployment
    """
    video_id = extract_video_id(video_url)
    
    # Primary method: Direct transcript API
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([entry['text'] for entry in transcript])
    except Exception as primary_error:
        if not use_fallback:
            raise RuntimeError(f"Primary transcript retrieval failed: {str(primary_error)}")
        
        # Fallback method 1: Try with different language codes
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-US', 'en-GB'])
            return " ".join([entry['text'] for entry in transcript])
        except Exception:
            pass
        
        # Fallback method 2: Try to get any available transcript
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            for transcript in transcript_list:
                try:
                    transcript_data = transcript.fetch()
                    return " ".join([entry['text'] for entry in transcript_data])
                except:
                    continue
            raise Exception("No accessible transcripts found")
        except Exception:
            pass
        
        # If all methods fail, provide helpful error message
        error_message = f"""Transcript retrieval failed for video {video_id}.

This is likely due to:
1. YouTube blocking cloud provider IPs (Azure/AWS/GCP)
2. Video has no captions/transcripts
3. Video is private or restricted
4. Geographic restrictions

For cloud deployment, consider:
1. Using manual transcript input
2. Using a proxy service
3. Processing videos locally before deployment"""

        raise RuntimeError(error_message)

def handle_manual_transcript(video_url: str, manual_transcript: str) -> str:
    """Validate and process manually provided transcript"""
    if not manual_transcript or not manual_transcript.strip():
        raise ValueError("Manual transcript text is required")
    return manual_transcript.strip()


# ---- API Endpoints ---- #

@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint"""
    return {"message": f"PDF and YouTube Video Query API - {os.getenv('SHREYA_NAME', 'Unknown')}", "status": "healthy"}

@app.get("/test-azure-openai", tags=["Testing"])
def test_azure_openai():
    """Test Azure OpenAI connectivity"""
    try:
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )

        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[{"role": "user", "content": "Give a short note on Dynamic Programming"}],
            max_tokens=500,
            temperature=0.7
        )

        result = response.choices[0].message.content
        return {"message": result, "status": "success"}
    except Exception as e:
        return {"error": f"Azure OpenAI connection failed: {str(e)}", "status": "failed"}

@app.post("/upload-pdf/", tags=["PDF Management"])
async def upload_pdfs(files: List[UploadFile] = File(...)):
    """Upload and process multiple PDF files"""
    upload_summaries = []

    try:
        for file in files:  
            validate_pdf(file)
            
            text = await extract_text_from_pdf(file) 
            chunks = split_text_into_chunks(text, source_name=file.filename)
            
            create_embeddings_and_store_qdrant(chunks)
            
            upload_summaries.append({
                "filename": file.filename,
                "num_chunks": len(chunks)
            })

        return JSONResponse(content={
            "message": "PDFs processed and stored successfully",
            "summary": upload_summaries
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query/", tags=["PDF Querying"])
async def query_documents(request: QueryRequest):
    """Query all uploaded documents"""
    try:
        results = qdrant_similarity_search(request.query, k=request.k)
        answer = ask_azure_openai(request.query, results)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/", tags=["PDF Management"])
async def list_documents():
    """Get list of all uploaded documents"""
    try:
        documents = get_available_documents()
        return {"documents": documents, "count": len(documents)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query-document/", tags=["PDF Querying"])
async def query_specific_document(request: DocumentQueryRequest):
    """Query a specific document by name"""
    try:
        results = search_specific_document(request.query, request.document_name, k=request.k)
        if not results:
            return {
                "answer": f"No relevant information found in document '{request.document_name}' for your query.",
                "document_queried": request.document_name
            }
        
        answer = ask_azure_openai(request.query, results)
        return {
            "answer": answer,
            "document_queried": request.document_name,
            "chunks_found": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/smart-query/", tags=["PDF Querying"])
async def smart_query(request: SmartQueryRequest):
    """Intelligent query with automatic strategy selection"""
    try:
        search_result = smart_document_search(request.query, k=request.k, strategy=request.strategy)
        
        if not search_result["chunks"]:
            return {
                "answer": "No relevant information found for your query.",
                "strategy_used": request.strategy
            }
        
        answer = ask_azure_openai(request.query, search_result["chunks"])
        
        response = {
            "answer": answer,
            "strategy_used": search_result["strategy_used"],
            "chunks_used": len(search_result["chunks"])
        }
        
        # Add metadata if available
        for key in ["primary_source", "sources_used", "document_scores"]:
            if key in search_result:
                response[key.replace("document_", "source_")] = search_result[key]
            
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---- YouTube Video Endpoints ---- #

@app.post("/upload-youtube/", tags=["YouTube Management"])
async def upload_youtube_video(request: VideoRequestWithTranscript):
    """Upload and process YouTube video transcript"""
    try:
        video_id = extract_video_id(request.video_url)
        
        # Get transcript
        if request.manual_transcript:
            transcript = handle_manual_transcript(request.video_url, request.manual_transcript)
            source_method = "manual"
        else:
            try:
                transcript = get_youtube_transcript(request.video_url, use_fallback=request.use_fallback)
                source_method = "automatic"
            except Exception as transcript_error:
                return {
                    "success": False,
                    "error": "transcript_blocked",
                    "message": "YouTube transcript retrieval failed",
                    "details": str(transcript_error),
                    "video_id": video_id,
                    "solutions": [
                        "Provide manual transcript text",
                        "Use a proxy service",
                        "Process video locally"
                    ]
                }
        
        source_name = f"video_{video_id}.txt"
        chunks = split_text_into_chunks(transcript, source_name=source_name)
        create_embeddings_and_store_qdrant(chunks)

        return {
            "success": True,
            "message": "YouTube transcript processed successfully",
            "video_id": video_id,
            "source": source_name,
            "num_chunks": len(chunks),
            "transcript_method": source_method,
            "transcript_length": len(transcript)
        }

    except Exception as e:
        return {
            "success": False,
            "error": "processing_failed",
            "message": "Failed to process YouTube video",
            "details": str(e)
        }

@app.post("/query-youtube/", tags=["YouTube Querying"])
async def query_youtube_video(request: VideoQueryRequest):
    """Query a specific YouTube video transcript"""
    try:
        video_id = extract_video_id(request.video_url)
        source_name = f"video_{video_id}.txt"
        
        # Try to search in existing database first
        try:
            results = search_specific_document(request.query, source_name, k=request.k)
            if results:
                answer = ask_azure_openai(request.query, results)
                return {
                    "success": True,
                    "answer": answer,
                    "video_id": video_id,
                    "source": "database",
                    "chunks_found": len(results)
                }
        except:
            pass
        
        # If not in database, get transcript
        if request.manual_transcript:
            transcript = handle_manual_transcript(request.video_url, request.manual_transcript)
            source_method = "manual"
        else:
            try:
                transcript = get_youtube_transcript(request.video_url, use_fallback=True)
                source_method = "automatic"
            except Exception as transcript_error:
                return {
                    "success": False,
                    "error": "transcript_blocked",
                    "message": "YouTube transcript blocked and no manual transcript provided",
                    "details": str(transcript_error),
                    "solutions": ["Provide manual transcript", "Upload video first", "Use proxy service"]
                }
        
        # Create chunks and answer
        chunks = split_text_into_chunks(transcript, source_name=source_name)
        relevant_chunks = chunks[:request.k] if len(chunks) > request.k else chunks
        answer = ask_azure_openai(request.query, relevant_chunks)
        
        return {
            "success": True,
            "answer": answer,
            "video_id": video_id,
            "source": f"direct_transcript_{source_method}",
            "chunks_used": len(relevant_chunks)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": "query_failed",
            "message": "Failed to query YouTube video",
            "details": str(e)
        }

@app.get("/videos/", tags=["YouTube Management"])
async def list_youtube_videos():
    """Get list of all uploaded YouTube videos"""
    try:
        documents = get_available_documents()
        videos = [doc for doc in documents if doc.startswith("video_") and doc.endswith(".txt")]
        
        video_info = []
        for video in videos:
            video_id = video.replace("video_", "").replace(".txt", "")
            video_info.append({
                "video_id": video_id,
                "source_name": video,
                "youtube_url": f"https://www.youtube.com/watch?v={video_id}"
            })
        
        return {"videos": video_info, "count": len(video_info)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/smart-query-all/", tags=["Smart Querying"])
async def smart_query_all_content(request: SmartVideoQueryRequest):
    """Intelligent query across PDFs, YouTube videos, or both"""
    try:
        documents = get_available_documents()
        
        # Filter by content type
        if request.content_type == "pdf":
            filtered_docs = [doc for doc in documents if not doc.startswith("video_")]
        elif request.content_type == "video":
            filtered_docs = [doc for doc in documents if doc.startswith("video_")]
        else:  # "all"
            filtered_docs = documents
        
        if not filtered_docs:
            return {
                "answer": f"No {request.content_type} content found in the database.",
                "strategy_used": request.strategy,
                "content_type": request.content_type
            }
        
        search_result = smart_document_search(request.query, k=request.k, strategy=request.strategy)
        
        if not search_result["chunks"]:
            return {
                "answer": f"No relevant information found in {request.content_type} content for your query.",
                "strategy_used": request.strategy,
                "content_type": request.content_type
            }
        
        answer = ask_azure_openai(request.query, search_result["chunks"])
        
        response = {
            "answer": answer,
            "strategy_used": search_result["strategy_used"],
            "chunks_used": len(search_result["chunks"]),
            "content_type": request.content_type
        }
        
        # Add metadata if available
        if "primary_source" in search_result:
            source = search_result["primary_source"]
            response["primary_source"] = source
            response["source_type"] = "video" if source.startswith("video_") else "pdf"
            
        for key in ["sources_used", "document_scores"]:
            if key in search_result:
                response[key.replace("document_", "source_")] = search_result[key]
            
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/content-summary/", tags=["Information"])
async def get_content_summary():
    """Get summary of all available content (PDFs and videos)"""
    try:
        return get_content_type_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/youtube-status/", tags=["Testing"])
async def check_youtube_api_status():
    """Check if YouTube transcript API is accessible"""
    test_video_id = "dQw4w9WgXcQ"
    test_url = f"https://www.youtube.com/watch?v={test_video_id}"
    
    try:
        get_youtube_transcript(test_url, use_fallback=True)
        return {
            "status": "accessible",
            "message": "YouTube transcript API is working",
            "environment": "local_or_compatible"
        }
    except Exception as e:
        error_str = str(e)
        
        if "cloud provider" in error_str.lower() or "ip" in error_str.lower():
            return {
                "status": "blocked_cloud",
                "message": "YouTube API blocked - Cloud provider IP detected",
                "environment": "cloud_deployment",
                "solutions": [
                    "Use manual transcript upload",
                    "Implement proxy service",
                    "Process videos locally"
                ]
            }
        else:
            return {
                "status": "error_other",
                "message": "YouTube API error - Not cloud-related",
                "error_details": error_str
            }


