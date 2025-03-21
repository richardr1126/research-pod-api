import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from '../App';

// Mock the setTimeout function
jest.useFakeTimers();

describe('Podcast App', () => {
  test('renders sidebar with navigation buttons', () => {
    render(<App />);
    
    // Check that the sidebar and logo are rendered
    expect(screen.getByText('AI Podcast')).toBeInTheDocument();
    
    // Check that both navigation buttons are rendered
    expect(screen.getByText('Browse Podcasts')).toBeInTheDocument();
    expect(screen.getByText('Generate New Podcast')).toBeInTheDocument();
  });

  test('initially shows the generate podcast page', () => {
    render(<App />);
    
    // Check that the generate podcast page is shown initially
    expect(screen.getByText('Generate a New Podcast')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/E.g., The history of jazz music/)).toBeInTheDocument();
    
    // The browse page should not be visible
    expect(screen.queryByText('Browse Podcasts', { selector: 'h2' })).not.toBeInTheDocument();
  });

  test('navigates to browse page when Browse button is clicked', async () => {
    render(<App />);
    
    // Click on the Browse Podcasts button
    fireEvent.click(screen.getByText('Browse Podcasts'));
    
    // Check that the browse page is now shown
    expect(screen.getByText('Browse Podcasts', { selector: 'h2' })).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Search podcasts...')).toBeInTheDocument();
    
    // The generate page should not be visible
    expect(screen.queryByText('Generate a New Podcast')).not.toBeInTheDocument();
  });

  test('navigates back to generate page when Generate button is clicked', async () => {
    render(<App />);
    
    // First navigate to browse page
    fireEvent.click(screen.getByText('Browse Podcasts'));
    
    // Then click on the Generate New Podcast button
    fireEvent.click(screen.getByText('Generate New Podcast'));
    
    // Check that the generate page is now shown
    expect(screen.getByText('Generate a New Podcast')).toBeInTheDocument();
    
    // The browse page should not be visible
    expect(screen.queryByText('Browse Podcasts', { selector: 'h2' })).not.toBeInTheDocument();
  });

  test('generate button is disabled when query is empty', () => {
    render(<App />);
    
    // Check that the generate button is initially disabled
    const generateButton = screen.getByText('Generate Podcast');
    expect(generateButton).toBeDisabled();
    
    // Type something in the textarea
    const textarea = screen.getByPlaceholderText(/E.g., The history of jazz music/);
    fireEvent.change(textarea, { target: { value: 'Test query' } });
    
    // Check that the button is now enabled
    expect(generateButton).not.toBeDisabled();
    
    // Clear the textarea
    fireEvent.change(textarea, { target: { value: '' } });
    
    // Check that the button is disabled again
    expect(generateButton).toBeDisabled();
  });

  test.skip('submitting the generate form shows loading state and success message', async () => {
    // Mock window.alert
    const alertMock = jest.spyOn(window, 'alert').mockImplementation();
    
    render(<App />);
    
    // Type a query
    const textarea = screen.getByPlaceholderText(/E.g., The history of jazz music/);
    fireEvent.change(textarea, { target: { value: 'History of AI' } });
    
    // Submit the form
    const generateButton = screen.getByText('Generate Podcast');
    fireEvent.click(generateButton);
    
    // Button should show loading state
    expect(screen.getByText('Generating...')).toBeInTheDocument();
    
    // Fast-forward timers
    jest.runAllTimers();
    
    // Check for success alert
    await waitFor(() => {
      expect(alertMock).toHaveBeenCalledWith('Podcast generation started! You will be notified when it is ready.');
    });
    
    // Button should return to normal state
    expect(screen.getByText('Generate Podcast')).toBeInTheDocument();
    
    // Input should be cleared
    expect(textarea.value).toBe('');
    
    // Cleanup
    alertMock.mockRestore();
  });

  test('browse page shows the podcast list with correct number of podcasts', () => {
    render(<App />);
    
    // Navigate to browse page
    fireEvent.click(screen.getByText('Browse Podcasts'));
    
    // Check for the podcast cards
    const podcasts = screen.getAllByText(/Duration:/);
    expect(podcasts).toHaveLength(3); // This should match the number of mock podcasts
    
    // Check that podcast titles are displayed
    expect(screen.getByText('The Future of AI')).toBeInTheDocument();
    expect(screen.getByText('Space Exploration in 2025')).toBeInTheDocument();
    expect(screen.getByText('Climate Change Solutions')).toBeInTheDocument();
  });

  test('each podcast card has play and download buttons', () => {
    render(<App />);
    
    // Navigate to browse page
    fireEvent.click(screen.getByText('Browse Podcasts'));
    
    // Check for play buttons
    const playButtons = screen.getAllByText('Play');
    expect(playButtons).toHaveLength(3);
    
    // Check for download buttons
    const downloadButtons = screen.getAllByText('Download');
    expect(downloadButtons).toHaveLength(3);
  });

  test('podcast search input exists and is functional', () => {
    render(<App />);
    
    // Navigate to browse page
    fireEvent.click(screen.getByText('Browse Podcasts'));
    
    // Check that search input exists
    const searchInput = screen.getByPlaceholderText('Search podcasts...');
    expect(searchInput).toBeInTheDocument();
    
    // Check that we can type in the search input
    fireEvent.change(searchInput, { target: { value: 'AI' } });
    expect(searchInput.value).toBe('AI');
  });
});