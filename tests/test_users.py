"""Portal accounts (app/users.py + app/auth.py): the .env admin, users.json
accounts, the admin-only Users page, self-service password change, and the
rule that the LLM API key only ever comes from the form."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from app import rgroups_tool, users
from app.config import Config

ADMIN, ADMIN_PW = "boss", "env-admin-password"


class UsersTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self._saved = {k: getattr(Config, k) for k in (
            "DATA_DIR", "COACHINGS_DIR", "COACHING_FILES_DIR", "PATIENT_MODELS_DIR",
            "APP_USERNAME", "APP_PASSWORD", "SECRET_KEY")}
        Config.DATA_DIR = self.tmp
        Config.COACHINGS_DIR = self.tmp / "coachings"
        Config.COACHING_FILES_DIR = self.tmp / "coachings" / "files"
        Config.PATIENT_MODELS_DIR = self.tmp / "patient_models"
        Config.APP_USERNAME, Config.APP_PASSWORD = ADMIN, ADMIN_PW
        Config.SECRET_KEY = "test-secret"
        from app import create_app
        self.app = create_app()
        self.app.config["SECRET_KEY"] = "test-secret"

    def tearDown(self):
        for k, v in self._saved.items():
            setattr(Config, k, v)
        shutil.rmtree(self.tmp)

    def client(self, username=None, password=None):
        c = self.app.test_client()
        if username:
            r = c.post("/login", data={"username": username, "password": password})
            self.assertEqual(r.status_code, 302, f"login failed for {username}")
        return c


class StoreTest(UsersTestBase):
    def test_create_and_authenticate_stores_only_a_hash(self):
        users.create_user("advisor", "a-long-password", "user", created_by=ADMIN)
        self.assertEqual(users.authenticate("advisor", "a-long-password"),
                         {"username": "advisor", "is_admin": False})
        self.assertIsNone(users.authenticate("advisor", "wrong-password"))
        raw = (self.tmp / "users.json").read_text()
        self.assertNotIn("a-long-password", raw)
        self.assertIn("password_hash", raw)

    def test_env_admin_authenticates_and_cannot_be_shadowed(self):
        self.assertTrue(users.authenticate(ADMIN, ADMIN_PW)["is_admin"])
        with self.assertRaises(users.UserError):
            users.create_user(ADMIN, "another-password", "user", created_by=ADMIN)
        with self.assertRaises(users.UserError):
            users.delete_user(ADMIN)
        with self.assertRaises(users.UserError):
            users.set_password(ADMIN, "another-password")

    def test_validation(self):
        for bad in ("a", "has space", "x" * 41, "semi;colon"):
            with self.assertRaises(users.UserError, msg=bad):
                users.create_user(bad, "a-long-password", "user", created_by=ADMIN)
        with self.assertRaises(users.UserError):
            users.create_user("shorty", "short", "user", created_by=ADMIN)
        with self.assertRaises(users.UserError):
            users.create_user("roleless", "a-long-password", "superuser", created_by=ADMIN)
        users.create_user("dup", "a-long-password", "user", created_by=ADMIN)
        with self.assertRaises(users.UserError):
            users.create_user("dup", "a-long-password", "user", created_by=ADMIN)


class PagesTest(UsersTestBase):
    def test_admin_creates_account_and_sees_password_once(self):
        admin = self.client(ADMIN, ADMIN_PW)
        r = admin.post("/users", data={"username": "advisor", "password": "", "role": "user"})
        self.assertEqual(r.status_code, 200)
        page = r.get_data(as_text=True)
        self.assertIn("Account created:", page)
        pw = page.split('<code class="secret">')[1].split("</code>")[0]
        self.assertGreaterEqual(len(pw), users.MIN_PASSWORD_LEN)
        self.assertNotIn(pw, admin.get("/users").get_data(as_text=True))
        self.client("advisor", pw)  # the generated password logs in

    def test_non_admin_gets_403_and_no_users_link(self):
        users.create_user("advisor", "a-long-password", "user", created_by=ADMIN)
        c = self.client("advisor", "a-long-password")
        self.assertEqual(c.get("/users").status_code, 403)
        self.assertEqual(c.post("/users", data={"username": "x1", "role": "admin"}).status_code, 403)
        self.assertNotIn("/users", c.get("/account").get_data(as_text=True).split("<main")[0])
        self.assertFalse(users.exists("x1"))

    def test_user_with_admin_role_can_manage(self):
        users.create_user("deputy", "a-long-password", "admin", created_by=ADMIN)
        c = self.client("deputy", "a-long-password")
        self.assertEqual(c.get("/users").status_code, 200)

    def test_change_own_password(self):
        users.create_user("advisor", "a-long-password", "user", created_by=ADMIN)
        c = self.client("advisor", "a-long-password")
        c.post("/account", data={"current_password": "wrong-one-here",
                                 "new_password": "brand-new-password",
                                 "new_password_again": "brand-new-password"})
        self.assertIsNotNone(users.authenticate("advisor", "a-long-password"))
        c.post("/account", data={"current_password": "a-long-password",
                                 "new_password": "brand-new-password",
                                 "new_password_again": "brand-new-password"})
        self.assertIsNone(users.authenticate("advisor", "a-long-password"))
        self.assertIsNotNone(users.authenticate("advisor", "brand-new-password"))

    def test_deleted_user_is_logged_out_on_next_request(self):
        users.create_user("advisor", "a-long-password", "user", created_by=ADMIN)
        c = self.client("advisor", "a-long-password")
        self.assertEqual(c.get("/coachings").status_code, 200)
        self.client(ADMIN, ADMIN_PW).post("/users/advisor/delete")
        self.assertEqual(c.get("/coachings").status_code, 302)

    def test_reset_shows_new_password(self):
        users.create_user("advisor", "a-long-password", "user", created_by=ADMIN)
        r = self.client(ADMIN, ADMIN_PW).post("/users/advisor/reset")
        pw = r.get_data(as_text=True).split('<code class="secret">')[1].split("</code>")[0]
        self.assertIsNotNone(users.authenticate("advisor", pw))
        self.assertIsNone(users.authenticate("advisor", "a-long-password"))

    def test_session_cookie_is_lax_and_httponly(self):
        r = self.app.test_client().post("/login", data={"username": ADMIN, "password": ADMIN_PW})
        cookie = r.headers.get("Set-Cookie", "")
        self.assertIn("SameSite=Lax", cookie)
        self.assertIn("HttpOnly", cookie)


class ApiKeyTest(UsersTestBase):
    def test_no_job_without_a_typed_key(self):
        # even with a key in the environment, the portal never falls back to it
        with self.assertRaises(ValueError):
            rgroups_tool.start_expand_job("any", "claude", 1, "")
        with self.assertRaises(ValueError):
            rgroups_tool.start_expand_job("any", "claude", 1, "   ")


if __name__ == "__main__":
    unittest.main()
