# ForestOS Backend - Phase 1.2 Part 1 Checkpoint

**Date:** November 26, 2025  
**Status:** ✅ Complete  
**Phase:** API Endpoints - Core Features

---

## Overview

Phase 1.2 Part 1 implements the core API endpoints for the ForestOS automated plant care system, building upon the database foundation from Phase 1.1. This phase delivers a fully functional REST API for user authentication, plant catalog management, and user plant tracking.

---

## Accomplishments

### 1. API Dependencies Layer

Created reusable dependency functions for FastAPI endpoints:

#### Database Dependency (`Server/app/api/dependencies/database.py`)
```python
get_db() → Generator[Session, None, None]
```
- Provides database session to endpoints
- Automatic session cleanup
- Dependency injection pattern

#### Authentication Dependencies (`Server/app/api/dependencies/auth.py`)
```python
get_current_user(token, db) → User
get_current_active_user(current_user) → User
get_current_superuser(current_user) → User
get_optional_current_user(token, db) → Optional[User]
```
- JWT token validation and decoding
- User extraction from database
- Role-based access control
- Optional authentication support

**OAuth2 Configuration:**
- Token URL: `/api/auth/login`
- Algorithm: HS256
- Token expiry: 7 days (configurable)

### 2. Authentication Endpoints

**Router:** `Server/app/api/endpoints/auth.py`  
**Prefix:** `/api/auth`  
**Tag:** `authentication`

#### Endpoints Implemented:

**POST `/api/auth/register`**
- Creates new user account
- Email uniqueness validation
- Password hashing (BCrypt, cost factor 12)
- Returns: User object
- Status: 201 Created

**POST `/api/auth/login`**
- OAuth2 password flow
- Email + password authentication
- JWT token generation
- Returns: Access token + type
- Status: 200 OK

**POST `/api/auth/test-token`**
- Validates JWT token
- Returns: Current user object
- Requires: Valid bearer token

**Security Features:**
- Email format validation
- Password minimum length: 8 characters
- Inactive user check
- Credential validation with proper error messages

### 3. Plant Catalog Endpoints

**Router:** `Server/app/api/endpoints/plants.py`  
**Prefix:** `/api/plants`  
**Tag:** `plants`

#### Endpoints Implemented:

**GET `/api/plants/`**
- List plants with pagination
- Query parameters:
  - `skip`: Offset (default: 0)
  - `limit`: Max results (default: 100, max: 100)
  - `light_level`: Filter (low/medium/bright_indirect/bright_direct)
  - `growth_rate`: Filter (slow/medium/fast)
- Returns: PlantListResponse with pagination metadata
- Public endpoint (no auth required)

**GET `/api/plants/search`**
- Search plants by name
- Query parameters:
  - `q`: Search query (min 2 characters)
  - `limit`: Max results (default: 20)
- Searches: Scientific name (case-insensitive)
- Returns: List of matching plants
- Note: Common names search (JSON field) - TODO for future enhancement

**GET `/api/plants/{species_id}`**
- Get detailed plant information
- Path parameter: species_id (unique identifier)
- Returns: Complete plant care requirements
- Includes: Water, light, climate, toxicity, health indicators
- Status: 404 if not found

**GET `/api/plants/by-care-level/{care_level}`**
- Filter plants by difficulty
- Path parameter: easy|moderate|difficult
- Easy: Low light + infrequent watering (≥10 days)
- Moderate: Medium light + moderate watering (5-10 days)
- Difficult: Specific needs or frequent watering (<5 days)
- Returns: List of plants matching criteria

**Plant Data Structure:**
```json
{
  "species_id": "monstera_deliciosa_001",
  "common_names": ["Monstera", "Swiss Cheese Plant"],
  "scientific_name": "Monstera deliciosa",
  "water_frequency_days_min": 7,
  "water_frequency_days_max": 10,
  "soil_moisture_target_pct": 40,
  "light_level": "bright_indirect",
  "optimal_lux_min": 10000,
  "optimal_lux_max": 20000,
  "growth_rate": "fast",
  "toxicity_pets": "toxic to cats and dogs",
  "description": "...",
  "image_url": "https://..."
}
```

### 4. User Plant Management Endpoints

