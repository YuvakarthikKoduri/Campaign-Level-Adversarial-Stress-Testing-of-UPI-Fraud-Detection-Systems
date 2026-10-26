# Security and responsible use

The dashboard is a single-user local research application, not a hardened multi-user service. It defaults to loopback and checks Host/Origin plus a session token for writes. Commands are fixed Python templates with validated enums/integers, approved catalog references, bounded output names, a single active job and timeouts.

No unrestricted shell string, arbitrary executable, command chaining, Git push/merge/release, public publication or Gate C action is exposed. Cancellation sends signals to the process group and escalates if needed. Logs distinguish stdout/stderr and redact common secret patterns, but redaction is not a general data-loss-prevention guarantee.

Do not reverse-proxy this service, bind it to a public interface, upload credentials, use real payment accounts, or run adversarial tests against third-party systems. Do not trust unreviewed pickle artifacts. Approved evidence paths must not be replaced with attacker-controlled symlinks.

The integration checks fixed-command behavior and local boundary cases, not formal security certification, all browsers or complete accessibility conformance. Scientific validity is a separate question from software safety.

The paper is substantially AI-assisted and requires student/supervisor ownership and policy approval. Citation-grounded original wording does not establish an AI-check percentage. Follow [external report instructions](../research/review_materials/EXTERNAL_CHECKS.md), and keep personal checker reports private unless approved for publication.
