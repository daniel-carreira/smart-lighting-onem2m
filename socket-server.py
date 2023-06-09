import asyncio
import websockets

# Store a set of connected clients
connected_clients = set()

async def handle_connection(websocket, path):
    # Add the new client to the connected_clients set
    connected_clients.add(websocket)

    try:
        # Handle incoming messages from the client
        async for message in websocket:
            print(f"Received message: {message}")

            # Broadcast the message to all connected clients
            for client in connected_clients:
                await client.send(message)
    finally:
        # Remove the client from the connected_clients set when the connection is closed
        connected_clients.remove(websocket)

async def start_server():
    # Create a WebSocket server
    server = await websockets.serve(handle_connection, 'localhost', 8081)

    print("WebSocket server listening in port 8081...")

    # Keep the server running indefinitely
    await server.wait_closed()

# Run the WebSocket server
asyncio.run(start_server())