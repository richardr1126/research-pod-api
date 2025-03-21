# AI Research Podcast Generator and Browser

This is the UI for a project which allows users to generate, browse, and listen to AI podcasts.

## What Can Users do with this UI?

1. Generate new AI podcasts
2. Browse existing podcasts
3. Look at recommended podcasts
4. Listen to all podcasts, newly generated or pre-existing
5. Generate modified versions of existing podcasts.
6. Retrieve previously viewed podcasts, along with their current watch-state.

## Pages

### Browse
* View Previously Generated Podcasts
* Filter through Podcasts with a Search function
* Generate New Podcasts from text input
TODO: The Generate Podcast button will hook up to the reasearch-pod-api backend and send out an API request.
### Create
* Generate Podcasts with a text input
* Add meta-requests for podcast length, tonality, persona, etc.
### Play (TODO)
* Podcast player with time-scroll bar
* Play/Pause, fast-forward, rewind
* Real-time captions
### Navigation Sidebar
* Quickly access Browse and Create pages from main page.
### Recommender Sidebar (TODO)
* Show Recommended podcasts based on user history and data
* Current podcast for Play page
* Not sure how to implement for Browse (home) page. Would need to track user history somehow.

### Getting Started

This project requires Node.js and npm. Download the latest version of Node.js to build the project.

# Setup
1. Clone the repository
2. Download and install the latest version of Node.js
3. Run `npm install` from the project repo to add dependencies

# Dev Commands
* `npm test` Run jest tests
* `npm run build` Build app for production
* `npm start` Build and run app locally. Must have a local instance of the API endpoint running for this to work (see section below).
* `npm run deploy` Build production version and deploy to GitHub pages.

# Setting up the API to run a local build.
The project is configured to use a local API endpoint for dev builds (`npm start`), and a remote API endpoint for production builds (`npm run build` and `npm run deploy`). This ensures that the API endpoint is in sync with the UI (as the remote endpoint is built from a different branch of the repo) and allows the developer to monitor the API from both ends when testing a dev build.
The Dev build will still run without a local API endpoint, but all API functionality will be lost.
#### *To set-up and run the API locally with Docker, follow the instructions the README in the root directory.*

# TODO

* Implement Play page with functionality listed
* Generate Button should either take the user to a loading screen or prevent the user from clicking away while the podcast is generating.
* Add a Sources button to each podcast in Browse, should generate a pop-up or a box in the UI listing the sources.
* Browse should be separated into rows and include recommended, as well as various topics

