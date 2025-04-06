import apiConfig from "../apiConfig";

const API_BASE_URL = apiConfig.apiBaseUrl;

const apiService = {
    async createPodcast(query) {
        try {
            const response = await fetch(`${API_BASE_URL}/v1/api/pod/create`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query }),
            });
            
            if (!response.ok) {
                throw new Error(`Failed to generate podcast: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error calling to generate podcast:', error);
            throw error;
        }
    },
    
    async checkStatus(podId) {
        try {
            const response = await fetch(`${API_BASE_URL}/v1/api/pod/status/${podId}`);
            
            if (!response.ok) {
                throw new Error(`Failed to check podcast status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error checking podcast status:', error);
            throw error;
        }
    },
    
    async getPodcast(podId) {
        try {
            const response = await fetch(`${API_BASE_URL}/v1/api/pod/get/${podId}`);
            
            if (!response.ok) {
                throw new Error(`Failed to get podcast details: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error fetching podcast details:', error);
            throw error;
        }
    }
};

export default apiService;