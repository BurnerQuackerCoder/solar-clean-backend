import io
import uuid
from PIL import Image
from supabase import create_client, Client
from app.core.config import settings

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def get_technician_by_chat_id(chat_id: str):
    """Checks if the Telegram user exists in our secure database."""
    response = supabase.table("technicians").select("*").eq("telegram_chat_id", str(chat_id)).execute()
    return response.data[0] if response.data else None

def upload_photo(file_bytes: bytes) -> str:
    """Compresses raw image bytes and uploads to Supabase Storage."""
    # 1. Compress Image in Memory
    image = Image.open(io.BytesIO(file_bytes))
    
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
        
    compressed_io = io.BytesIO()
    image.save(compressed_io, format="JPEG", quality=60, optimize=True)
    compressed_bytes = compressed_io.getvalue()

    # 2. Upload to Cloud
    file_name = f"photo_{uuid.uuid4().hex}.jpg"
    supabase.storage.from_("solar-photos").upload(
        file_name, 
        compressed_bytes, 
        {"content-type": "image/jpeg"}
    )
    
    return supabase.storage.from_("solar-photos").get_public_url(file_name)

def get_active_job(tech_id: str):
    """Finds the job the technician is currently actively working on."""
    response = supabase.table("jobs").select("*").eq("assigned_tech_id", tech_id).in_("status", ["awaiting_before", "awaiting_after", "awaiting_reason"]).execute()
    return response.data[0] if response.data else None

def get_next_job(tech_id: str):
    """Finds the oldest scheduled job specifically assigned to this tech."""
    response = supabase.table("jobs").select("*").eq("assigned_tech_id", tech_id).eq("status", "scheduled").order("created_at").limit(1).execute()
    return response.data[0] if response.data else None

def update_job(job_id: str, update_data: dict):
    """Updates a job and its photo arrays."""
    response = supabase.table("jobs").update(update_data).eq("id", job_id).execute()
    return response.data[0] if response.data else None

def claim_next_job_from_pool(tech_id: str):
    """Atomically claims the oldest unassigned job from the global pool."""
    # This triggers the SQL function we just wrote in the database
    response = supabase.rpc("claim_next_job", {"p_tech_id": tech_id}).execute()
    return response.data[0] if response.data else None

def get_active_job(tech_id: str):
    """Finds the job the technician is currently actively working on."""
    response = supabase.table("jobs").select("*").eq("assigned_tech_id", tech_id).in_("status", ["awaiting_before", "awaiting_after", "awaiting_reason"]).execute()
    return response.data[0] if response.data else None