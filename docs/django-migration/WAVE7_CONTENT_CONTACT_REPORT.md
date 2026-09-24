# Wave 7 News And Contact Report

## News Routes

- `GET /news`
- `GET /news/<slug>`

News content is read through `CmsService`.

## Contact Route

`GET/POST /contact`

## Forms

Implemented:

- Contact form.
- Quote request form.

## Validation

The forms require:

- name
- email or phone
- valid captcha answer
- product/message content for quote requests

## Submission Handling

Valid submissions are stored as safe Django submission intents using:

`replacement_submission_service.create_submission()`

Wave 7 does not send external email or call external systems.

## Security

- CSRF enabled.
- Django forms validate browser input.
- No file upload is accepted in Wave 7.
