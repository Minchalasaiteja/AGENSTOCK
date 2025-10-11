from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from pymongo import MongoClient
from bson import ObjectId

from app.config import settings
from app.services.auth import get_current_active_user
from app.services.llm_service import llm_service
from app.services.stock_service import StockDataService
from app.utils.security import get_db

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def send_json(self, payload: dict, websocket: WebSocket):
        await websocket.send_text(json.dumps(payload))

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, db: MongoClient = Depends(get_db)):
    await manager.connect(websocket)
    # Send a welcome message
    welcome_message = {
        "type": "system",
        "content": "Hello! I'm AGENSTOCK, your AI financial assistant. How can I help you with your stock research today?"
    }
    await manager.send_personal_message(json.dumps(welcome_message), websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Save user message to database (ensure all required fields)
            session_id = message_data.get("session_id", "")
            chat_message = {
                "session_id": session_id,
                "user_id": user_id,
                "message_type": "user",
                "content": message_data.get("content", ""),
                "timestamp": datetime.utcnow(),
                "metadata": message_data.get("metadata", {})
            }
            db.chat_messages.insert_one(chat_message)
            # Update session's message count and timestamp
            # Match by session_id field (session ids are stored as strings in session_id)
            res = db.chat_sessions.update_one(
                {"session_id": session_id, "user_id": user_id},
                {"$inc": {"message_count": 1}, "$set": {"updated_at": datetime.utcnow()}},
                upsert=False
            )
            # Fallback: try matching by ObjectId if session_id looks like an ObjectId
            if res.matched_count == 0:
                try:
                    obj_id = ObjectId(session_id)
                    db.chat_sessions.update_one(
                        {"_id": obj_id, "user_id": user_id},
                        {"$inc": {"message_count": 1}, "$set": {"updated_at": datetime.utcnow()}},
                        upsert=False
                    )
                except Exception:
                    pass

            # Broadcast session update to all connected clients
            try:
                session_summary = db.chat_sessions.find_one({"session_id": session_id})
                if session_summary:
                    # Ensure we send both _id and session_id strings
                    session_summary["_id"] = str(session_summary.get("_id"))
                    session_summary["session_id"] = str(session_summary.get("session_id") or session_summary.get("_id"))
                    session_summary["updated_at"] = session_summary["updated_at"].isoformat() if isinstance(session_summary.get("updated_at"), datetime) else session_summary.get("updated_at")
                    await manager.broadcast(json.dumps({"type": "session_update", "session": session_summary}))
            except Exception:
                pass
            
            # --- Get AI response (Streaming) ---
            final_ai_content = ""
            context = "" # Context can be built here if needed for specific queries

            async with StockDataService() as stock_service:
                # For general chat, we now use the streaming endpoint
                response_stream = await llm_service.get_streaming_llm_response(
                    prompt=message_data.get("content"),
                    context=context, # You can build a context here for specific queries
                    conversation_history=message_data.get("history", [])
                )

                # Send response back to client chunk by chunk
                for chunk in response_stream:
                    if chunk.text:
                        chunk_text = chunk.text
                        final_ai_content += chunk_text
                        response_data = json.dumps({
                            "type": "stream",
                            "content": chunk_text
                        })
                        await manager.send_personal_message(response_data, websocket)

            # Send an end-of-stream message
            await manager.send_personal_message(json.dumps({"type": "stream_end"}), websocket)

            # Save AI response to database (ensure all required fields)
            ai_message = {
                "session_id": session_id,
                "user_id": user_id,
                "message_type": "ai",
                "content": final_ai_content if final_ai_content else "I am unable to respond at the moment.",
                "timestamp": datetime.utcnow(),
                "metadata": {"type": message_data.get("type", "")}
            }
            db.chat_messages.insert_one(ai_message)
            # Update session's message count and timestamp
            res2 = db.chat_sessions.update_one(
                {"session_id": session_id, "user_id": user_id},
                {"$inc": {"message_count": 1}, "$set": {"updated_at": datetime.utcnow()}},
                upsert=False
            )
            if res2.matched_count == 0:
                try:
                    obj_id = ObjectId(session_id)
                    db.chat_sessions.update_one(
                        {"_id": obj_id, "user_id": user_id},
                        {"$inc": {"message_count": 1}, "$set": {"updated_at": datetime.utcnow()}},
                        upsert=False
                    )
                except Exception:
                    pass

            # Broadcast session update after AI response
            try:
                session_summary = db.chat_sessions.find_one({"session_id": session_id})
                if session_summary:
                    session_summary["_id"] = str(session_summary.get("_id"))
                    session_summary["session_id"] = str(session_summary.get("session_id") or session_summary.get("_id"))
                    session_summary["updated_at"] = session_summary["updated_at"].isoformat() if isinstance(session_summary.get("updated_at"), datetime) else session_summary.get("updated_at")
                    await manager.broadcast(json.dumps({"type": "session_update", "session": session_summary}))
            except Exception:
                pass
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.get("/sessions")
async def get_chat_sessions(
    current_user: dict = Depends(get_current_active_user),
    user_id: Optional[str] = None,
    db = Depends(get_db)
):
    # Admins may request sessions for any user by passing user_id
    if getattr(current_user, 'get', False) and current_user.get('role') == 'admin' and user_id:
        target_user_id = user_id
    else:
        target_user_id = str(current_user["_id"])

    sessions = list(db.chat_sessions.find(
        {"user_id": target_user_id}
    ).sort("updated_at", -1))
    
    for session in sessions:
        session["_id"] = str(session["_id"])
        # Ensure session_id is always present and string
        session["session_id"] = str(session.get("session_id") or session["_id"])
        if isinstance(session.get("created_at"), datetime):
            session["created_at"] = session["created_at"].isoformat()
        if isinstance(session.get("updated_at"), datetime):
            session["updated_at"] = session["updated_at"].isoformat()
    
    return sessions

@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_db)
):
    from bson import ObjectId
    
    user_id_str = str(current_user["_id"])
    # Allow admins to fetch messages for any session; regular users can only fetch their own
    if current_user.get('role') == 'admin':
        query = {"session_id": session_id}
    else:
        query = {"session_id": session_id, "user_id": user_id_str}

    messages = list(db.chat_messages.find(query).sort("timestamp", 1))
    
    for message in messages:
        message["_id"] = str(message["_id"])
        if isinstance(message.get("timestamp"), datetime):
            message["timestamp"] = message["timestamp"].isoformat()
    
    return messages

@router.post("/sessions")
async def create_chat_session(
    session_data: dict,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_db)
):
    from bson import ObjectId
    
    new_session_id = ObjectId()
    session = {
        "_id": new_session_id,
        "user_id": str(current_user["_id"]),
        "title": session_data.get("title", "New Chat"),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "message_count": 0,
        "is_active": True,
        "session_id": str(new_session_id) # Add session_id field
    }
    
    db.chat_sessions.insert_one(session)
    
    # Return a dictionary that is JSON serializable
    return {"_id": str(new_session_id), "session_id": str(new_session_id), "title": session["title"]}

@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_db)
):
    from bson import ObjectId
    
    result = db.chat_sessions.delete_one({
        "_id": ObjectId(session_id),
        "user_id": str(current_user["_id"])
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Also delete associated messages
    db.chat_messages.delete_many({"session_id": session_id})
    
    return {"message": "Session deleted successfully"}