**Router:** `Server/app/api/endpoints/user_plants.py`  
**Prefix:** `/api/user-plants`  
**Tag:** `user-plants`  
**Authentication:** Required (all endpoints)

#### Endpoints Implemented:

**POST `/api/user-plants/`**
- Create new plant instance for user
- Request body: UserPlantCreate
  - species_id (required)
  - nickname (required)
  - location, pot_size, pot_material (optional)
  - custom_water_frequency_days (optional)
  - auto_water_enabled (default: true)
- Validates species exists in catalog
- Initializes last_watered to current time
- Returns: Created user plant
- Status: 201 Created

**GET `/api/user-plants/`**
- List all plants for current user
- Query parameters:
  - `skip`: Offset (default: 0)
  - `limit`: Max results (default: 100)
- Returns: UserPlantListResponse with pagination
- Filtered by user_id automatically

**GET `/api/user-plants/{plant_id}`**
- Get specific user plant details
- Path parameter: plant_id
- Validates plant belongs to current user
- Returns: Complete plant instance with care settings
- Status: 404 if not found or not owned

**PUT `/api/user-plants/{plant_id}`**
- Update plant information
- Request body: UserPlantUpdate (all fields optional)
- Updatable fields:
  - nickname, location
  - pot_size, pot_material
  - notes, is_active
  - custom_moisture targets
  - auto_watering_enabled
- Validates ownership
- Returns: Updated plant
- Status: 404 if not found/not owned

**DELETE `/api/user-plants/{plant_id}`**
- Remove plant from user's collection
- Path parameter: plant_id
- Validates ownership
- Hard delete from database
- Status: 204 No Content

**POST `/api/user-plants/{plant_id}/water`**
- Manual watering tracking
- Updates last_watered timestamp to current UTC time
- Used when user waters plant manually
- Helps system track watering history
- Returns: Updated plant with new timestamp

**User Plant Data Structure:**
```json
{
  "id": 123,
  "user_id": 1,
  "species_id": "monstera_deliciosa_001",
  "nickname": "My Monstera",
  "location": "Living room, east window",
  "pot_size": "medium",
  "pot_material": "terracotta",
  "last_watered": "2025-11-26T03:11:55Z",
  "auto_water_enabled": true,
  "is_active": true,
  "custom_water_frequency_days": null
}
```

### 5. Pydantic Schema Enhancements

Added missing response schemas for list endpoints:

**`Server/app/schemas/user.py`**
```python
UserResponse = User  # Alias for clarity
Token(BaseModel):
    access_token: str
    token_type: str
TokenData(BaseModel):
    user_id: Optional[int]
```

**`Server/app/schemas/plant.py`**
```python
PlantResponse = Plant
PlantListResponse(BaseModel):
    plants: List[PlantResponse]
    total: int
    skip: int
    limit: int
```

**`Server/app/schemas/user_plant.py`**
```python
UserPlantResponse = UserPlant
UserPlantListResponse(BaseModel):
    plants: list[UserPlantResponse]
    total: int
    skip: int
    limit: int
```

### 6. FastAPI Application Configuration

**File:** `Server/app/main.py`

**Application Setup:**
```python
app = FastAPI(
    title="ForestOS API",
    openapi_url="/api/openapi.json",
    debug=True  # Development mode
)
```

**CORS Middleware:**
```python
allow_origins = ["http://localhost:3000", "http://localhost:19006"]
allow_credentials = True
allow_methods = ["*"]
allow_headers = ["*"]
```

**Router Registration:**
```python
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(plants.router, prefix="/api/plants", tags=["plants"])
app.include_router(user_plants.router, prefix="/api/user-plants", tags=["user-plants"])
```

**Health Endpoints:**
- `GET /` - API info and status
- `GET /health` - Health check

