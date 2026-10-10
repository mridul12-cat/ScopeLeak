import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.models.project import Project
from backend.app.models.contract import Contract
from backend.app.models.scope_item import ScopeItem
from backend.app.services.contract_extractor import extract_text_from_file

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_scope_item_creation_and_contract_linkage(db_session):
    project = Project(
        name="Test Project",
        client_name="Test Client",
        currency="USD",
        default_hourly_rate=150.0,
    )
    db_session.add(project)
    db_session.commit()

    contract = Contract(
        project_id=project.id,
        filename="Agreement.txt",
        content_hash="dummyhash123",
        extracted_text="Contract deliverables include responsive frontend.",
        processing_status="extracted",
    )
    db_session.add(contract)
    db_session.commit()

    item = ScopeItem(
        project_id=project.id,
        contract_id=contract.id,
        item_type="deliverable",
        description="Responsive frontend",
        normalized_description="Responsive design",
        source_clause_id="Clause 1.1",
        source_quote="Contract deliverables include responsive frontend.",
        page_number=1,
        review_status="pending",
    )
    db_session.add(item)
    db_session.commit()

    fetched = db_session.query(ScopeItem).filter(ScopeItem.id == item.id).first()
    assert fetched is not None
    assert fetched.project_id == project.id
    assert fetched.contract_id == contract.id
    assert fetched.source_clause_id == "Clause 1.1"
    assert fetched.review_status == "pending"

def test_baseline_review_confirmation(db_session):
    project = Project(name="P2", client_name="C2")
    db_session.add(project)
    db_session.commit()

    item = ScopeItem(
        project_id=project.id,
        item_type="exclusion",
        description="SEO optimization excluded",
        normalized_description="SEO excluded",
        review_status="pending",
    )
    db_session.add(item)
    db_session.commit()

    # User reviews and confirms
    item.review_status = "confirmed"
    db_session.commit()

    assert db_session.query(ScopeItem).filter(ScopeItem.id == item.id).first().review_status == "confirmed"
