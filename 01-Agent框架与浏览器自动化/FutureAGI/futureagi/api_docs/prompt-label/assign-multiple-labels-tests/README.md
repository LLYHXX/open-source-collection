# Assign Multiple Labels API - Test Documentation

This folder contains comprehensive API test documentation for the `assign-multiple-labels` endpoint.

## Endpoint

```
POST /model-hub/prompt-labels/assign-multiple-labels/
```

## Request Format

```json
{
  "template_version_id": "uuid",
  "label_ids": ["uuid1", "uuid2", ...]
}
```

## Success Response

```json
{
  "status": true,
  "result": "Labels assigned successfully"
}
```

## Error Response

```json
{
  "status": false,
  "result": "Error assigning multiple labels: <error_message>"
}
```

## Test Cases Overview

### ✅ Success Cases (8 tests)

| Test | File | Description |
|------|------|-------------|
| 01 | `01-assign-single-label.bru` | Assign a single label to a version |
| 02 | `02-assign-multiple-labels.bru` | Assign multiple labels at once |
| 03 | `03-assign-custom-labels.bru` | Assign custom organization labels |
| 04 | `04-assign-mixed-labels.bru` | Mix of system and custom labels |
| 05 | `05-labels-add-to-existing.bru` | Labels add to existing (not replace) |
| 06 | `06-all-system-labels.bru` | All three system labels at once |
| 07 | `07-large-number-labels.bru` | Assign 10+ labels (performance) |
| 08 | `08-idempotent-assignment.bru` | Same request twice (idempotency) |

### ❌ Error Cases (12 tests)

| Test | File | Description | Status Code |
|------|------|-------------|-------------|
| 09 | `09-empty-label-list.bru` | Empty label_ids array | 400 |
| 10 | `10-missing-template-version-id.bru` | Missing required field | 400 |
| 11 | `11-missing-label-ids.bru` | Missing required field | 400 |
| 12 | `12-invalid-version-id.bru` | Invalid UUID format | 400 |
| 13 | `13-nonexistent-version.bru` | Version doesn't exist | 400 |
| 14 | `14-nonexistent-label.bru` | Label doesn't exist | 400 |
| 15 | `15-mixed-valid-invalid-labels.bru` | Mix of valid/invalid labels | 400 |
| 16 | `16-deleted-label.bru` | Soft-deleted label | 400 |
| 17 | `17-deleted-version.bru` | Soft-deleted version | 400 |
| 18 | `18-cross-organization-label.bru` | Label from different org | 400 |
| 19 | `19-cross-organization-version.bru` | Version from different org | 400 |
| 20 | `20-unauthenticated.bru` | No authentication token | 401 |

## API Behavior

### Key Features

1. **Additive Assignment**: Labels are ADDED to existing labels, not replaced
2. **Exclusivity Within Template**: A label can only exist on one version per template
3. **Cross-Template Independence**: Same label can exist on versions from different templates
4. **Transaction Safety**: All-or-nothing behavior with automatic rollback on error
5. **Organization Isolation**: Users can only access their organization's resources
6. **Soft Delete Respect**: Deleted entities cannot be used

### Label Exclusivity Example

```
Template A:
  - Version v1: [Production, Staging]
  - Version v2: []

After: Assign [Production] to v2
  - Version v1: [Staging]          # Production removed
  - Version v2: [Production]       # Production added
```

### Additive Behavior Example

```
Version v2: [Development, Custom1]

After: Assign [Production, Staging] to v2
Version v2: [Development, Custom1, Production, Staging]  # All 4 labels
```

## Running Tests in Bruno

1. Import the `api_docs/prompt-label/assign-multiple-labels-tests/` folder into Bruno
2. Set up environment variables:
   ```
   host: http://localhost:8000
   access_token: <your_token>
   version_v1_id: <uuid>
   version_v2_id: <uuid>
   prod_label_id: <uuid>
   staging_label_id: <uuid>
   dev_label_id: <uuid>
   custom_label_1_id: <uuid>
   custom_label_2_id: <uuid>
   ```
3. Run tests sequentially or individually

## Automated Testing

The unit tests for this API are located at:
```
model_hub/tests/test_assign_multiple_labels.py
```

Run with:
```bash
docker-compose -f docker-compose.test.yml -p futureagi-test run --rm test-backend python -m pytest model_hub/tests/test_assign_multiple_labels.py -v
```

## Test Coverage Summary

- **Total API Tests**: 20
- **Success Scenarios**: 8 (40%)
- **Error Scenarios**: 12 (60%)
- **Authentication Tests**: 1
- **Validation Tests**: 6
- **Security Tests**: 2
- **Behavior Tests**: 11

## Notes

- All tests assume the use of Bearer token authentication
- Variable placeholders ({{variable}}) should be replaced with actual UUIDs
- Tests are designed to be run in sequence or independently
- Error messages may vary slightly based on implementation details
