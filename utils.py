async def cek_syarat_referral(user_id: int) -> (bool, int, int):
    async with httpx.AsyncClient() as client:
        # Cek apakah user sudah approved
        try:
            r1 = await client.get(f"{API_BASE_URL}/approved/{user_id}")
            if r1.status_code == 200 and r1.json().get("approved"):
                return True, 0, 0
        except Exception:
            pass

        # Jika tidak approved, cek jumlah referral
        try:
            r2 = await client.get(f"{API_BASE_URL}/referral/{user_id}")
            if r2.status_code == 200:
                referral_data = r2.json()
                jumlah_referral = len(referral_data.get("referral_list", []))
                target = jumlah_referral + 5
                return False, jumlah_referral, target
        except Exception:
            pass

        return False, 0, 5
