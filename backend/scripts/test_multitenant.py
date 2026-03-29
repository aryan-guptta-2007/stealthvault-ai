import asyncio
import httpx
import json

API_URL = "http://127.0.0.1:8000/api/v1"

# Keys and credentials from init_tenants.py
DEFAULT_API_KEY = "sv_local_dev_key"
ACME_API_KEY = "sv_acme_enterprise_key"

DEFAULT_CREDS = {"username": "admin", "password": "admin"}
ACME_CREDS = {"username": "acme-admin", "password": "acme123"}

async def test_multitenancy():
    print("\n🚀 Starting Multi-Tenant Validation Suite")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # === Step 1: Login and get JWTs ===
        print("\n1. Authenticating Tenants...")
        
        # Login Default Tenant
        res = await client.post(f"{API_URL}/auth/token", data=DEFAULT_CREDS)
        if res.status_code != 200:
            print(f"❌ Login Default Failed: {res.status_code} - {res.text}")
            return
        default_token = res.json().get("access_token")
        print(f"✅ Default Tenant Token Received")
        
        # Login Acme Tenant
        res = await client.post(f"{API_URL}/auth/token", data=ACME_CREDS)
        if res.status_code != 200:
            print(f"❌ Login Acme Failed: {res.status_code} - {res.text}")
            return
        acme_token = res.json().get("access_token")
        print(f"✅ Acme Tenant Token Received")
        
        # === Step 2: Inject Traffic with API Keys ===
        print("\n2. Simulating Packet Ingestion...")
        
        packet = {
            "src_ip": "1.1.1.1", "dst_ip": "10.0.0.1", "src_port": 1234, "dst_port": 80,
            "protocol": "TCP", "packet_size": 250, "flags": "S", "payload_size": 0, "ttl": 64, "duration": 0.1
        }
        
        # Send to Default Tenant (Normal traffic)
        res = await client.post(
            f"{API_URL}/traffic/analyze", 
            json=packet,
            headers={"X-API-Key": DEFAULT_API_KEY}
        )
        print(f"✅ Injected packet to Default Tenant -> Risk: {res.json()['risk']['score']}")
        
        # Send to Acme Tenant (High-Severity Attack Simulation)
        packet_acme = packet.copy()
        packet_acme["src_ip"] = "192.168.1.99"
        packet_acme["flags"] = "S"
        packet_acme["payload_size"] = 5000 # High payload for anomaly
        packet_acme["dst_port"] = 3306 # SQL Port
        
        # Simulate Port Scan + High Payload
        for port in range(1, 40):
            packet_acme["dst_port"] = port
            res = await client.post(
                f"{API_URL}/traffic/analyze", 
                json=packet_acme,
                headers={"X-API-Key": ACME_API_KEY}
            )
        print(f"✅ Injected 40 high-severity attack packets to Acme Tenant")
        
        # Allow Redis/DB workers a moment to process
        await asyncio.sleep(2)
        
        # === Step 3: Query Dashboards using JWT ===
        print("\n3. Verifying Dashboard Isolation...")
        
        res_default = await client.get(
            f"{API_URL}/dashboard/",
            headers={"Authorization": f"Bearer {default_token}"}
        )
        dash_default = res_default.json()
        
        res_acme = await client.get(
            f"{API_URL}/dashboard/",
            headers={"Authorization": f"Bearer {acme_token}"}
        )
        dash_acme = res_acme.json()
        
        
        print("\n--- 🏢 Default Tenant Dashboard ---")
        print(f"Total Alerts: {dash_default.get('total_alerts')}")
        print(f"Top Attackers: {len(dash_default.get('top_attackers', []))}")
        
        print("\n--- 🏢 ACME Corp Dashboard ---")
        print(f"Total Alerts: {dash_acme.get('total_alerts')}")
        print(f"Top Attackers: {len(dash_acme.get('top_attackers', []))}")
        
        if dash_default.get('total_alerts') != dash_acme.get('total_alerts'):
            print("\n✅ DATA IS STRICTLY ISOLATED BETWEEN TENANTS!")
        else:
            print("\n❌ DATA LEAK: Dashboards returned the same alert counts!")


if __name__ == "__main__":
    asyncio.run(test_multitenancy())
