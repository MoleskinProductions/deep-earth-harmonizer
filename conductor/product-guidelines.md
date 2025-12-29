# Product Guidelines

These guidelines define the design, documentation, and operational principles for the Deep Earth Harmonizer project.

## Design Principles

### Technical Rigor
- **Accuracy First:** Coordinate system integrity (UTM) and mathematical accuracy in data reprojection are non-negotiable.
- **Data Provenance:** Always track and expose the source and quality of data (`f@data_quality`, `s@source_year`).
- **Validated Inputs:** Parameters such as bounding boxes and credentials must be validated strictly to prevent downstream processing errors.

### Creative Flow & Intuition
- **Artist Centric:** While technically rigorous, the tool must provide fast viewport feedback and prioritize artist intuition.
- **Experimentation:** Support non-destructive experimentation through Houdini's procedural nature and efficient caching.
- **Performance:** Network and processing bottlenecks must be managed via async operations and tile-based subdivision to maintain a responsive UI.

### Native Houdini Integration
- **Convention Adherence:** Follow standard Houdini UX patterns, particularly those established by the Heightfield and PDG/TOP networks.
- **VEX Utilities:** Provide clean, well-documented VEX snippets that allow artists to query complex embeddings without deep technical knowledge of the underlying vector math.

## Documentation & Communication

### User-Centric & Educational
- **Approachable Prose:** Documentation should explain *why* geospatial concepts (like coordinate reprojection) are necessary, not just *how* to toggle a button.
- **Visual Diagnostics:** Use viewport visualizations and status attributes to communicate system state and errors, reducing reliance on the technical console.

### Code Style
- **Python:** Use modern `asyncio` patterns for I/O bound tasks. Maintain clear separation between the core logic and the Houdini HDA wrapper.
- **VEX:** Write performant, readable VEX with clear attribute naming conventions as defined in the Hyper-Point Schema.

## Error Handling & Resilience

### Fail-Graceful Design
- **Non-Blocking Logic:** The failure of one data stream (e.g., a missing OSM tile) must not prevent the successful synthesis of other available streams (e.g., SRTM elevation).
- **Clear Flagging:** Missing or partial data must be explicitly flagged via attributes so procedural systems can adapt gracefully.
- **Diagnostic Feedback:** Credential failures or API rate limits should be communicated through the HDA's status bar and visual indicators.
