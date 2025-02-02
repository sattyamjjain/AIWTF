import axios from 'axios';

const API_URL = 'http://localhost:8000/api/v1/research';

export const fetchResearchResults = async (topic) => {
  try {
    const response = await axios.post(API_URL, { topic });
    return response.data;
  } catch (error) {
    throw error;
  }
}; 