**API Documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/api/openapi.json`

---

## File Structure

```
Server/app/
├── __init__.py
├── main.py                          # FastAPI application entry point
│
├── api/
│   ├── dependencies/
│   │   ├── __init__.py             # Exports get_db, get_current_user, etc.
│   │   ├── auth.py                 # Authentication dependencies (118 lines)
│   │   └── database.py             # Database session dependency (23 lines)
│   │
│   └── endpoints/
│       ├── __init__.py             # Exports routers
│       ├── auth.py                 # Authentication endpoints (108 lines)
│       ├── plants.py               # Plant catalog endpoints (127 lines)
│       └── user_plants.py          # User plant management (231 lines)
│
├── core/
│   ├── config.py                   # Settings (from Phase 1.1)
│   └── security.py                 # Password/JWT utilities (from Phase 1.1)
│
├── db/
│   ├── base.py                     # Base model (from Phase 1.1)
│   └── session.py                  # Session factory (from Phase 1.1)
│
├── models/                         # (All from Phase 1.1)
│   ├── __init__.py
│   ├── alert.py
│   ├── plant.py
│   ├── reading.py
│   ├── sensor.py
│   ├── user_plant.py
│   ├── user.py
│   └── watering.py
│
├── schemas/                        # Enhanced in Phase 1.2
│   ├── plant.py                    # Added PlantListResponse
│   ├── reading.py
│   ├── sensor.py
│   ├── user_plant.py               # Added UserPlantListResponse
│   └── user.py                     # Added Token, TokenData
│
├── services/                       # (Empty - for Phase 1.2 Part 2)
├── utils/                          # (Empty - for future use)
└── logs/                           # (Empty - for logging)
```

**Total Lines of Code (Phase 1.2 Part 1):**
- API endpoints: ~466 lines
- Dependencies: ~141 lines
- Schema additions: ~30 lines
- **Total new code: ~637 lines**

---

## API Design Patterns

### 1. Dependency Injection
All endpoints use FastAPI's dependency injection:
```python
@router.get("/")
def list_plants(
    skip: int = Query(0),
    db: Session = Depends(get_db)  # Injected
):
    ...
```

### 2. Authentication Flow
```python
@router.post("/")
def create_plant(
    plant_in: UserPlantCreate,
    current_user: User = Depends(get_current_active_user),  # Auto-validates token
    db: Session = Depends(get_db)
):
    ...
```

### 3. Error Handling
Consistent HTTP exception format:
```python
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Plant not found or doesn't belong to you"
)
```

### 4. Pagination Pattern
Standardized list responses:
```python
{
  "plants": [...],
  "total": 150,
  "skip": 0,
  "limit": 100
}
```

---

## Testing the API

### 1. Start the Server

```bash
cd /home/totalsmart/ForestOS/Server
source ../env/bin/activate
python -m uvicorn app.main:app --reload --port 8000
```

### 2. Access API Documentation

**Swagger UI:** http://localhost:8000/docs
- Interactive API testing
- Try out endpoints directly
- View request/response schemas

### 3. Sample API Flow

**Step 1: Register User**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123",
    "full_name": "John Doe"
  }'
```

**Step 2: Login**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=securepass123"
```
Response: `{"access_token": "eyJ...", "token_type": "bearer"}`

**Step 3: Browse Plants (No Auth)**
```bash
curl http://localhost:8000/api/plants/?limit=10
```

**Step 4: Create User Plant (With Auth)**
```bash
curl -X POST http://localhost:8000/api/user-plants/ \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{
    "species_id": "monstera_deliciosa_001",
    "nickname": "My Monstera",
    "location": "Living room"
  }'
```

**Step 5: Manual Watering**
```bash
curl -X POST http://localhost:8000/api/user-plants/1/water \
  -H "Authorization: Bearer eyJ..."
