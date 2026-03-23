/**
 * Test block for syntax highlighting
 * Features: multi-line comments, JSDoc
 */
import { Component } from './base-module'; // Import statement

const API_URL = "https://api.example.com"; // String
const MAX_RETRIES = 5; // Number

export default class HighlighterTest extends Component {
  constructor(options = {}) {
    super(options);
    this.pattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/gmu; // Regular Expression 
  }

  async fetchData(id) {
    // Single line comment
    try {
      const response = await fetch(`${API_URL}/items/${id}`); // Template literal
      if (!response.ok) throw new Error(`HTTP error: ${response.status}`);

      const data = await response.json();
      return data.filter(item => item.active ?? true); // Nullish coalescing & arrow function
    } catch (err) {
      console.error("Failed to fetch:", err);
      return null;
    }
  }

  /* Complex logic test */
  render() {
    const list = [1, 2, 3].map(n => n * 2);
    const isActive = true;

    return `
      <div class="${isActive ? 'active' : ''}">
        Count: ${list.length}
      </div>
    `;
  }
}
