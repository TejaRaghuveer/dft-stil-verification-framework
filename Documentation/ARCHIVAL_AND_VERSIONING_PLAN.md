# Archival and Versioning Plan

## Archive Policy

- Every tapeout handoff is archived with timestamp and release note.
- Archive naming convention: `GPU_Shader_DFT_<revision>_<YYYYMMDD>`.

## Required Archive Content

- STIL patterns and converted ATE pattern sets
- ATE programs and validation reports
- Coverage and sign-off reports
- Documentation and runbooks
- Configuration snapshots used for sign-off

## Backup and Retention

- Primary storage: secure internal artifact server
- Secondary storage: geographically separate backup repository
- Retention period: minimum 10 years

## Access Control and Security

- Role-based access with least privilege
- Read access for manufacturing/test operations
- Write access limited to release owners
- Integrity verification via checksums per archive

