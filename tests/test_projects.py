import pytest

from app.main import app

# class TestProjects:

#     def test_get_project_info(client, access_token,new_project):
#         headers = {"Authorization": f"Bearer {access_token}"}
#         response = client.get(f"/projects/{new_project['id']}/info", headers=headers)

#         assert response.status_code == 200
#         data = response.json()
#         assert "name" in data