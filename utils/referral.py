import httpx
from config import API_BASE

async def cek_syarat_referral(user_id: int) -> tuple[bool, int, int]:
    """
    Mengecek apakah user sudah memenuhi syarat referral.
    - Jika user sudah termasuk approved, return True.
    - Jika belum, hitung jumlah referral aktif dan target minimal (misal: 5).
    
    Returns:
        (bool) status_lolos,
        (int) jumlah_referral_aktif,
        (int) target_referral
    """
    async with httpx.AsyncClient() as client:
        try:
            # Cek apakah user sudah approved
            resp_approved = await client.get(f"{API_BASE}/approved/{user_id}")
            if resp_approved.status_code == 200 and resp_approved.json().get("approved"):
                return True, 0, 0
        except Exception:
            pass

        try:
            # Cek jumlah referral aktif user
            resp_ref = await client.get(f"{API_BASE}/referral/{user_id}")
            if resp_ref.status_code == 200:
                referral_data = resp_ref.json()
                aktif = len(referral_data.get("referral_list", []))
                target = 5  # bisa diubah sesuai kebutuhan
                return (aktif >= target), aktif, target
        except Exception:
            pass

    # Jika gagal request atau tidak memenuhi
    return False, 0, 5
