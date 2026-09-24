# Wave 7 Product Website Report

## Routes

- `GET /products`
- `GET /product/<slug>`

## Product Listing

The listing page supports:

- published product listing
- category filter using `category_name`
- product image display
- product summary
- detail links

## Product Detail

The detail page supports:

- slug-based lookup
- SEO title/description fallback
- product image
- SKU, status, and price display
- related products
- quote CTA

## Data Ownership

Product rendering uses Django-owned `BusinessProduct` records from previous ownership waves.

## 404 Handling

Missing product slugs return Django 404.
