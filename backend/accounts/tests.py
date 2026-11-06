from rest_framework.test import APITestCase

from .models import User

PW = "Str0ngPass!234"


class AuthApiTests(APITestCase):
    def register(self, **extra):
        data = {"username": "ram", "email": "ram@example.com", "password": PW, "role": "seller"}
        data.update(extra)
        return self.client.post("/api/auth/register/", data, format="json")

    def test_register_returns_token_and_user(self):
        r = self.register()
        self.assertEqual(r.status_code, 201)
        self.assertTrue(r.data["token"])
        self.assertEqual(r.data["user"]["role"], "seller")

    def test_cannot_register_as_admin(self):
        r = self.register(role="admin")
        self.assertEqual(r.status_code, 400)
        self.assertFalse(User.objects.filter(username="ram").exists())

    def test_weak_password_rejected(self):
        r = self.register(password="12345678")
        self.assertEqual(r.status_code, 400)
        self.assertIn("password", r.data)

    def test_duplicate_username_rejected(self):
        self.register()
        self.assertEqual(self.register(email="x@example.com").status_code, 400)

    def test_login_and_me(self):
        self.register()
        r = self.client.post("/api/auth/login/", {"username": "ram", "password": PW}, format="json")
        self.assertEqual(r.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {r.data['token']}")
        me = self.client.get("/api/auth/me/")
        self.assertEqual(me.data["username"], "ram")

    def test_wrong_password_rejected(self):
        self.register()
        r = self.client.post("/api/auth/login/", {"username": "ram", "password": "nope"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_me_requires_login(self):
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 401)

    def test_logout_invalidates_token(self):
        token = self.register().data["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(self.client.post("/api/auth/logout/").status_code, 204)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 401)

    def test_superuser_gets_admin_role(self):
        u = User.objects.create_superuser("boss", "b@example.com", "pw12345678")
        self.assertEqual(u.role, "admin")
