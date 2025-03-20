const apiConfig = {
    development: {
      apiBaseUrl: 'http://localhost:8888',
      eventsBaseUrl: 'http://localhost:8081',
    },
    production: {
      apiBaseUrl: 'https://api.richardr.dev',
      eventsBaseUrl: 'https://research-consumer-0.richardr.dev',
    }
  };
  
  const environment = process.env.NODE_ENV || 'development';
  export default apiConfig[environment];