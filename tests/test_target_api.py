"""Target API contract failures independent of external services."""
import unittest

try:
    from fastapi.testclient import TestClient

    from medmlops.serving import create_app
except ImportError as exc:
    raise unittest.SkipTest('Install requirements-target.lock for target API tests') from exc

TOKEN = 'test-only-target-token-123456'


class UnavailableGovernance:
    def active(self):
        raise ConnectionError('private database detail')


class TargetApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app(UnavailableGovernance(), TOKEN))
        self.headers = {'Authorization': f'Bearer {TOKEN}'}

    def test_health_auth_and_unavailable_deployment(self):
        self.assertEqual(self.client.get('/health').status_code, 200)
        self.assertEqual(self.client.get('/ready').status_code, 401)
        result = self.client.get('/ready', headers=self.headers)
        self.assertEqual(result.status_code, 503)
        self.assertNotIn('private', result.text)

    def test_schema_privacy_and_body_limit(self):
        result = self.client.post('/predict', headers=self.headers,
                                  json={'records': [{'patient_name': 'secret-name'}]})
        self.assertEqual(result.status_code, 422)
        self.assertNotIn('secret-name', result.text)
        result = self.client.post('/predict', headers=self.headers, content=b'x' * (1024 * 1024 + 1))
        self.assertEqual(result.status_code, 413)

    def test_metrics_and_correlation_bounded(self):
        result = self.client.get('/health', headers={'X-Correlation-ID': 'invalid value'})
        self.assertEqual(len(result.headers['X-Correlation-ID']), 32)
        self.assertIn('medmlops_requests_total', self.client.get('/metrics').text)

    def test_no_default_token(self):
        with self.assertRaises(ValueError):
            create_app(UnavailableGovernance(), 'short')

    def test_non_ascii_bearer_is_unauthorized(self):
        result = self.client.get('/ready', headers={
            b'Authorization': b'Bearer \xc3\xa9'})
        self.assertEqual(result.status_code, 401)

    def test_registry_version_rejects_paths_before_network_access(self):
        from medmlops.tracking import version_id
        for value in (None, '../1', '/tmp/model', '0', '-1', '1/2', '1;echo', '01'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                version_id(value)
        self.assertEqual(version_id(12), '12')

    def test_openapi_documents_bearer_authentication(self):
        schema = self.client.get('/openapi.json').json()
        self.assertEqual(schema['components']['securitySchemes']['HTTPBearer']['scheme'], 'bearer')
        self.assertEqual(schema['paths']['/predict']['post']['security'], [{'HTTPBearer': []}])
