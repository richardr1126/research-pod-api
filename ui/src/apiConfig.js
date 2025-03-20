const apiConfig = {
    development: {
      apiBaseUrl: 'http://localhost:8888'
    },
    production: {
      apiBaseUrl: 'https://api.richardr.dev'
    }
  };
  
  const environment = process.env.NODE_ENV || 'development';
  export default apiConfig[environment];