from django.test import SimpleTestCase

from project_x_backend.infrastructure.tasks import ping


class InfrastructureTaskTests(SimpleTestCase):
    def test_infrastructure_celery_ping_task(self):
        self.assertEqual(ping(), {"status": "ok"})
