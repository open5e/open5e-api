## Pipelines and Infrastructure
This document describes the pipelines and infrastructure of the open5e api. It's intended to a good primer on the actual hosting and delivery mechanisms. It's not intended to be documentation of the api or its code structure.

## Infrastructure

### DNS / Certificates / Edge
There are two A records related to open5e api, one for each environment.
| Record | Environment | Authority | Certificate Issuer |
| ---- | ---- | ---- | ---- | 
| api.open5e.com | Production API | Cloudflare | Clouflare | 
| api-beta.open5e.com | Beta API | DigitalOcean and Cloudflare? | Cloudflare | 

Cloudflare provides certificates for requests that terminate on its edge. These records all resolve on cloudflare's edge proxies and are forwarded onto the backend servers. The certificates auto-renew.

Cloudflare also caches requests. More information about caching should go here.

### Compute / Storage
Digital Ocean is used for production and beta environments. We are using DigitalOcean App Engine to serve a docker container in both environments.

### Code / Build
The root repository is https://github.com/open5e/open5e-api.

### Monitoring / Analytics
New Relic is being used, as well as cloudflare's built in analytics.

## Pipelines
We have four major flows.
| Pipeline | Trigger | Result | 
| --- | --- | --- |
| PR Validation | pull_request, push (except to staging, main) | Python tests are run, and docker image is built. |
| Build and Deploy (Staging) | push (staging)| Docker image is built and pushed to DO staging app, as well as docker hub.|
| Build and Deploy (Production) | push (main) | Docker image is built and pushed to DO production app, as well as docker hub.|
| Deploy Readme OpenAPI | push (main) | openAPI schema is pushed to readme.io.|


We have controls around the ***staging*** branch (no one is allowed to merge directly). We have similar controls around the ***main*** branch, but we also require that merges come from staging.