```

---

## Known Issues & Limitations

### 1. JSON Search Not Implemented
**Issue:** Plant search only covers scientific_name, not common_names (JSON field)

**Reason:** PostgreSQL JSON operators require special handling

**Workaround:** Search by scientific name only for now

**Future Fix:** Implement GIN index on common_names and use JSON containment operators

### 2. No Pagination Metadata Validation
**Issue:** Large skip/limit values could impact performance

**Current:** Max limit enforced (100), but no total page count

**Future Enhancement:** Add page count, has_more fields

### 3. Soft Delete Not Implemented
**Issue:** DELETE endpoints perform hard delete

**Impact:** No recovery if user accidentally deletes plant

**Future Enhancement:** Add is_deleted flag, implement soft delete

### 4. No Image Upload
**Issue:** Plant images are URLs only, no upload endpoint

**Future Enhancement:** Add image upload endpoint with S3/cloud storage

---

## Security Considerations

### Current Implementation

✅ **Password Security:**
- BCrypt hashing (cost factor 12)
- Never stored in plaintext
- Min 8 character requirement

✅ **JWT Tokens:**
- HS256 algorithm
- 7-day expiry
- Includes user ID in payload
- Validated on every protected endpoint

✅ **Authorization:**
- User can only access own plants
- Ownership validation on all CRUD operations
- Superuser role for future admin features

### Production Hardening Required

⚠️ **To Do Before Production:**
- [ ] Change SECRET_KEY (use `openssl rand -hex 32`)
- [ ] Enable HTTPS/TLS
- [ ] Add rate limiting (prevent brute force)
- [ ] Implement refresh tokens (reduce access token expiry)
- [ ] Add API key authentication for sensors
- [ ] Log security events (failed logins, etc.)
- [ ] Input sanitization for user-provided text
- [ ] Add CAPTCHA for registration

---

## Performance Considerations

### Database Query Optimization

**Current State:**
- Indexes on all foreign keys ✓
- Pagination on list endpoints ✓
- Explicit field selection (future optimization)

**Recommended Optimizations:**
```python
# Current: Loads all fields
plants = db.query(UserPlant).filter(...).all()

# Optimized: Load specific fields
plants = db.query(
    UserPlant.id,
    UserPlant.nickname,
    UserPlant.location
).filter(...).all()
```

### Caching Strategy (Phase 1.3)

**Candidates for Redis Caching:**
1. Plant catalog (rarely changes)
   - TTL: 24 hours
   - Key: `plant:{species_id}`

2. User plant list (changes on CRUD)
   - TTL: 5 minutes
   - Invalidate on create/update/delete

3. Latest sensor readings (Phase 1.2 Part 2)
   - TTL: 1 minute
   - High-frequency access

---

## Phase 1.2 Part 2 Preparation

The following are ready for Phase 1.2 Part 2 implementation:

✅ **Database models exist**
✅ **Pydantic schemas exist**
✅ **Authentication working**
✅ **CRUD patterns established**

### Next Steps for Phase 1.2 Part 2:

**1. Sensor Endpoints** (`/api/sensors`)
   - Register/pair new sensors (device_id, secret)
   - Update sensor status (battery, online/offline)
   - Get sensor readings (time-series data)
   - Sensor authentication (separate from user auth)

**2. Sensor Reading Endpoints** (`/api/readings`)
   - Submit new readings (from ESP32 devices)
   - Get latest readings for plant
   - Get historical data (time range query)
   - Aggregate data (hourly/daily averages)

**3. Watering Endpoints** (`/api/watering`)
   - Trigger automatic watering
   - Get watering history
   - Get watering recommendations
   - Schedule future watering

**4. Alert Endpoints** (`/api/alerts`)
   - List user alerts
   - Mark alerts as read
   - Dismiss alerts
   - Alert preferences

**5. Dashboard Endpoint** (`/api/dashboard`)
   - Overview statistics
   - Recent activity
   - Health summary
   - Upcoming tasks

---

## Lessons Learned

### 1. OAuth2 Password Flow
- Use `OAuth2PasswordRequestForm` for standard compliance
- Username field actually contains email
- Token response must include "token_type": "bearer"

### 2. Dependency Injection Benefits
- Cleaner code separation
- Easy to test (mock dependencies)
- Consistent authentication across endpoints

### 3. Pydantic Schema Design
- Use inheritance (Base → Create → Update → Response)
- Separate create/update schemas (different required fields)
- Response schemas separate from database models

### 4. FastAPI Router Organization
- One router per resource (auth, plants, user_plants)
- Logical prefix grouping (/api/resource)
- Tags for API documentation organization

### 5. Error Handling Consistency
- Always use HTTPException with proper status codes
- Descriptive error messages
- Include context (what was not found, why access denied)

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [OAuth2 Password Flow](https://oauth.net/2/grant-types/password/)
- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)
- [REST API Design](https://restfulapi.net/)

---

## Contact & Support

**Project:** ForestOS Automated Plant Care System  
**Phase:** 1.2 Part 1 - API Endpoints (Core Features)  
**Maintainer:** Development Team  
**Last Updated:** November 26, 2025

---

**Phase 1.2 Part 1 Status: ✅ COMPLETE AND READY FOR PART 2**
