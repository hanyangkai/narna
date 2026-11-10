#!/usr/bin/env python3
"""Database migration script for mobile API tables."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "web" / "backend"))

from app.database import Base, engine, init_db
from app.models import ApprovalRequest, MobileDevice


def main():
    """Create mobile API tables."""
    print("=" * 60)
    print("NARNA Mobile API - Database Migration")
    print("=" * 60)
    
    print("\nCreating/updating database tables...")
    
    try:
        # Create all tables (existing tables are skipped)
        Base.metadata.create_all(bind=engine)
        
        # Run migrations
        init_db()
        
        print("\n✅ Database migration completed successfully!")
        print("\nNew tables created:")
        print("  - mobile_devices: Store paired mobile device tokens")
        print("  - approval_requests: Store agent approval requests")
        
        # Verify tables exist
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print("\nVerifying tables...")
        if "mobile_devices" in tables:
            print("  ✅ mobile_devices table exists")
        else:
            print("  ❌ mobile_devices table NOT found")
        
        if "approval_requests" in tables:
            print("  ✅ approval_requests table exists")
        else:
            print("  ❌ approval_requests table NOT found")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
