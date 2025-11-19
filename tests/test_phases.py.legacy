"""Tests for tournament phases logic."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import magic_link_auth
from app.config import settings
from app.routers.phases import TournamentPhase, get_next_phase, get_previous_phase


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def admin_session():
    """Create admin session cookie."""
    token = magic_link_auth.generate_token("admin@battle-d.com", "admin")
    return {settings.SESSION_COOKIE_NAME: token}


class TestPhaseNavigation:
    """Tests for phase navigation logic."""

    def test_phase_sequence(self):
        """Test correct phase sequence."""
        phases = list(TournamentPhase)
        assert phases[0] == TournamentPhase.REGISTRATION
        assert phases[1] == TournamentPhase.PRESELECTION
        assert phases[2] == TournamentPhase.POOLS
        assert phases[3] == TournamentPhase.FINALS
        assert phases[4] == TournamentPhase.COMPLETED

    def test_get_next_phase_from_registration(self):
        """Test getting next phase from registration."""
        next_phase = get_next_phase(TournamentPhase.REGISTRATION)
        assert next_phase == TournamentPhase.PRESELECTION

    def test_get_next_phase_from_preselection(self):
        """Test getting next phase from preselection."""
        next_phase = get_next_phase(TournamentPhase.PRESELECTION)
        assert next_phase == TournamentPhase.POOLS

    def test_get_next_phase_from_pools(self):
        """Test getting next phase from pools."""
        next_phase = get_next_phase(TournamentPhase.POOLS)
        assert next_phase == TournamentPhase.FINALS

    def test_get_next_phase_from_finals(self):
        """Test getting next phase from finals."""
        next_phase = get_next_phase(TournamentPhase.FINALS)
        assert next_phase == TournamentPhase.COMPLETED

    def test_get_next_phase_from_completed(self):
        """Test getting next phase from completed (should be None)."""
        next_phase = get_next_phase(TournamentPhase.COMPLETED)
        assert next_phase is None

    def test_get_previous_phase_from_registration(self):
        """Test getting previous phase from registration (should be None)."""
        prev_phase = get_previous_phase(TournamentPhase.REGISTRATION)
        assert prev_phase is None

    def test_get_previous_phase_from_preselection(self):
        """Test getting previous phase from preselection."""
        prev_phase = get_previous_phase(TournamentPhase.PRESELECTION)
        assert prev_phase == TournamentPhase.REGISTRATION

    def test_get_previous_phase_from_pools(self):
        """Test getting previous phase from pools."""
        prev_phase = get_previous_phase(TournamentPhase.POOLS)
        assert prev_phase == TournamentPhase.PRESELECTION

    def test_get_previous_phase_from_finals(self):
        """Test getting previous phase from finals."""
        prev_phase = get_previous_phase(TournamentPhase.FINALS)
        assert prev_phase == TournamentPhase.POOLS

    def test_get_previous_phase_from_completed(self):
        """Test getting previous phase from completed."""
        prev_phase = get_previous_phase(TournamentPhase.COMPLETED)
        assert prev_phase == TournamentPhase.FINALS


class TestPhaseProgression:
    """Tests for phase progression through API."""

    def test_initial_phase_is_registration(self, client, admin_session):
        """Test tournament starts in registration phase."""
        # Reset phase to registration
        from app.routers import phases as phases_module

        phases_module.CURRENT_PHASE = TournamentPhase.REGISTRATION

        response = client.get("/phases/current", cookies=admin_session)
        data = response.json()
        assert data["phase"] == "registration"

    def test_advance_through_all_phases(self, client, admin_session):
        """Test advancing through all tournament phases."""
        # Reset to registration
        from app.routers import phases as phases_module

        phases_module.CURRENT_PHASE = TournamentPhase.REGISTRATION

        expected_sequence = [
            "registration",
            "preselection",
            "pools",
            "finals",
            "completed",
        ]

        for i, expected_phase in enumerate(expected_sequence):
            # Check current phase
            response = client.get("/phases/current", cookies=admin_session)
            assert response.json()["phase"] == expected_phase

            # Advance to next phase (if not last)
            if i < len(expected_sequence) - 1:
                response = client.post("/phases/advance", cookies=admin_session)
                assert response.status_code == 200

    def test_cannot_advance_beyond_completed(self, client, admin_session):
        """Test cannot advance beyond completed phase."""
        # Set to completed phase
        from app.routers import phases as phases_module

        phases_module.CURRENT_PHASE = TournamentPhase.COMPLETED

        response = client.post("/phases/advance", cookies=admin_session)
        data = response.json()
        assert "already completed" in data["message"].lower()
        assert data["phase"] == "completed"

    def test_go_back_through_phases(self, client, admin_session):
        """Test going back through phases."""
        # Start at finals
        from app.routers import phases as phases_module

        phases_module.CURRENT_PHASE = TournamentPhase.FINALS

        # Go back to pools
        response = client.post("/phases/go-back", cookies=admin_session)
        assert response.status_code == 200
        assert response.json()["phase"] == "pools"

        # Go back to preselection
        response = client.post("/phases/go-back", cookies=admin_session)
        assert response.status_code == 200
        assert response.json()["phase"] == "preselection"

        # Go back to registration
        response = client.post("/phases/go-back", cookies=admin_session)
        assert response.status_code == 200
        assert response.json()["phase"] == "registration"

    def test_cannot_go_back_from_registration(self, client, admin_session):
        """Test cannot go back from registration phase."""
        # Set to registration
        from app.routers import phases as phases_module

        phases_module.CURRENT_PHASE = TournamentPhase.REGISTRATION

        response = client.post("/phases/go-back", cookies=admin_session)
        data = response.json()
        assert "already at registration" in data["message"].lower()
        assert data["phase"] == "registration"

    def test_phases_overview_page(self, client, admin_session):
        """Test phases overview page renders correctly."""
        response = client.get("/phases/", cookies=admin_session)
        assert response.status_code == 200

        content = response.content.decode()
        assert "Tournament Phases" in content
        assert "Registration" in content
        assert "Preselection" in content
        assert "Pools" in content
        assert "Finals" in content
        assert "Completed" in content

    def test_phases_overview_shows_current_phase(self, client, admin_session):
        """Test overview page highlights current phase."""
        from app.routers import phases as phases_module

        # Set to pools phase
        phases_module.CURRENT_PHASE = TournamentPhase.POOLS

        response = client.get("/phases/", cookies=admin_session)
        content = response.content.decode()

        assert "POOLS" in content
        assert "Current Phase" in content
