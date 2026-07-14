import uuid
import logging
from typing import List, Optional, Any, Union

from app.schemas.interaction import InteractionCreate, InteractionUpdate, InteractionInDB
from app.models.interaction import Interaction
from app.database.session import SessionLocal

logger = logging.getLogger(__name__)


# ── Firestore helpers ────────────────────────────────────────────────────────

def _to_firestore_dict(record: InteractionInDB) -> dict:
    """Convert a Pydantic InteractionInDB to a plain dict safe for Firestore."""
    data = record.dict()
    # Remove None values so Firestore doesn't store unnecessary nulls
    return {k: v for k, v in data.items() if v is not None}


def _firestore_write(doc_id: str, data: dict, merge: bool = False):
    """Fire-and-forget helper — logs but never raises so SQLite path is unaffected."""
    try:
        from app.core.firebase_client import get_firestore
        db = get_firestore()
        if db is None:
            logger.debug("Firestore client unavailable; skipping write for %s", doc_id)
            return
        ref = db.collection("interactions").document(doc_id)
        if merge:
            ref.set(data, merge=True)
        else:
            ref.set(data)
        logger.info("Firestore write OK — interactions/%s", doc_id)
    except Exception as exc:
        logger.warning("Firestore write failed for %s: %s", doc_id, exc)


# ── Repository ───────────────────────────────────────────────────────────────

class InteractionRepository:
    def get_all(self) -> List[InteractionInDB]:
        with SessionLocal() as session:
            items = session.query(Interaction).all()
            return [InteractionInDB.from_orm(item) for item in items]

    def get_by_id(self, id: str) -> Optional[InteractionInDB]:
        with SessionLocal() as session:
            item = session.query(Interaction).filter(Interaction.id == id).first()
            if item:
                return InteractionInDB.from_orm(item)
            return None

    def create(self, obj_in: InteractionCreate) -> InteractionInDB:
        new_id = str(uuid.uuid4())
        data = obj_in.dict()
        data["id"] = new_id
        db_obj = Interaction(**data)

        with SessionLocal() as session:
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
            result = InteractionInDB.from_orm(db_obj)

        # Mirror to Firestore (non-blocking, won't raise)
        _firestore_write(new_id, _to_firestore_dict(result))

        return result

    def update(self, id: str, obj_in: Union[InteractionUpdate, dict[str, Any]]) -> Optional[InteractionInDB]:
        with SessionLocal() as session:
            item = session.query(Interaction).filter(Interaction.id == id).first()
            if not item:
                return None

            update_data = obj_in.dict(exclude_unset=True) if hasattr(obj_in, 'dict') else obj_in
            for field, value in update_data.items():
                setattr(item, field, value)

            session.commit()
            session.refresh(item)
            result = InteractionInDB.from_orm(item)

        # Mirror update to Firestore (merge=True so only changed fields are updated)
        partial = {k: v for k, v in update_data.items() if v is not None}
        if partial:
            _firestore_write(id, partial, merge=True)

        return result


interaction_repo = InteractionRepository()
