import React, { useState, useEffect, useRef } from 'react';
import io from 'socket.io-client';
import './App.css';

const API_BASE_URL = 'http://localhost:5000';

const ModelCategories = {
  '💻 Coding': '💻 Coding & Development',
  '✍️ Creative': '✍️ Creative & Writing',
  '🔬 Research': '🔬 Research & Analysis',
  '💬 Conversational': '💬 Conversational AI',
  '⚡ Efficient': '⚡ Efficient & Lightweight',
  '🤖 General': '🤖 General Purpose'
};

const App = () => {
  const [models, setModels] = useState([]);
  const [selectedModels, setSelectedModels] = useState([]);
  const [currentMode, setCurrentMode] = useState('qa');
  const [question, setQuestion] = useState('');
  const [questionType, setQuestionType] = useState('general');
  const [debateTopic, setDebateTopic] = useState('');
  const [debateRounds, setDebateRounds] = useState(3);
  const [responses, setResponses] = useState({});
  const [debateState, setDebateState] = useState({});
  const [isQuerying, setIsQuerying] = useState(false);
  const [isDebating, setIsDebating] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sessionId] = useState(() => Math.random().toString(36).substring(2, 15));
  
  const socketRef = useRef(null);

  useEffect(() => {
    // Initialize socket connection
    socketRef.current = io(API_BASE_URL);
    
    // Socket event listeners
    socketRef.current.on('response_update', (data) => {
      setResponses(prev => ({
        ...prev,
        [data.model]: data
      }));
    });

    socketRef.current.on('debate_update', (data) => {
      setDebateState(prev => ({
        ...prev,
        ...data
      }));
    });

    socketRef.current.on('query_complete', () => {
      setIsQuerying(false);
    });

    socketRef.current.on('debate_complete', () => {
      setIsDebating(false);
    });

    socketRef.current.on('error', (data) => {
      setError(data.message);
      setIsQuerying(false);
      setIsDebating(false);
    });

    // Load models on component mount
    loadModels();

    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, []);

  const loadModels = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/models`);
      const data = await response.json();
      if (data.success) {
        setModels(data.models_with_info || []);
      }
    } catch (err) {
      setError('Failed to load models');
    } finally {
      setLoading(false);
    }
  };

  const handleModelSelect = (modelName) => {
    setSelectedModels(prev => 
      prev.includes(modelName) 
        ? prev.filter(m => m !== modelName)
        : [...prev, modelName]
    );
  };

  const handleSelectAll = () => {
    setSelectedModels(models.map(m => m.name));
  };

  const handleClearAll = () => {
    setSelectedModels([]);
  };

  const handleSelectDiverse = () => {
    const selectedCategories = new Set();
    const diverseModels = [];
    
    models.forEach(model => {
      const category = model.category || 'General';
      if (selectedCategories.size < 3 && !selectedCategories.has(category)) {
        diverseModels.push(model.name);
        selectedCategories.add(category);
      }
    });
    
    setSelectedModels(diverseModels);
  };

  const handleSubmitQuery = async () => {
    if (!question.trim() || selectedModels.length === 0) return;
    
    setIsQuerying(true);
    setResponses({});
    setError('');
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question,
          type: questionType,
          streaming: true,
          selected_models: selectedModels,
          session_id: sessionId
        }),
      });
      
      const data = await response.json();
      if (!data.success) {
        setError(data.error || 'Query failed');
        setIsQuerying(false);
      }
    } catch (err) {
      setError('Failed to submit query');
      setIsQuerying(false);
    }
  };

  const handleStartDebate = async () => {
    if (!debateTopic.trim() || selectedModels.length === 0) return;
    
    if (selectedModels.length > 6) {
      setError('Please select no more than 6 models for optimal debate quality');
      return;
    }
    
    setIsDebating(true);
    setDebateState({});
    setError('');
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/debate/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          topic: debateTopic,
          selected_models: selectedModels,
          debate_rounds: debateRounds,
          session_id: sessionId
        }),
      });
      
      const data = await response.json();
      if (!data.success) {
        setError(data.error || 'Debate failed to start');
        setIsDebating(false);
      }
    } catch (err) {
      setError('Failed to start debate');
      setIsDebating(false);
    }
  };

  const handleCancelQuery = () => {
    if (socketRef.current) {
      socketRef.current.emit('cancel_query', { session_id: sessionId });
    }
    setIsQuerying(false);
    setResponses({});
  };

  const handleCancelDebate = () => {
    if (socketRef.current) {
      socketRef.current.emit('cancel_debate', { session_id: sessionId });
    }
    setIsDebating(false);
    setDebateState({});
  };

  const renderModelSelection = () => {
    const categorizedModels = models.reduce((acc, model) => {
      const category = model.category || 'General';
      if (!acc[category]) acc[category] = [];
      acc[category].push(model);
      return acc;
    }, {});

    return (
      <div className="model-selection">
        <h3>🤖 Model Selection</h3>
        
        <div className="model-actions">
          <button onClick={handleSelectAll} className="btn btn-outline">
            Select All
          </button>
          <button onClick={handleClearAll} className="btn btn-outline">
            Clear All
          </button>
          <button onClick={handleSelectDiverse} className="btn btn-outline">
            Select Diverse
          </button>
          <button onClick={loadModels} className="btn btn-outline">
            🔄 Refresh
          </button>
        </div>

        <div className="model-categories">
          {Object.entries(categorizedModels).map(([category, categoryModels]) => (
            <div key={category} className="model-category">
              <h4>{category} ({categoryModels.length} models)</h4>
              <div className="models-grid">
                {categoryModels.map(model => (
                  <div
                    key={model.name}
                    className={`model-card ${selectedModels.includes(model.name) ? 'selected' : ''}`}
                    onClick={() => handleModelSelect(model.name)}
                  >
                    <div className="model-name">{model.name}</div>
                    <div className="model-specialty">{model.specialty || 'General Purpose'}</div>
                    <div className="model-description">{model.description}</div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="selection-summary">
          Selected: {selectedModels.length} model{selectedModels.length !== 1 ? 's' : ''}
        </div>
      </div>
    );
  };

  const renderQAInterface = () => (
    <div className="qa-interface">
      <h2>❓ Q&A Mode</h2>
      
      <div className="question-input">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask anything... What would you like to know?"
          rows={4}
          className="question-textarea"
        />
      </div>

      <div className="question-type">
        <label>
          <input
            type="radio"
            value="general"
            checked={questionType === 'general'}
            onChange={(e) => setQuestionType(e.target.value)}
          />
          💭 General
        </label>
        <label>
          <input
            type="radio"
            value="coding"
            checked={questionType === 'coding'}
            onChange={(e) => setQuestionType(e.target.value)}
          />
          💻 Coding
        </label>
      </div>

      {renderModelSelection()}

      <div className="submit-controls">
        <button
          onClick={handleSubmitQuery}
          disabled={isQuerying || !question.trim() || selectedModels.length === 0}
          className="btn btn-primary"
        >
          {isQuerying ? '⏳ Processing...' : '🚀 Query Models'}
        </button>
        {isQuerying && (
          <button onClick={handleCancelQuery} className="btn btn-danger">
            ⏹️ Cancel
          </button>
        )}
      </div>

      {Object.keys(responses).length > 0 && (
        <div className="responses">
          <h3>📝 Responses</h3>
          {Object.entries(responses).map(([modelName, response]) => (
            <div key={modelName} className="response-card">
              <h4>🤖 {modelName}</h4>
              {response.status === 'completed' && (
                <div>
                  <div className="response-meta">
                    ✅ Completed in {response.time?.toFixed(2) || 0}s
                  </div>
                  <div className="response-content">
                    {response.content}
                  </div>
                </div>
              )}
              {response.status === 'error' && (
                <div className="response-error">
                  ❌ Error: {response.error || 'Unknown error'}
                </div>
              )}
              {response.status === 'processing' && (
                <div className="response-processing">
                  ⏳ Processing...
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderDebateInterface = () => (
    <div className="debate-interface">
      <h2>🗣️ Debate Mode</h2>
      
      <div className="debate-topic">
        <textarea
          value={debateTopic}
          onChange={(e) => setDebateTopic(e.target.value)}
          placeholder="Enter a topic for the models to debate... (e.g., 'Should AI development be regulated?')"
          rows={4}
          className="topic-textarea"
        />
      </div>

      <div className="debate-rounds">
        <label>Number of Rounds:</label>
        <select 
          value={debateRounds} 
          onChange={(e) => setDebateRounds(parseInt(e.target.value))}
        >
          <option value={2}>2 Rounds - Quick</option>
          <option value={3}>3 Rounds - Standard</option>
          <option value={4}>4 Rounds - Extended</option>
          <option value={5}>5 Rounds - Comprehensive</option>
        </select>
      </div>

      {renderModelSelection()}

      <div className="submit-controls">
        <button
          onClick={handleStartDebate}
          disabled={isDebating || !debateTopic.trim() || selectedModels.length === 0}
          className="btn btn-primary"
        >
          {isDebating ? '⏳ Debate in Progress...' : '🗣️ Start Debate'}
        </button>
        {isDebating && (
          <button onClick={handleCancelDebate} className="btn btn-danger">
            ⏹️ Cancel Debate
          </button>
        )}
      </div>

      {Object.keys(debateState).length > 0 && (
        <div className="debate-display">
          <h3>🎭 Live Debate</h3>
          
          <div className="debate-participants">
            <strong>Participants:</strong>
            {(debateState.participants || selectedModels).map(participant => (
              <span key={participant} className="participant-tag">
                🤖 {participant}
              </span>
            ))}
          </div>

          <div className="debate-progress">
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{
                  width: `${((debateState.current_round || 1) - 1) / (debateState.total_rounds || debateRounds) * 100}%`
                }}
              />
            </div>
            <div className="progress-text">
              Round {debateState.current_round || 1} of {debateState.total_rounds || debateRounds}
            </div>
          </div>

          <div className="debate-rounds-display">
            {Array.from({length: debateState.current_round || 1}, (_, i) => i + 1).map(roundNum => (
              <div key={roundNum} className="debate-round">
                <h4>Round {roundNum}</h4>
                {debateState[`round_${roundNum}`] && Object.entries(debateState[`round_${roundNum}`]).map(([modelName, response]) => (
                  <div key={modelName} className="debate-response">
                    <h5>🤖 {modelName}</h5>
                    <div className="response-content">{response.content}</div>
                    {response.time && (
                      <div className="response-time">⏱️ {response.time.toFixed(2)}s</div>
                    )}
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const renderDashboard = () => (
    <div className="dashboard">
      <h2>📊 Dashboard</h2>
      
      <div className="dashboard-grid">
        <div className="dashboard-card">
          <h3>🖥️ System Resources</h3>
          <div className="metrics">
            <div className="metric">
              <span className="metric-label">CPU Usage</span>
              <span className="metric-value">45.2%</span>
            </div>
            <div className="metric">
              <span className="metric-label">Memory Usage</span>
              <span className="metric-value">62.8%</span>
            </div>
            <div className="metric">
              <span className="metric-label">Disk Usage</span>
              <span className="metric-value">34.5%</span>
            </div>
          </div>
        </div>

        <div className="dashboard-card">
          <h3>🤖 Model Status</h3>
          <div className="metrics">
            <div className="metric">
              <span className="metric-label">Total Models</span>
              <span className="metric-value">{models.length}</span>
            </div>
            <div className="metric">
              <span className="metric-label">Active Models</span>
              <span className="metric-value">{models.filter(m => m.active !== false).length}</span>
            </div>
            <div className="metric">
              <span className="metric-label">Avg Response Time</span>
              <span className="metric-value">2.3s</span>
            </div>
          </div>
        </div>

        <div className="dashboard-card full-width">
          <h3>📋 Recent Activity</h3>
          <div className="activity-log">
            <div className="activity-item">
              <span className="activity-time">2 minutes ago</span>
              <span className="activity-action">Q&A Query</span>
              <span className="activity-models">3 models</span>
              <span className="activity-status completed">🟢 Completed</span>
            </div>
            <div className="activity-item">
              <span className="activity-time">5 minutes ago</span>
              <span className="activity-action">Debate Started</span>
              <span className="activity-models">4 models</span>
              <span className="activity-status progress">🟡 In Progress</span>
            </div>
            <div className="activity-item">
              <span className="activity-time">10 minutes ago</span>
              <span className="activity-action">Model Refresh</span>
              <span className="activity-models">8 models</span>
              <span className="activity-status completed">🟢 Completed</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>🤖 Multi-Model AI Assistant</h1>
          <p>React Implementation - Query multiple AI models or watch them debate</p>
        </div>
      </header>

      <nav className="app-nav">
        <button
          onClick={() => setCurrentMode('qa')}
          className={`nav-btn ${currentMode === 'qa' ? 'active' : ''}`}
        >
          ❓ Q&A
        </button>
        <button
          onClick={() => setCurrentMode('debate')}
          className={`nav-btn ${currentMode === 'debate' ? 'active' : ''}`}
        >
          🗣️ Debate
        </button>
        <button
          onClick={() => setCurrentMode('dashboard')}
          className={`nav-btn ${currentMode === 'dashboard' ? 'active' : ''}`}
        >
          📊 Dashboard
        </button>
      </nav>

      <main className="app-main">
        {error && (
          <div className="error-message">
            ❌ {error}
            <button onClick={() => setError('')} className="error-close">×</button>
          </div>
        )}

        {loading && (
          <div className="loading-message">
            ⏳ Loading models...
          </div>
        )}

        {currentMode === 'qa' && renderQAInterface()}
        {currentMode === 'debate' && renderDebateInterface()}
        {currentMode === 'dashboard' && renderDashboard()}
      </main>

      <footer className="app-footer">
        <div className="footer-content">
          <span>Session ID: {sessionId.substring(0, 8)}...</span>
          <span>Models: {models.length}</span>
          <span>Selected: {selectedModels.length}</span>
        </div>
      </footer>
    </div>
  );
};

export default App;
