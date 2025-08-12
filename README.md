# **API Contract**

## **Authentication**

All endpoints (except `/auth/login` and `/auth/sign_up`) require authentication via a JSON Web Token (JWT) in the `Authorization` header:

```
Authorization: Bearer <jwt_token>
```

* The token is obtained by sending valid credentials to `/auth/login`.
* On each request, the server validates the token and extracts `user_id` from its payload.
* If the token is invalid or expired, the server returns `401 Unauthorized`.

---

## **/auth**

### **POST /auth/sign\_up**

**Description:** Create a new user account.

**Input Parameters:**

* `login` *(string)* – Login not existing in database.
* `password` *(string)* – User’s password.

**Example Request:**

```json
POST /auth/sign_up
{
    "login": "user_1",
    "password": "VerySafePass123"
}
```

**Status Codes:**

* `201 Created`
* `400 Bad Request` – Login already exists.

---

### **POST /auth/login**

**Description:** Authenticate user and receive JWT token.

**Input Parameters:**

* `login` *(string)* – Login existing in database.
* `password` *(string)* – Correct password.

**Output Parameters:**

* `jwt_token` *(string)* – JWT token for authenticating further requests.

**Example Request/Response:**

```json
POST /auth/login
{
    "login": "user_1",
    "password": "VerySafePass123"
}

Response:
{
    "jwt_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ..."
}
```

**Status Codes:**

* `200 OK`
* `401 Unauthorized` – Invalid credentials.

---

## **/projects**

### **GET /projects**

**Description:** Get all projects accessible for the authenticated user (owned + shared), including project details and associated documents.

**Headers:**

```
Authorization: Bearer <jwt_token>
```

**Response:**

```json
[
  {
    "id": "uuid",
    "name": "Project Alpha",
    "description": "Project description",
    "owner_id": "uuid",
    "created_at": "2025-08-11T10:00:00Z",
    "documents": [
      {
        "id": "uuid",
        "name": "design.pdf",
        "uploaded_at": "2025-08-11T12:00:00Z"
      }
    ]
  }
]
```

**Status Codes:**

* `200 OK`
* `401 Unauthorized`

---

### **GET /projects/{project\_id}/info**

**Description:** Return project details if the user has access.

**Headers:**

```
Authorization: Bearer <jwt_token>
```

**Response:**

```json
{
  "id": "uuid",
  "name": "Project Alpha",
  "description": "Detailed description",
  "owner_id": "uuid",
  "created_at": "2025-08-11T10:00:00Z"
}
```

**Status Codes:**

* `200 OK`
* `401 Unauthorized`
* `403 Forbidden`
* `404 Not Found`

---

### **PUT /projects/{project\_id}/info**

**Description:** Update project name and description.
**Permissions:** Owner or users with edit rights.

**Headers:**

```
Authorization: Bearer <jwt_token>
```

**Request Body:**

```json
{
  "name": "Updated Project Name",
  "description": "Updated description"
}
```

**Response:**

```json
{
  "id": "uuid",
  "name": "Updated Project Name",
  "description": "Updated description",
  "owner_id": "uuid",
  "updated_at": "2025-08-11T12:10:00Z"
}
```

**Status Codes:**

* `200 OK`
* `401 Unauthorized`
* `403 Forbidden`
* `404 Not Found`

---

### **DELETE /projects/{project\_id}**

**Description:** Delete project and all associated documents.
**Permissions:** Only project owner.

**Headers:**

```
Authorization: Bearer <jwt_token>
```

**Response:**

```json
{ "message": "Project deleted successfully" }
```

**Status Codes:**

* `200 OK`
* `401 Unauthorized`
* `403 Forbidden`
* `404 Not Found`

---

### **GET /projects/{project\_id}/documents**

**Description:** Get all documents belonging to a project.

**Headers:**

```
Authorization: Bearer <jwt_token>
```

**Response:**

```json
[
  {
    "id": "uuid",
    "name": "design.pdf",
    "size": 24576,
    "uploaded_at": "2025-08-11T12:00:00Z"
  }
]
```

**Status Codes:**

* `200 OK`
* `401 Unauthorized`
* `403 Forbidden`
* `404 Not Found`

---

### **POST /projects/{project\_id}/documents**

**Description:** Upload one or multiple documents to a project.

**Headers:**

```
Authorization: Bearer <jwt_token>
Content-Type: multipart/form-data
```

**Request:**
`multipart/form-data` with `files[]`

**Response:**

```json
[
  {
    "id": "uuid",
    "name": "design.pdf",
    "size": 24576,
    "uploaded_at": "2025-08-11T12:00:00Z"
  }
]
```

**Status Codes:**

* `201 Created`
* `401 Unauthorized`
* `403 Forbidden`
* `404 Not Found`
* `415 Unsupported Media Type`

---

## **/document**

### **GET /document/{document\_id}**

**Description:** Download a document if the user has access to its project.

**Headers:**

```
Authorization: Bearer <jwt_token>
```

**Response:** Binary file stream.
Example Headers:

```
Content-Disposition: attachment; filename="design.pdf"
Content-Type: application/pdf
```

*(Content-Type depends on the file type.)*

**Status Codes:**

* `200 OK`
* `401 Unauthorized`
* `403 Forbidden`
* `404 Not Found`

---

### **PUT /document/{document\_id}**

**Description:** Update document content or metadata.

**Headers:**

```
Authorization: Bearer <jwt_token>
```

**Request:**
`multipart/form-data` or JSON

```json
{
  "name": "updated_design.pdf"
}
```

**Response:**

```json
{
  "id": "uuid",
  "name": "updated_design.pdf",
  "size": 30000,
  "updated_at": "2025-08-11T12:30:00Z"
}
```

**Status Codes:**

* `200 OK`
* `401 Unauthorized`
* `403 Forbidden`
* `404 Not Found`

---

### **DELETE /document/{document\_id}**

**Description:** Delete document from its project.

**Headers:**

```
Authorization: Bearer <jwt_token>
```

**Response:**

```json
{ "message": "Document deleted successfully" }
```

**Status Codes:**

* `200 OK`
* `401 Unauthorized`
* `403 Forbidden`
* `404 Not Found`

---

### **POST /projects/{project\_id}/invite?user={login}**

**Description:** Grant a user access to a project.
**Permissions:** Only project owner.

**Headers:**

```
Authorization: Bearer <jwt_token>
```

**Response:**

```json
{
  "message": "Access granted",
  "project_id": "uuid",
  "granted_to": "user_login"
}
```

**Status Codes:**

* `200 OK`
* `400 Bad Request` – User already has access
* `401 Unauthorized`
* `403 Forbidden` – Not project owner
* `404 Not Found` – Project or user not found