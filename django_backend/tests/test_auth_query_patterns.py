"""Query pattern tests for auth repositories."""

from apps.accounts.repositories.auth_repository import AdminSessionRepository, AdminUserRepository


def test_admin_user_list_defers_password_hash_in_one_query(legacy_db, django_assert_num_queries):
    """Admin list should avoid selecting password_hash and use one query."""
    repository = AdminUserRepository()

    with django_assert_num_queries(1, using="legacy"):
        users = list(repository.list_users())

    assert users
    assert all("password_hash" in user.get_deferred_fields() for user in users)


def test_admin_sessions_select_admin_in_one_query(legacy_db, django_assert_num_queries):
    """Session list should load admin relationship without N+1 queries."""
    repository = AdminSessionRepository()

    with django_assert_num_queries(1, using="legacy"):
        sessions = list(repository.list_sessions())
        emails = [session.admin.email for session in sessions]

    assert sessions
    assert all(emails)
