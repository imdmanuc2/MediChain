
# MediChain

**MediChain** is a blockchain-based medical record and payment system designed to give patients full control over their data while enabling secure and transparent sharing among healthcare providers.

---

## Features

- Secure Blockchain for Medical Visits and Payments
- Patient Record Management
- File Uploads (PDFs, images, TXT)
- OCR Integration for Automated Text Extraction
- Historical Record Viewer with Filter/Search
- Export Data in JSON or CSV
- Admin Dashboard with Medications, Allergies, Payments
- Simple Registration/Login System

---

## Vision and Scalability

MediChain is designed with the following scalable goals in mind:

1. **Decentralized Infrastructure**
   - Enable multiple nodes to participate in validating transactions.
   - Transition from in-memory blockchain to persistent DB-backed chain (e.g., MongoDB, Postgres).

2. **Role-Based Access Control (RBAC)**
   - Define roles: patient, doctor, admin, pharmacist.
   - Restrict who can view/edit what portions of the data.

3. **File Storage & Encryption**
   - Migrate file uploads to IPFS or encrypted S3-compatible storage.
   - Add per-record or per-user AES encryption using private keys.

4. **Authentication**
   - Use JWT or OAuth2 for scalable and secure login sessions.
   - Optional 2FA for high-trust environments.

5. **Interoperability**
   - Implement FHIR or HL7 compatibility to integrate with existing EMRs.
   - Support APIs for 3rd party patient-facing apps.

6. **Data Auditing and Provenance**
   - Track edits and versioning for all records.
   - Log all access to patient records.

---

## Setup Instructions

1. Clone this repo:

```bash
git clone https://github.com/yourusername/medichain.git
cd medichain
```

2. Create a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Run the app:

```bash
python api.py
```

4. Navigate to [http://localhost:5000](http://localhost:5000) in your browser.

---

## License

MIT License © 2025 MediChain Authors
