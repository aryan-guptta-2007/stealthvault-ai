import httpx
import asyncio
import json

BASE_URL = "http://localhost:8000/api/v1"

async def verify_saas():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("--- Step 1: Register Tenant A ---")
        resp = await client.post(f"{BASE_URL}/saas/register", json={
            "tenant_name": "Tenant Alpha",
            "admin_username": "alpha_admin",
            "admin_password": "Password123!"
        })
        print(f"Status: {resp.status_code}")
        if resp.status_code == 201:
            data_a = resp.json()
            print("Successfully registered Tenant Alpha.")
        elif resp.status_code == 400:
            print("Tenant Alpha already exists. Skipping registration.")
        else:
            print(f"FAILED Step 1: {resp.text}")
            return

        print("\n--- Step 2: Login Tenant A ---")
        resp = await client.post(f"{BASE_URL}/auth/token", data={
            "username": "alpha_admin",
            "password": "Password123!"
        })
        print(f"Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"FAILED Step 2: {resp.text}")
            return
        token_a = resp.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        print("\n--- Step 3: Register Tenant B ---")
        resp = await client.post(f"{BASE_URL}/saas/register", json={
            "tenant_name": "Tenant Beta",
            "admin_username": "beta_admin",
            "admin_password": "Password123!"
        })
        print(f"Status: {resp.status_code}")
        if resp.status_code == 201:
             print("Successfully registered Tenant Beta.")
        elif resp.status_code == 400:
             print("Tenant Beta already exists. Skipping registration.")
        else:
             print(f"FAILED Step 3: {resp.text}")
             return

        print("\n--- Step 4: Login Tenant B ---")
        resp = await client.post(f"{BASE_URL}/auth/token", data={
            "username": "beta_admin",
            "password": "Password123!"
        })
        print(f"Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"FAILED Step 4: {resp.text}")
            return
        token_b = resp.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        print("\n--- Step 5: Test Isolation (Defender) ---")
        # Block IP 1.1.1.1 for Tenant A
        await client.post(f"{BASE_URL}/soc/defender/block", 
                         json={"ip": "1.1.1.1", "reason": "Test isolation"}, 
                         headers=headers_a)
        
        # Check Tenant A blocklist
        resp_a = await client.get(f"{BASE_URL}/soc/defender/blocklist", headers=headers_a)
        list_a = resp_a.json()["blocked_ips"]
        print(f"Tenant A Blocklist: {list_a}")

        # Check Tenant B blocklist (should be empty)
        resp_b = await client.get(f"{BASE_URL}/soc/defender/blocklist", headers=headers_b)
        list_b = resp_b.json()["blocked_ips"]
        print(f"Tenant B Blocklist: {list_b}")

        if "1.1.1.1" in list_a and "1.1.1.1" not in list_b:
            print("✅ ISOLATION VERIFIED: Tenant B list is clean.")
        else:
            print("❌ ISOLATION FAILED")

        print("\n--- Step 6: Test User Management ---")
        resp = await client.post(f"{BASE_URL}/saas/users", 
                                json={"username": "alpha_analyst", "password": "Password123!", "roles": ["soc_analyst"]}, 
                                headers=headers_a)
        print(f"Add User Status: {resp.status_code}")
        
        resp = await client.get(f"{BASE_URL}/saas/users", headers=headers_a)
        users = resp.json()
        print(f"Tenant A User Count: {len(users)}")
        
        if len(users) >= 2:
            print("✅ USER MANAGEMENT VERIFIED")
        else:
            print("❌ USER MANAGEMENT FAILED")

if __name__ == "__main__":
    asyncio.run(verify_saas())
