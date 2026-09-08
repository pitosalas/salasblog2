# TF37 — EasyMDE Markdown Editor in Admin Post Editor
**Date Created:** 2026-04-15

## TF37.0 — Add POST /api/upload-image endpoint in server.py
**Status**: done

**Description**: Add a new endpoint `POST /api/upload-image` that accepts a multipart file upload (`file: UploadFile`). Reuse the same three-location save logic as `metaweblog_newMediaObject`: source (`static/images/uploads/`), output (`output/static/images/uploads/`), volume (`/data/static/images/uploads/`). Date-prefix the filename. Return `{"url": "/static/images/uploads/<filename>"}`. Require admin authentication.
**Tests**: Add tests in `tests/test_upload_image.py`: (1) authenticated upload saves file and returns correct URL, (2) unauthenticated request returns 401, (3) filename is date-prefixed.

## TF37.1 — Integrate EasyMDE into edit_post.html and new_post.html
**Status**: done

**Description**: Load EasyMDE via CDN in both templates. Replace the `<textarea>` with an EasyMDE instance configured with: toolbar `["bold", "italic", "heading", "|", "image", "link", "code", "|", "unordered-list", "ordered-list"]`, preview/fullscreen/guide hidden, `status: false`, `spellChecker: false`, `uploadImage: true`, `imageUploadFunction` wired to `POST /api/upload-image`. Sync EasyMDE value back to textarea before FormData submission.
**Tests**: `tests/test_upload_image.py` covers the upload endpoint. Full suite passes with no regressions.
