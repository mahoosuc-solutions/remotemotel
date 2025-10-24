"""Lead creation for potential guests"""
import logging
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

async def create_lead(
    full_name: str,
    email: str,
    phone: str,
    check_in: str = None,
    check_out: str = None,
    adults: int = 2,
    source: str = "voice_ai",
    notes: str = None
) -> Dict[str, Any]:
    """
    Create a lead for potential booking

    Args:
        full_name: Guest's full name
        email: Guest's email
        phone: Guest's phone number
        check_in: Desired check-in date (optional)
        check_out: Desired check-out date (optional)
        adults: Number of adults
        source: Lead source (voice_ai, web, phone, etc.)
        notes: Additional notes

    Returns:
        Lead information including ID
    """
    try:
        from packages.hotel.models import Lead, LeadStatus
        from mcp_servers.shared.database import DatabaseManager

        logger.info(f"Creating lead for {full_name}, {email}")

        # Initialize database
        db = DatabaseManager(business_module="hotel")
        db.create_tables()

        with db.get_session() as session:
            # Parse name
            name_parts = full_name.strip().split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""

            # Create lead
            lead = Lead(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                check_in_date=check_in,
                check_out_date=check_out,
                adults=adults,
                source=source,
                status=LeadStatus.NEW,
                notes=notes,
                created_at=datetime.utcnow()
            )

            session.add(lead)
            session.commit()
            session.refresh(lead)

            result = {
                "success": True,
                "lead_id": f"LD{lead.id:05d}",
                "status": "saved",
                "name": full_name,
                "email": email,
                "phone": phone,
                "created_at": lead.created_at.isoformat()
            }

            logger.info(f"Lead created successfully: LD{lead.id:05d}")
            return result

    except Exception as e:
        logger.error(f"Error creating lead: {e}", exc_info=True)

        # Fallback to mock if database fails
        return {
            "success": False,
            "error": str(e),
            "lead_id": "LD-MOCK",
            "status": "failed"
        }
