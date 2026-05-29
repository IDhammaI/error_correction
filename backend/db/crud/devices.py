import uuid

from db.models import DeviceBinding, DeviceCapture


def create_device_binding(db, user_id: int) -> DeviceBinding:
    binding = DeviceBinding(device_uuid=str(uuid.uuid4()), user_id=user_id, is_active=True)
    db.add(binding)
    db.commit()
    db.refresh(binding)
    return binding


def get_active_device_binding(db, device_uuid: str) -> DeviceBinding | None:
    return (
        db.query(DeviceBinding)
        .filter(DeviceBinding.device_uuid == device_uuid, DeviceBinding.is_active == True)
        .first()
    )


def get_user_device_binding(db, user_id: int, device_uuid: str) -> DeviceBinding | None:
    return (
        db.query(DeviceBinding)
        .filter(
            DeviceBinding.user_id == user_id,
            DeviceBinding.device_uuid == device_uuid,
            DeviceBinding.is_active == True,
        )
        .first()
    )


def get_latest_user_device_binding(db, user_id: int) -> DeviceBinding | None:
    return (
        db.query(DeviceBinding)
        .filter(DeviceBinding.user_id == user_id, DeviceBinding.is_active == True)
        .order_by(DeviceBinding.created_at.desc(), DeviceBinding.id.desc())
        .first()
    )


def deactivate_user_device_binding(db, user_id: int, device_uuid: str) -> bool:
    binding = get_user_device_binding(db, user_id, device_uuid)
    if not binding:
        return False
    binding.is_active = False
    db.commit()
    return True


def create_device_capture(
    db,
    *,
    device_uuid: str,
    user_id: int,
    file_key: str,
    original_filename: str,
    file_path: str,
    content_type: str = "",
    file_size: int = 0,
) -> DeviceCapture:
    capture = DeviceCapture(
        device_uuid=device_uuid,
        user_id=user_id,
        file_key=file_key,
        original_filename=original_filename,
        file_path=file_path,
        content_type=content_type or "",
        file_size=file_size or 0,
    )
    db.add(capture)
    db.commit()
    db.refresh(capture)
    return capture


def get_device_captures(db, *, user_id: int, device_uuid: str | None = None, limit: int = 50):
    query = db.query(DeviceCapture).filter(DeviceCapture.user_id == user_id)
    if device_uuid:
        query = query.filter(DeviceCapture.device_uuid == device_uuid)
    return (
        query.order_by(DeviceCapture.created_at.desc(), DeviceCapture.id.desc())
        .limit(max(1, min(limit, 200)))
        .all()
    )


def get_device_captures_by_ids(db, *, user_id: int, ids: list[int]):
    if not ids:
        return []
    return (
        db.query(DeviceCapture)
        .filter(DeviceCapture.user_id == user_id, DeviceCapture.id.in_(ids))
        .order_by(DeviceCapture.created_at.desc(), DeviceCapture.id.desc())
        .all()
    )
