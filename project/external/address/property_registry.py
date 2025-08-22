from external.client.a_pick import APickClient

def get_property_registry(full_addr: str) -> bytes:
    client = APickClient()
    try:
        full_addr = (full_addr or "").strip()
        registry_info = client.view_property_registry(full_addr=full_addr)

        data = registry_info.get("data") or {}
        if data.get("success") != 1:
            raise ValueError(f"등기부 생성 미완료: {data!r}")

        ic_id = int(data.get("ic_id") or 0)
        if not ic_id:
            raise ValueError("ic_id를 찾을 수 없습니다.")

        return client.download_property_registry(ic_id=ic_id, stream=False)
    finally:
        client.close()