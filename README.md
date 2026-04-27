# Email Extractor API

## Features
- Crawl domains
- Extract public emails
- Filter invalid emails
- Remove Gmail/Yahoo/etc
- Export CSV

## Endpoints

### POST /extract
Returns JSON emails

### POST /extract-csv
Downloads CSV file

## Example Request
{
  "domains": ["example.com"]
}