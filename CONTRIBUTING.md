# Contributing Guidelines
**Project:** AI-Based Fake Identity & Document Screening System (SIH26188)  
**Team:** Da Vinci Code (Team ID: 139735)

Thank you for contributing to the **BorderShield AI** identity and document screening initiative.

---

## 1. Code of Conduct
We adhere to collaborative, professional, and ethical AI development standards. Ensure all synthetic test data remains explicitly labeled as synthetic.

---

## 2. Development Workflow

1. **Fork or Branch**:
   Create your feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Modular Architecture Compliance**:
   - Keep stages isolated behind clean service interfaces.
   - Do not merge distinct forensic checks into monolithic scripts.
   - Ensure all forensic modules handle input exceptions gracefully without crashing the whole pipeline.

3. **Running Local Tests**:
   Before submitting changes, execute the test suite:
   ```bash
   pytest tests/
   ```

4. **Submitting Pull Requests**:
   - Ensure `npm run build` succeeds cleanly in `frontend/`.
   - Update `LIMITATIONS.md` if altering model capabilities or hardware requirements.
   - Document any new environment variables in `.env.example`.
