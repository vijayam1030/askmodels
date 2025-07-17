# Collapsible Model Responses Feature

## Overview
The Multi-Model Query Application now includes collapsible model responses, allowing you to manage screen space efficiently when querying multiple models.

## Features Added

### Individual Model Collapse/Expand
- **Click Header**: Click on any model's header (🤖 Model Name) to collapse or expand that specific model's response
- **Visual Indicator**: Each model has a collapse toggle (🔽/▶️) that shows the current state
- **Smooth Animation**: Responses collapse/expand with smooth CSS transitions

### Bulk Controls
- **Toggle All Button**: A "📁 Collapse All" / "📂 Expand All" button appears when models start responding
- **Smart Toggle**: Automatically detects current state and toggles appropriately
- **Consistent State**: All models collapse or expand together

## UI Enhancements

### Visual Design
- **Clickable Headers**: Model headers now have hover effects and cursor changes
- **Smooth Transitions**: CSS animations for collapse/expand actions
- **Space Management**: Collapsed models take minimal space, showing only the header

### User Experience
- **Persistent State**: Each model remembers its collapse state during the session
- **Real-time Updates**: Collapsible state works with both streaming and non-streaming responses
- **Intuitive Controls**: Clear visual indicators for interaction

## How to Use

### Web Interface
1. **Start a Query**: Enter your question and click "🚀 Query Models"
2. **Wait for Responses**: Models will start appearing as they respond
3. **Individual Control**: Click any model header to collapse/expand that model
4. **Bulk Control**: Use the "📁 Collapse All" / "📂 Expand All" button for all models

### Benefits
- **Screen Space**: Collapse completed models to focus on others still processing
- **Organization**: Keep only relevant responses visible
- **Performance**: Reduced visual clutter improves readability
- **Efficiency**: Quickly scan multiple model responses

## Technical Implementation

### CSS Classes
- `.response-content.collapsed`: Hides content with smooth transition
- `.response-content.expanded`: Shows content (default state)
- `.collapse-toggle`: Animated arrow indicator

### JavaScript Functions
- `toggleResponse(modelName)`: Toggles individual model collapse state
- `toggleAllResponses()`: Manages bulk collapse/expand functionality
- Enhanced `createOrUpdateResponseCard()`: Includes collapse functionality

### Features
- **Responsive Design**: Works on all screen sizes
- **Accessibility**: Keyboard navigation and screen reader friendly
- **Performance**: Minimal impact on response streaming
- **Compatibility**: Works with existing streaming and error handling

## Usage Examples

### Scenario 1: Multiple Model Comparison
1. Ask a coding question to multiple models
2. As responses come in, collapse completed ones
3. Focus on models still processing
4. Expand specific models for detailed comparison

### Scenario 2: Long Responses
1. Query models for detailed explanations
2. Collapse models with satisfactory answers
3. Keep problematic responses expanded for review
4. Use bulk controls to manage all at once

### Scenario 3: Resource Monitoring
1. View system resources while models run
2. Collapse model responses to see more system info
3. Monitor GPU/CPU usage with clean interface
4. Expand models only when needed

## Configuration
- **Default State**: All models start expanded
- **Auto-Show Controls**: Toggle button appears automatically when models respond
- **Persistent UI**: Controls remain visible throughout the session

This feature significantly improves the user experience when working with multiple AI models simultaneously, providing better organization and visual management of responses.
