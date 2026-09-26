# LIMITATIONS AND TECHNICAL DISCLOSURES
**Project:** AI-Based Fake Identity & Document Screening System  
**Problem Statement:** SIH26188 | **Team:** Da Vinci Code (ID: 139735) | **Event:** Smart India Hackathon 2026

---

## 1. Prototype Boundaries & Honest Disclosures

In accordance with strict hackathon engineering ethics, this document distinguishes between fully functional components, simulated interfaces, and hardware-dependent boundaries.

| Pipeline Component | Implementation State | Technical Context & Production Roadmap |
| :--- | :--- | :--- |
| **Stage 1: Quality Gate** | **Fully Implemented** | OpenCV Laplacian variance calculates blur ($\text{Var} < 100$), and histogram intensity measures exposure. |
| **Stage 2: OCR & MRZ Parsing** | **Fully Implemented** | Official ICAO Doc 9303 Part 3 & 7 check digit algorithms ($7, 3, 1$ weights) for TD3 passports and date pivot logic. |
| **Stage 3: Central Registry & Blacklist** | **Mocked / Schema-Ready** | Relational SQLite database with pre-seeded stolen/expired/blacklisted documents. Architecture supports 1-line replacement with live Interpol / ICAO PKD REST APIs. |
| **Stage 4.1: Error Level Analysis (ELA)** | **Fully Implemented** | JPEG recompression diffs generated with high-frequency standard deviation scoring and visual heatmap exports. |
| **Stage 4.2: Copy-Move Detection** | **Fully Implemented** | OpenCV ORB keypoints + Hamming Distance matcher with spatial distance filtering. |
| **Stage 4.3: Font Consistency** | **Fully Implemented** | Contour geometry, stroke height, and glyph aspect ratio variance analysis. |
| **Stage 4.4: CNN Classifier** | **Interface / Heuristic Stub** | Standardized ResNet-18 interface returning patch tamper probability; ready for fine-tuned weights on MIDV-2020 dataset or ONNX Runtime deployment. |
| **Stage 5: Face Verification** | **Fully Implemented (Lightweight)** | Haar Cascade / oriented gradient feature embeddings with cosine similarity and human-in-the-loop borderline fallback. |
| **Stage 6: Explainable Risk Engine** | **Fully Implemented** | Transparent weighted scoring formula: MRZ (25%), DB (30%), Tampering (25%), Face (20%) with granular flag attribution. |
| **Stage 7: Digital Audit Trail** | **Fully Implemented** | Immutable screening logs and officer decisions persisted with timestamps. |

---

## 2. Physical & Operational Limitations

1. **Optical Security Features**:
   - High-end physical passports employ physical security laminates, UV-reactive ink, holograms, and infrared micro-print.
   - Detecting physical substrate tampering requires specialized multi-spectral optical hardware (3M / Regula scanners) beyond RGB camera captures.
2. **Risk Weight Tuning**:
   - Risk weights are reasoned domain heuristics. In production, weights should be dynamically calibrated using a labeled dataset of real-world checkpoint intercepts.
3. **Biometric Lighting Variations**:
   - To prevent false rejections of genuine travelers with older document photos, the similarity threshold is tolerant ($0.70$) and routes borderline cases ($0.55 - 0.70$) to human officer review.
