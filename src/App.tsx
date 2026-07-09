import { useMemo, useState } from 'react';
import { sampleData } from './data';
import { DataItem, SourceType } from './types';
import { groupBySource, mapStrategyQuestion, sourceColors, sourceLabels } from './helpers';

const presetQuestions = [
  'What should our next product priority be?',
  'What are the top retention risks from current data?',
  'How can we differentiate from competitors this quarter?'
];

const sourceOrder: SourceType[] = ['feedback', 'support', 'jira', 'usage', 'competitor'];

function App() {
  const [selectedSource, setSelectedSource] = useState<SourceType | 'all'>('all');
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [selectedItem, setSelectedItem] = useState<DataItem | null>(null);

  const grouped = useMemo(() => groupBySource(sampleData), []);

  const filtered = useMemo(() => {
    if (selectedSource === 'all') return sampleData;
    return sampleData.filter((item) => item.source === selectedSource);
  }, [selectedSource]);

  const handleAsk = () => {
    const summary = filtered.map((item) => `${item.source.toUpperCase()}: ${item.title}`).join(' | ');
    const questionText = question.trim() ? question : presetQuestions[0];
    setAnswer(
      `Based on the available sources (${selectedSource === 'all' ? 'all data' : sourceLabels[selectedSource]}), focus on:
- ${mapStrategyQuestion(questionText)}
- Look for themes across customer feedback, support friction, usage drop-off, Jira execution, and competitor differentiation.
- Key signals: ${summary || 'no data selected'}.`
    );
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="panel">
          <h1>Product Strategy Copilot</h1>
          <p>Bring feedback, support, Jira, usage, and competitor insights together for better strategy decisions.</p>
        </div>

        <div className="panel">
          <h2>Data sources</h2>
          <div className="source-filters">
            <button
              className={selectedSource === 'all' ? 'active' : ''}
              onClick={() => setSelectedSource('all')}
            >
              All
            </button>
            {sourceOrder.map((source) => (
              <button
                key={source}
                className={selectedSource === source ? 'active' : ''}
                style={{ borderColor: sourceColors[source] }}
                onClick={() => setSelectedSource(source)}
              >
                {sourceLabels[source]}
              </button>
            ))}
          </div>
        </div>

        <div className="panel">
          <h2>Top insights</h2>
          {sourceOrder.map((source) => (
            <div key={source} className="insight-card">
              <div className="insight-header" style={{ borderLeftColor: sourceColors[source] }}>
                <span>{sourceLabels[source]}</span>
                <strong>{grouped[source].length}</strong>
              </div>
              <p>{grouped[source][0]?.summary ?? 'No items yet.'}</p>
            </div>
          ))}
        </div>
      </aside>

      <main className="main-content">
        <section className="question-panel">
          <h2>Ask a strategy question</h2>
          <div className="presets">
            {presetQuestions.map((preset) => (
              <button key={preset} onClick={() => setQuestion(preset)}>{preset}</button>
            ))}
          </div>

          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Type a product strategy question..."
          />
          <button className="ask-button" onClick={handleAsk}>Get insight</button>
          {answer && (
            <div className="answer-block">
              <h3>Strategic insight</h3>
              <pre>{answer}</pre>
            </div>
          )}
        </section>

        <section className="data-panel">
          <div className="panel-header">
            <h2>Unified intelligence</h2>
            <span>{filtered.length} items</span>
          </div>

          <div className="data-grid">
            {filtered.map((item) => (
              <article
                key={item.id}
                className={`data-card ${selectedItem?.id === item.id ? 'selected' : ''}`}
                onClick={() => setSelectedItem(item)}
              >
                <div className="data-card-header" style={{ background: sourceColors[item.source] }}>
                  {sourceLabels[item.source]}
                </div>
                <h3>{item.title}</h3>
                <p>{item.summary}</p>
                <div className="data-meta">
                  <span>{item.createdAt}</span>
                  <div>{item.tags.map((tag) => <small key={tag}>{tag}</small>)}</div>
                </div>
              </article>
            ))}
          </div>

          {selectedItem && (
            <div className="detail-panel">
              <h3>Detail</h3>
              <p><strong>{selectedItem.title}</strong></p>
              <p>{selectedItem.details}</p>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
