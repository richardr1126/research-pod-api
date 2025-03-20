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
* `npm run build` build app for production
* `npm start` build and run app locally (good for manual testing)
* `npm run deploy` (NOT IMPLEMENTED IN THIS REPO) build production version and deploy to GitHub pages.