# PR #71 — current-main revalidation marker

This documentation-only commit requests a fresh pull-request CI merge test for the RAR real-byte extraction guard against:

- target branch: `main`;
- current target snapshot at request time: `f9adf687f2c46e5e98ae663823d89d0165356425`;
- security invariant: RAR extraction must be bounded by bytes actually read, not archive-declared metadata;
- scope invariant: no new provider, scheduler, Canon, ESM, network, or user-output authority.

The marker changes no runtime behavior. PR #71 remains draft until fresh full CI, Docker validation and independent review are complete.
