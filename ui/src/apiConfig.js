const apiConfig = {
    // This is the default URL when running "npm start". To use this URL, you must run the API server locally with docker.
    // See the README.md in the root directory for instructions on setting up the local API service with docker.
    development: {
      apiBaseUrl: 'http://localhost:8888'
    },
    // We're using Richard's website when running "npm run build" and deploying to production.
    production: {
      apiBaseUrl: 'https://api.richardr.dev'
    }
  };
  
  const environment = process.env.NODE_ENV || 'development';
  export default apiConfig[environment];