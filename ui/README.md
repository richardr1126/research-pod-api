### AI Research Podcast Generator and Browser

This is the UI for a project which allows users to Generate Research podcasts using the latest AI models, and browse/search stored podcasts.

## What Can Users do with this UI?

1. Generate new AI podcasts
2. Browse existing podcasts
3. Look at recommended podcasts
4. Listen to all podcasts, newly generated or pre-existing
5. Generate modified versions of existing podcasts.
6. Retrieve previously viewed podcasts, along with their current watch-state.

## Pages

# Home
This page has a button to generate new podcasts with a text prompt, along with a search-bar for searching existing podcasts. 
TODO: The Generate Podcast button will hook up to the reasearch-pod-api backend and send out an API request.
# Watch
TODO: The user will navigate to this page when they click on a podcast to play it. It will display the podcast similarly to something like spotify, with a time-scroll bar to move through the podcast, FF and rewind buttons, and a pause/play button. It will also display real-time captions of the podcast.
# Browse
This page displays the previously generated podcast. There will be a list of podcasts with play buttons.
TODO: Clicking on the pre-generated podcast takes the user to the Watch page. There are buttons to organizethe podcasts in various ways. There are filter options for date created, user who created them, and of course a working search-bar to filter on keywords. Each podcast will have a set of pre-generated tags which attach to the keyword search.
# Navigation Sidebar
There will be a sidebar in each page which leads the user back to the Generate and Browse pages.
# Recommender Sidebar
TODO: There will be a sidebar showing recommended podcasts based on the podcast the user is currently watching as well as their prior search history.

# Getting Started with Create React App

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

To get started with the project and run these scripts, download the latest version of node.js, which will come with Node Package Manager. I just realized that my __modules__ folder is outside of this Repo, so I'm not sure that these scripts will just run in any clone of this repo.

## Available Scripts

In the project directory, you can run:

### `npm test`

~~Launches the test runner in the interactive watch mode.~~
I altered this to run tests with Jest, and Babel for .js translation. If you can run this command without errors, then it means you've got everything installed and working properly.
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.
[Jest documentation](https://jestjs.io/)

### `npm run deploy`

Compiles the application into static .html files in the gh-pages branch, the pushes gh-pages to GitHub, for GitHub Pages deployment. This is how I'm hosting the page for now.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can't go back!**

If you aren't satisfied with the build tool and configuration choices, you can `eject` at any time. This command will remove the single build dependency from your project.

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc) right into your project so you have full control over them. All of the commands except `eject` will still work, but they will point to the copied scripts so you can tweak them. At this point you're on your own.

You don't have to ever use `eject`. The curated feature set is suitable for small and middle deployments, and you shouldn't feel obligated to use this feature. However we understand that this tool wouldn't be useful if you couldn't customize it when you are ready for it.

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).

### Code Splitting

This section has moved here: [https://facebook.github.io/create-react-app/docs/code-splitting](https://facebook.github.io/create-react-app/docs/code-splitting)

### Analyzing the Bundle Size

This section has moved here: [https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size](https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size)

### Making a Progressive Web App

This section has moved here: [https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app](https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app)

### Advanced Configuration

This section has moved here: [https://facebook.github.io/create-react-app/docs/advanced-configuration](https://facebook.github.io/create-react-app/docs/advanced-configuration)

### Deployment

This section has moved here: [https://facebook.github.io/create-react-app/docs/deployment](https://facebook.github.io/create-react-app/docs/deployment)

### `npm run build` fails to minify

This section has moved here: [https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify](https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify)
