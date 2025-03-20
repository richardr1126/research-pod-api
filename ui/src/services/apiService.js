

const API_BASE_URL = 'https://api.richardr.dev';

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
            throw new Error('Failed call to generate podcast');
        }
        return await response.json();
        } catch (error) {
        console.error('Error calling to generate podcast:', error);
        throw error;
        }
    },
    async checkStatus(jobId) {
        try {
            const response = await fetch(`${API_BASE_URL}/v1/api/pod/status/${jobId}`, {
                method: 'GET',
            });
            if (!response.ok) {
                throw new Error('Failed to generate podcast');
            }
            return await response.json();
        } catch (error) {
            console.error('Error generating podcast:', error);
            throw error;
        }
    }
};

export default apiService;