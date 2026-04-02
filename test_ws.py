import asyncio
import json
import uuid
import websockets

async def test_chat():
    # Replace with the actual match ID from the API response
    match_id = "58395dcd-0639-40e5-899e-1fe15ebb61b4"
    uri = f"ws://localhost:8000/ws/chat/{match_id}/"
    
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri, additional_headers={"Origin": "http://localhost:5173"}) as websocket:
            print("Connected!")
            
            # 1. Wait for connection established message
            msg = await websocket.recv()
            print(f"< {msg}")
            
            # 2. Send Join payload
            join_payload = {
                "username": "TestUser",
                "team_supported": "CSK"
            }
            print(f"> {json.dumps(join_payload)}")
            await websocket.send(json.dumps(join_payload))
            
            # 3. Receive Chat History
            msg = await websocket.recv()
            print(f"< {msg}")
            
            # 4. Receive User Join event
            msg = await websocket.recv()
            print(f"< {msg}")
            
            # 5. Send Chat message
            chat_payload = {
                "username": "TestUser",
                "team": "CSK",
                "message": "Hello from automation!"
            }
            print(f"> {json.dumps(chat_payload)}")
            await websocket.send(json.dumps(chat_payload))
            
            # 6. Receive Broadcasted message
            msg = await websocket.recv()
            print(f"< {msg}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_chat())
