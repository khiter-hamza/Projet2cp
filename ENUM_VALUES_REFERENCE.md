# API Enum Values Reference

This document lists the correct enum values required by the API endpoints.

## User Roles
Use one of these values for the `role` field when registering users:

- `chercheur` - Regular researcher/user
- `assistant_dpgr` - Assistant department manager
- `admin_dpgr` - Admin department manager
- `super_admin` - Super administrator

**Example**:
```json
{
  "email": "researcher@test.com",
  "role": "chercheur"
}
```

## User Grades
Use one of these values for the `grade` field when registering users:

- `professeur` - Professor
- `mca_a` - Maitre de Conferences Class A
- `mca_b` - Maitre de Conferences Class B
- `enseignant_chercheur` - Teacher-Researcher
- `doctorant_salarie` - Salaried PhD Student
- `doctorant_non_salarie` - Non-Salaried PhD Student

**Example**:
```json
{
  "email": "researcher@test.com",
  "grade": "professeur"
}
```

## Countries
Use one of these values for the `destination_country` field when creating applications:

- `algerie` - Algeria
- `france` - France
- `allemagne` - Germany
- `tunisie` - Tunisia

**Example**:
```json
{
  "destination_country": "france",
  "destination_city": "Paris"
}
```

## Application Status
These are the possible values for the `status` field:

- `draft` - Draft (not submitted)
- `submitted` - Submitted for review
- `cs_preparation` - Ready for CS deliberation
- `approved` - Approved by CS
- `completed` - Completed
- `closed` - Closed
- `rejected` - Rejected
- `cancelled` - Cancelled by user

## Stage Type
Use one of these values for the `stage_type` field:

- `stage_perfectionnement` - Training internship
- `sejour_scientifique` - Scientific stay

## CS Decision
Values for CS decisions:

- `approuve` - Approved
- `rejete` - Rejected

## Document Types
Supported document types for uploads:

- `invitation` - Invitation letter
- `passport` - Passport copy
- `cv` - Curriculum Vitae
- `programme` - Research program
- `accord_labo` - Laboratory agreement
- `ordre_mission` - Mission order
- `report` - Final report
- `attestation` - Certificate/Attestation

## Common Mistakes

❌ **Wrong**: Using English names
```json
{ "role": "researcher", "grade": "Professor" }
```

✅ **Correct**: Using French/system enum values
```json
{ "role": "chercheur", "grade": "professeur" }
```

❌ **Wrong**: Using country codes
```json
{ "destination_country": "FR" }
```

✅ **Correct**: Using full country names in lowercase
```json
{ "destination_country": "france" }
```

## Default Test Credentials

### Researcher
```json
{
  "email": "researcher@test.com",
  "username": "researcher_user",
  "lastname": "Test",
  "password": "TestPassword123!",
  "role": "chercheur",
  "grade": "professeur",
  "anciente": 5,
  "laboratory_name": "Lab1"
}
```

### Admin
```json
{
  "email": "admin@test.com",
  "username": "admin_user",
  "lastname": "Admin",
  "password": "AdminPassword123!",
  "role": "admin_dpgr",
  "grade": "professeur",
  "anciente": 10,
  "laboratory_name": "Admin_Lab"
}
```

## Registration Example

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "user123",
    "lastname": "Surname",
    "password": "SecurePassword123!",
    "role": "chercheur",
    "grade": "professeur",
    "anciente": 5,
    "laboratory_name": "Lab Name"
  }'
```

## Application Creation Example

```bash
curl -X POST http://localhost:8000/api/v1/applications/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "destination_country": "france",
    "destination_city": "Paris",
    "host_institution": "University of Paris",
    "scientific_objective": "Research objectives",
    "start_date": "2024-02-20",
    "end_date": "2024-03-20"
  }'
```

## Troubleshooting

### Error: "Input should be 'chercheur', 'assistant_dpgr', 'admin_dpgr' or 'super_admin'"
This means you're using an incorrect role value. Use one of the correct values listed above.

### Error: "Input should be 'professeur', 'mca_a', 'mca_b', 'enseignant_chercheur', 'doctorant_salarie' or 'doctorant_non_salarie'"
This means you're using an incorrect grade value. Use one of the correct values listed above.

### Error: When creating an application with invalid destination_country
Ensure you're using the full lowercase country name (e.g., "france" not "FR").

## Notes

- All enum values are case-sensitive
- Roles and grades follow French naming conventions
- Country names should be lowercase
- Document types should match the exact names listed
