# Stage 4 biopsy planning results

All distances are in mm. Sphere centre (0,0,0), radius 1; direction +x.
Expected values are derived independently in docs/STAGE4_DERIVATIONS.md.

| Case | Targeting error | Core length | Insertion depth | Status | Passed |
|---|---:|---:|---:|---|---|
| intersects | 0.6 | 1.6 | 5.8 | intersects | True |
| tangent | 1 | 0 | 5 | contact | True |
| miss | 2 | 0 | N/A | miss | True |
| behind | 0 | 0 | N/A | behind | True |
| inside | 0 | 1 | 1 | intersects | True |
| surface_inward | 0 | 2 | 2 | intersects | True |
| surface_outward | 0 | 0 | 0 | contact | True |

N/A means the forward trajectory cannot reach the sphere. It is stored as
JSON null / Python None, not as a zero insertion depth. Tangency has zero
harvestable core and a finite contact depth. Starting on the surface and
pointing outward also gives zero core, with contact already at depth zero.
The inside case counts only the forward part of the chord.

These geometric results idealize the needle as a line and the tumor as a
sphere. They do not model cutting geometry, actual core-device sampling
length, tissue deformation, or finite needle radius.
