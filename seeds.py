from sqlalchemy.orm import Session
from app.models.category import CategoryMaster, CategorySectionMaster

DEFAULTS = {
    "finance": {
        "name": "Finance",
        "sections": [
            ("bank_accounts", "Bank Accounts"),
            ("credit_cards", "Credit Cards"),
            ("investments", "Investment Accounts"),
        ]
    },
    "property": {
        "name": "Property",
        "sections": [
            ("real_estate", "Real Estate"),
            ("vehicles", "Vehicles"),
        ]
    },
    "passwords": {
        "name": "Passwords",
        "sections": [
            ("email_accounts", "Email Accounts"),
            ("banking", "Banking"),
            ("social", "Social Accounts"),
        ]
    },
}

def seed_categories(db: Session):
    # insert masters if missing
    for idx, (code, meta) in enumerate(DEFAULTS.items()):
        cat = db.query(CategoryMaster).filter(CategoryMaster.code==code).first()
        if not cat:
            cat = CategoryMaster(code=code, name=meta["name"], sort_index=idx)
            db.add(cat); db.flush()
            for s_idx, (s_code, s_name) in enumerate(meta["sections"]):
                db.add(CategorySectionMaster(category_id=cat.id, code=s_code, name=s_name, sort_index=s_idx))
    db.commit()
