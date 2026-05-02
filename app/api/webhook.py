from fastapi import APIRouter, Request
from app.services.bot_service import send_message, bot
from app.services.supabase import (
    get_technician_by_chat_id, upload_photo, 
    get_active_job, update_job, claim_next_job_from_pool
)

router = APIRouter()

@router.post("/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()
    if "message" not in data: 
        return {"status": "ok"}
        
    chat_id = str(data["message"]["chat"]["id"])
    technician = get_technician_by_chat_id(chat_id)
    
    # 1. SECURITY GATEWAY
    if not technician:
        await send_message(chat_id, f"⛔ UNAUTHORIZED DEVICE ⛔\nID: {chat_id}")
        return {"status": "unauthorized"}
        
    tech_id = technician["id"]
    
    # 2. STATE LOOKUP
    active_job = get_active_job(tech_id)
    
    # 3. TEXT COMMANDS (State Transitions)
    if "text" in data["message"]:
        text = data["message"]["text"]
        
        if text == "/start":
            await send_message(chat_id, f"Welcome back, {technician['name']}. Send /next to start your shift.")
            
        elif text == "/next":
            if active_job:
                await send_message(chat_id, f"⚠️ You are already on a job for {active_job['customer_name']}. Please finish it first.")
            else:
                # The tech reaches into the global pool
                claimed_job = claim_next_job_from_pool(tech_id)
                if claimed_job:
                    await send_message(chat_id, f"🔧 CLAIMED JOB: {claimed_job['customer_name']}\n📍 Phone: {claimed_job['customer_phone']}\n\n📸 Send as many BEFORE photos as you need. Type /clean when finished.")
                else:
                    await send_message(chat_id, "🎉 The global pool is empty! Take a break.")
                    
        elif text == "/clean":
            if active_job and active_job["status"] == "awaiting_before":
                if len(active_job["before_photos"]) == 0:
                    await send_message(chat_id, "⚠️ You must upload at least one BEFORE photo first.")
                else:
                    update_job(active_job["id"], {"status": "awaiting_after"})
                    await send_message(chat_id, "🧹 Status: Cleaning. \n\nOnce the panels are clean, send your AFTER photos, then type /done.")
            else:
                await send_message(chat_id, "Command not valid right now.")
                
        elif text == "/done":
            if active_job and active_job["status"] == "awaiting_after":
                if len(active_job["after_photos"]) == 0:
                    await send_message(chat_id, "⚠️ You must upload at least one AFTER photo first.")
                else:
                    update_job(active_job["id"], {"status": "completed"})
                    await send_message(chat_id, f"✅ Job COMPLETED for {active_job['customer_name']}!\nSend /next for your next assignment.")
            else:
                await send_message(chat_id, "Command not valid right now.")
        elif text == "/cancel":
            if active_job:
                update_job(active_job["id"], {"status": "awaiting_reason"})
                await send_message(chat_id, "⚠️ Cancellation Initiated.\n\nPlease type the reason (e.g., 'Customer not home', 'Raining', 'Locked gate').")
            else:
                await send_message(chat_id, "❌ You have no active job to cancel.")
                
        # --- NEW: CAPTURE THE REASON ---
        elif active_job and active_job["status"] == "awaiting_reason":
            # If they are in the awaiting_reason state, whatever text they send next is logged as the reason.
            update_job(active_job["id"], {
                "status": "cancelled", 
                "issue_reason": text
            })
            await send_message(chat_id, f"🚫 Job cancelled. Reason logged: '{text}'.\n\nSend /next to grab another job from the pool.")

    # 4. PHOTO UPLOADS (Array Appending)
    elif "photo" in data["message"]:
        if not active_job:
            await send_message(chat_id, "❌ You don't have an active job! Send /next first.")
            return {"status": "ok"}
            
        await send_message(chat_id, "⏳ Compressing and saving photo...")
        try:
            photo_file_id = data["message"]["photo"][-1]["file_id"]
            file = await bot.get_file(photo_file_id)
            file_bytes = await file.download_as_bytearray()
            public_url = upload_photo(bytes(file_bytes))
            
            if active_job["status"] == "awaiting_before":
                new_photos = active_job["before_photos"] + [public_url]
                update_job(active_job["id"], {"before_photos": new_photos})
                await send_message(chat_id, f"✅ BEFORE photo saved ({len(new_photos)} total). Send another, or type /clean.")
                
            elif active_job["status"] == "awaiting_after":
                new_photos = active_job["after_photos"] + [public_url]
                update_job(active_job["id"], {"after_photos": new_photos})
                await send_message(chat_id, f"✅ AFTER photo saved ({len(new_photos)} total). Send another, or type /done.")
                
        except Exception as e:
            print(f"Error: {e}")
            await send_message(chat_id, "❌ Upload failed. Please try again.")

    return {"status": "ok"}