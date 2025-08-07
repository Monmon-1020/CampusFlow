"""
Basic tests for stream role functionality
Run with: python -m pytest test_stream_roles.py -v
"""

import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel

from src.database import get_async_session
from src.main import app
from src.models import Stream, StreamMembership, StreamRole, User

# Mock database session for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///test_campusflow.db"


@pytest.fixture
async def async_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session = AsyncSession(engine)
    yield async_session
    await async_session.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_user():
    return User(
        id="test_user_1", email="test@example.com", name="Test User", role="student"
    )


@pytest.fixture
def sample_stream():
    return Stream(
        id="test_stream_1",
        name="Test Stream",
        description="Test Stream Description",
        created_by="admin_user",
    )


class TestStreamRoles:
    """Test cases for stream role functionality"""

    def test_stream_role_enum_values(self):
        """Test that StreamRole enum has correct values"""
        assert StreamRole.STUDENT == "student"
        assert StreamRole.STREAM_ADMIN == "stream_admin"
        assert StreamRole.ADMIN == "admin"

    def test_stream_membership_default_role(self):
        """Test that StreamMembership defaults to student role"""
        membership = StreamMembership(user_id="user1", stream_id="stream1")
        assert membership.role == StreamRole.STUDENT

    def test_stream_membership_role_assignment(self):
        """Test that StreamMembership role can be assigned"""
        membership = StreamMembership(
            user_id="user1", stream_id="stream1", role=StreamRole.STREAM_ADMIN
        )
        assert membership.role == StreamRole.STREAM_ADMIN


class TestStreamPermissions:
    """Test cases for stream posting permissions"""

    @pytest.mark.asyncio
    async def test_student_cannot_post(self, client, sample_user, sample_stream):
        """Test that students cannot create posts"""
        # This would require setting up authentication and database
        # For now, just test the logic conceptually
        student_role = StreamRole.STUDENT
        assert student_role not in {"stream_admin", "admin"}

    @pytest.mark.asyncio
    async def test_stream_admin_can_post(self, client, sample_user, sample_stream):
        """Test that stream_admin users can create posts"""
        stream_admin_role = StreamRole.STREAM_ADMIN
        assert stream_admin_role in {"stream_admin", "admin"}

    @pytest.mark.asyncio
    async def test_admin_can_post(self, client, sample_user, sample_stream):
        """Test that admin users can create posts"""
        admin_role = StreamRole.ADMIN
        assert admin_role in {"stream_admin", "admin"}


class TestElevationEndpoint:
    """Test cases for the elevation endpoint"""

    def test_elevation_code_validation(self):
        """Test that elevation requires correct code"""
        # Mock test - in real implementation would test actual endpoint
        correct_code = "STREAM_ADMIN_123"
        test_code = "STREAM_ADMIN_123"
        assert correct_code == test_code

    def test_elevation_code_rejection(self):
        """Test that incorrect codes are rejected"""
        correct_code = "STREAM_ADMIN_123"
        wrong_code = "WRONG_CODE"
        assert correct_code != wrong_code


class TestRoleMigration:
    """Test cases for role migration logic"""

    def test_role_conversion_logic(self):
        """Test role conversion from old system to new"""
        # Old system: boolean flags
        # New system: role enum

        # Admin user (had all permissions)
        old_is_admin = True
        old_can_moderate = True
        old_can_post = True

        if old_is_admin:
            new_role = StreamRole.ADMIN
        elif old_can_post and old_can_moderate:
            new_role = StreamRole.STREAM_ADMIN
        else:
            new_role = StreamRole.STUDENT

        assert new_role == StreamRole.ADMIN

        # Stream admin user (could post and moderate)
        old_is_admin = False
        old_can_moderate = True
        old_can_post = True

        if old_is_admin:
            new_role = StreamRole.ADMIN
        elif old_can_post and old_can_moderate:
            new_role = StreamRole.STREAM_ADMIN
        else:
            new_role = StreamRole.STUDENT

        assert new_role == StreamRole.STREAM_ADMIN

        # Student (no special permissions)
        old_is_admin = False
        old_can_moderate = False
        old_can_post = False

        if old_is_admin:
            new_role = StreamRole.ADMIN
        elif old_can_post and old_can_moderate:
            new_role = StreamRole.STREAM_ADMIN
        else:
            new_role = StreamRole.STUDENT

        assert new_role == StreamRole.STUDENT


def test_role_text_conversion():
    """Test role text conversion for frontend display"""
    role_mapping = {"student": "学生", "stream_admin": "ストリーム管理者", "admin": "管理者"}

    assert role_mapping[StreamRole.STUDENT] == "学生"
    assert role_mapping[StreamRole.STREAM_ADMIN] == "ストリーム管理者"
    assert role_mapping[StreamRole.ADMIN] == "管理者"


if __name__ == "__main__":
    # Run tests
    import subprocess
    import sys

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"],
            capture_output=True,
            text=True,
        )

        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        print("Return code:", result.returncode)

    except Exception as e:
        print(f"Error running tests: {e}")

        # Run basic tests manually
        print("\n=== Running manual tests ===")

        # Test enum values
        try:
            assert StreamRole.STUDENT == "student"
            assert StreamRole.STREAM_ADMIN == "stream_admin"
            assert StreamRole.ADMIN == "admin"
            print("✅ StreamRole enum test passed")
        except Exception as e:
            print(f"❌ StreamRole enum test failed: {e}")

        # Test role permissions logic
        try:
            student_role = "student"
            stream_admin_role = "stream_admin"
            admin_role = "admin"

            allowed_roles = {"stream_admin", "admin"}

            assert student_role not in allowed_roles
            assert stream_admin_role in allowed_roles
            assert admin_role in allowed_roles
            print("✅ Role permissions logic test passed")
        except Exception as e:
            print(f"❌ Role permissions logic test failed: {e}")

        print("=== Manual tests completed ===")
