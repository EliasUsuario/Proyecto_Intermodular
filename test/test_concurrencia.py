import asyncio
import httpx

BASE_URL = "http://127.0.0.1:8000"

async def login(client, email, password):
    r = await client.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    return r.json()["access_token"]

async def pedir_maquina(client, nombre, token, id_maquina):
    r = await client.post(
        f"{BASE_URL}/maquinas/{id_maquina}/prestamo",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"[{nombre}] Código: {r.status_code} -> {r.json()}")

async def main():
    async with httpx.AsyncClient() as client:
        token_laura = await login(client, "laura@gestormaterial.com", "laura1234")
        token_pedro = await login(client, "pedro@gestormaterial.com", "pedro1234")

        print("=== Prueba de concurrencia: 2 peticiones simultáneas sobre máquina 4 ===")
        await asyncio.gather(
            pedir_maquina(client, "Laura", token_laura, 4),
            pedir_maquina(client, "Pedro", token_pedro, 4),
        )

if __name__ == "__main__":
    asyncio.run(main())