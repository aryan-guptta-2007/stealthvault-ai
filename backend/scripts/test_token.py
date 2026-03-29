import httpx
import asyncio

async def test():
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(
                "http://127.0.0.1:8000/api/v1/auth/token",
                data={"username": "admin", "password": "admin"}
            )
            print(f"Default Status: {res.status_code}")
            
            res = await client.post(
                "http://127.0.0.1:8000/api/v1/auth/token",
                data={"username": "acme-admin", "password": "acme123"}
            )
            print(f"Acme Status: {res.status_code}")
            
            # test injection
            res = await client.post(
                "http://127.0.0.1:8000/api/v1/traffic/analyze",
                json={
                    "src_ip": "1.1.1.1", "dst_ip": "10.0.0.1", "src_port": 1234, "dst_port": 80,
                    "protocol": "TCP", "packet_size": 250, "flags": "S", "payload_size": 0, "ttl": 64, "duration": 0.1
                },
                headers={"X-API-Key": "sv_local_dev_key"}
            )
            print(f"Injection Status: {res.status_code}")
            print(f"Injection Body: {res.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
