# Exact Docker image for M2 runs

Tag: `black-ref:0aa7ce6`
Image ID (`docker image inspect --format '{{.Id}}'`): `sha256:97ad1d4c33ba11fc921bb6f0e5b6b1144459cbd07c31adf41ff5f1d6563274ef`
Layer fingerprint (sha256 of `{{json .RootFS.Layers}}`): `5a6f9e3a00446ab914c6b8c331406f387bdd668f8d3454dd394b68dad02998db`
Base image: `python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b`
Archive: `black-ref-0aa7ce6.tar.gz` (66,651,939 bytes; made with `docker save`, then `gzip -9`)
Archive SHA-256: `c4616f494c46054a75b7e1b24fb58c17691b05107e0159db048e409a8714eab4` (file `black-ref-0aa7ce6.tar.gz.sha256`)
Download: `<link, to be filled>`

Do not rebuild. An independent rebuild gives a different image ID; `docker/build.sh` then exits with 77 and keeps the recorded ID.

## Verify and load
```bash
sha256sum -c black-ref-0aa7ce6.tar.gz.sha256       # PowerShell: Get-FileHash -Algorithm SHA256 black-ref-0aa7ce6.tar.gz
docker load -i black-ref-0aa7ce6.tar.gz
docker image inspect black-ref:0aa7ce6 --format '{{.Id}}'                              # must equal docker/IMAGE_DIGEST.txt
docker image inspect black-ref:0aa7ce6 --format '{{json .RootFS.Layers}}' | sha256sum   # must equal the layer fingerprint
```
If the ID differs but the layer fingerprint matches, the content is identical but your Docker image store reports another ID. The run scripts then stop with exit 72. Report it to Member 2; do not edit `docker/IMAGE_DIGEST.txt`.