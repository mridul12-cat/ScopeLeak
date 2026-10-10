import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.models.project import Project
from backend.app.models.change_order import ChangeOrder
from backend.app.services.pdf_export_service import generate_change_order_pdf

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_change_order_creation_and_versioning(db_session):
    project = Project(name="Project Alpha", client_name="Client Alpha", currency="INR", default_hourly_rate=2000.0)
    db_session.add(project)
    db_session.commit()

    co1 = ChangeOrder(
        project_id=project.id,
        version=1,
        title="CO 1",
        status="draft",
        currency="INR",
        subtotal=16000.0,
        taxes=0.0,
        total=16000.0,
    )
    co1.line_items = [
        {"title": "Stripe", "hours": 8.0, "rate": 2000.0, "line_total": 16000.0}
    ]
    db_session.add(co1)
    db_session.commit()

    assert co1.version == 1
    assert co1.total == 16000.0
    assert len(co1.line_items) == 1

    # Version 2
    co2 = ChangeOrder(
        project_id=project.id,
        version=2,
        title="CO 2",
        status="ready_for_review",
        currency="INR",
        subtotal=26000.0,
        taxes=0.0,
        total=26000.0,
    )
    db_session.add(co2)
    db_session.commit()

    assert co2.version == 2

def test_change_order_pdf_export(db_session):
    project = Project(name="Northstar Redesign", client_name="Northstar Studio", currency="INR", default_hourly_rate=2000.0)
    db_session.add(project)
    db_session.commit()

    co = ChangeOrder(
        project_id=project.id,
        version=1,
        title="Stripe Checkout Integration",
        status="approved_by_freelancer",
        currency="INR",
        subtotal=16000.0,
        taxes=0.0,
        total=16000.0,
        assumptions="Sandbox API keys provided by client.",
        exclusions="Stripe processing fees.",
    )
    co.line_items = [
        {"title": "Stripe Checkout & Webhook Integration", "hours": 8.0, "rate": 2000.0, "line_total": 16000.0}
    ]
    db_session.add(co)
    db_session.commit()

    pdf_bytes = generate_change_order_pdf(co, project)
    assert len(pdf_bytes) > 500  # Valid non-empty PDF binary
    assert pdf_bytes.startswith(b"%PDF")
