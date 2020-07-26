# The RetryLife API

This is the source for the [Vercel](https://vercel.com) Lambda functions that power the RetryLife API

## What is this?

The RetryLife API is my personal API. It is used by many of my web-based projects to fetch data from various sources around the internet. All requests are handled by vercel.com's edge servers. Depending on the request type, responses are either served from edge caches, or through a lambda function. The API itself is used to expose data from services that don't provide their own APIs by carefully scraping web data, and faking user connections to services.

The public-facing API documentation can be found [here](https://api.retrylife.ca/apidocs). Some API functionality and endpoints are hidden, and not hosted in this repo.

## Can I use it in my own projects? 

Yes, as long as the endpoint you are planning to use is listed in the public API documentation, it is free to use. If you figure out how to use some of the hidden functionality, just send me an email to make sure the endpoint is stable and ready for use.

## API status

You can view the API status page [here](https://status.retrylife.ca)