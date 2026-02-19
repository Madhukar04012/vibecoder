# VibeCoder IDE Frontend Plan
## Building an Atmos-Level IDE Experience

This plan complements the backend transformation with the frontend IDE features needed to match Atmos.

---

## 🎨 Complete IDE Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     VibeCoder IDE                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  Project   │  │   Agent    │  │  Document  │            │
│  │   Setup    │  │  Dashboard │  │   Viewer   │            │
│  └────────────┘  └────────────┘  └────────────┘            │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  Code Editor                         │   │
│  │  main.py                              Monaco Editor  │   │
│  │  ┌───────────────────────────────────────────────┐  │   │
│  │  │ def create_user(user_data: dict):            │  │   │
│  │  │     # AI suggestion: Add validation          │  │   │
│  │  │     validate_user_data(user_data)  [Accept] │  │   │
│  │  └───────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────┐  ┌──────────────────────────────────┐    │
│  │    Files    │  │        Terminal                   │    │
│  │  📁 src     │  │  $ python main.py                 │    │
│  │  📁 tests   │  │  Server running on port 8000...   │    │
│  │  📄 main.py │  │                                    │    │
│  └─────────────┘  └──────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

---

## 🚀 Phase 1: Core IDE Features (Weeks 1-4)

### 1.1 Project Creation Wizard

**File: `frontend/src/components/ProjectWizard.tsx`**
```typescript
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface ProjectTemplate {
  id: string;
  name: string;
  description: string;
  icon: string;
  defaultStack: TechStack;
}

const templates: ProjectTemplate[] = [
  {
    id: 'web_app',
    name: 'Web Application',
    description: 'Full-stack web app with React + FastAPI',
    icon: '🌐',
    defaultStack: {
      frontend: 'react',
      backend: 'fastapi',
      database: 'postgres'
    }
  },
  {
    id: 'api',
    name: 'REST API',
    description: 'Backend API service',
    icon: '🔌',
    defaultStack: {
      backend: 'fastapi',
      database: 'postgres'
    }
  },
  {
    id: 'mobile',
    name: 'Mobile App',
    description: 'React Native mobile app',
    icon: '📱',
    defaultStack: {
      mobile: 'react_native',
      backend: 'firebase'
    }
  },
  {
    id: 'ml_pipeline',
    name: 'ML Pipeline',
    description: 'Machine learning data pipeline',
    icon: '🤖',
    defaultStack: {
      framework: 'pytorch',
      backend: 'fastapi'
    }
  }
];

export function ProjectWizard({ onComplete }: { onComplete: (config: ProjectConfig) => void }) {
  const [step, setStep] = useState(1);
  const [config, setConfig] = useState<Partial<ProjectConfig>>({});

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 text-white">
      <div className="max-w-4xl mx-auto py-12 px-6">
        {/* Progress indicator */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            {[1, 2, 3, 4].map((s) => (
              <div
                key={s}
                className={`w-1/4 h-2 rounded-full mx-1 ${
                  s <= step ? 'bg-blue-500' : 'bg-gray-700'
                }`}
              />
            ))}
          </div>
          <p className="text-sm text-gray-400">Step {step} of 4</p>
        </div>

        <AnimatePresence mode="wait">
          {step === 1 && <Step1_Template config={config} setConfig={setConfig} />}
          {step === 2 && <Step2_Description config={config} setConfig={setConfig} />}
          {step === 3 && <Step3_TechStack config={config} setConfig={setConfig} />}
          {step === 4 && <Step4_Review config={config} />}
        </AnimatePresence>

        {/* Navigation */}
        <div className="flex justify-between mt-8">
          <button
            onClick={() => setStep(Math.max(1, step - 1))}
            disabled={step === 1}
            className="px-6 py-2 bg-gray-700 rounded-lg disabled:opacity-50"
          >
            Back
          </button>
          <button
            onClick={() => {
              if (step === 4) {
                onComplete(config as ProjectConfig);
              } else {
                setStep(step + 1);
              }
            }}
            className="px-6 py-2 bg-blue-600 rounded-lg hover:bg-blue-700"
          >
            {step === 4 ? 'Create Project' : 'Next'}
          </button>
        </div>
      </div>
    </div>
  );
}

function Step1_Template({ config, setConfig }: StepProps) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
    >
      <h1 className="text-3xl font-bold mb-2">Choose a template</h1>
      <p className="text-gray-400 mb-8">Start with a template or build from scratch</p>

      <div className="grid grid-cols-2 gap-4">
        {templates.map((template) => (
          <button
            key={template.id}
            onClick={() => setConfig({ ...config, template: template.id })}
            className={`p-6 rounded-xl border-2 text-left transition-all ${
              config.template === template.id
                ? 'border-blue-500 bg-blue-500/10'
                : 'border-gray-700 hover:border-gray-600'
            }`}
          >
            <div className="text-4xl mb-3">{template.icon}</div>
            <h3 className="text-xl font-semibold mb-2">{template.name}</h3>
            <p className="text-sm text-gray-400">{template.description}</p>
          </button>
        ))}
      </div>
    </motion.div>
  );
}

function Step2_Description({ config, setConfig }: StepProps) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
    >
      <h1 className="text-3xl font-bold mb-2">Describe your project</h1>
      <p className="text-gray-400 mb-8">Tell us what you want to build</p>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium mb-2">Project Name</label>
          <input
            type="text"
            placeholder="my-awesome-app"
            value={config.projectName || ''}
            onChange={(e) => setConfig({ ...config, projectName: e.target.value })}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:border-blue-500 outline-none"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">
            What should your app do?
          </label>
          <textarea
            rows={6}
            placeholder="I want to build a task management app where users can create, organize, and track their todos. It should have user authentication, different task categories, and due date reminders."
            value={config.description || ''}
            onChange={(e) => setConfig({ ...config, description: e.target.value })}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:border-blue-500 outline-none resize-none"
          />
          <p className="text-xs text-gray-500 mt-2">
            Be specific! The more detail, the better the results.
          </p>
        </div>

        {/* AI-powered suggestions */}
        {config.description && config.description.length > 50 && (
          <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
            <div className="flex items-start gap-3">
              <div className="text-2xl">💡</div>
              <div>
                <h4 className="font-semibold mb-1">AI Suggestions</h4>
                <ul className="text-sm text-gray-300 space-y-1">
                  <li>• Consider adding email notifications for due dates</li>
                  <li>• Users might want to share tasks with team members</li>
                  <li>• Dark mode would improve user experience</li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
}

function Step3_TechStack({ config, setConfig }: StepProps) {
  const [customizing, setCustomizing] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
    >
      <h1 className="text-3xl font-bold mb-2">Tech Stack</h1>
      <p className="text-gray-400 mb-8">
        We've suggested a stack based on your project. Customize if needed.
      </p>

      <div className="space-y-6">
        {/* Suggested stack */}
        <div className="p-6 bg-gray-800 rounded-lg border border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Recommended Stack</h3>
            <button
              onClick={() => setCustomizing(!customizing)}
              className="text-sm text-blue-400 hover:text-blue-300"
            >
              {customizing ? 'Use Recommended' : 'Customize'}
            </button>
          </div>

          {!customizing ? (
            <div className="grid grid-cols-2 gap-4">
              <StackItem label="Frontend" value="React + TypeScript" icon="⚛️" />
              <StackItem label="Backend" value="FastAPI + Python" icon="🐍" />
              <StackItem label="Database" value="PostgreSQL" icon="🐘" />
              <StackItem label="Deployment" value="Docker + AWS" icon="☁️" />
            </div>
          ) : (
            <div className="space-y-4">
              <TechSelector
                label="Frontend"
                options={['React', 'Vue', 'Angular', 'Svelte']}
                value={config.techStack?.frontend}
                onChange={(v) =>
                  setConfig({
                    ...config,
                    techStack: { ...config.techStack, frontend: v }
                  })
                }
              />
              <TechSelector
                label="Backend"
                options={['FastAPI', 'Django', 'Express', 'Flask']}
                value={config.techStack?.backend}
                onChange={(v) =>
                  setConfig({
                    ...config,
                    techStack: { ...config.techStack, backend: v }
                  })
                }
              />
              {/* More selectors... */}
            </div>
          )}
        </div>

        {/* Advanced options */}
        <details className="p-4 bg-gray-800/50 rounded-lg">
          <summary className="cursor-pointer font-medium">Advanced Options</summary>
          <div className="mt-4 space-y-3">
            <label className="flex items-center gap-2">
              <input type="checkbox" className="w-4 h-4" />
              <span className="text-sm">Include authentication</span>
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" className="w-4 h-4" />
              <span className="text-sm">Add CI/CD pipeline</span>
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" className="w-4 h-4" />
              <span className="text-sm">Setup monitoring & logging</span>
            </label>
          </div>
        </details>
      </div>
    </motion.div>
  );
}
```

### 1.2 Live Agent Dashboard

**File: `frontend/src/components/AgentDashboard.tsx`**
```typescript
import { useAgentStatus } from '@/hooks/useAgentStatus';
import { motion } from 'framer-motion';

export function AgentDashboard({ runId }: { runId: string }) {
  const { agents, currentStage } = useAgentStatus(runId);

  return (
    <div className="p-6 bg-gray-900 rounded-xl">
      <h2 className="text-xl font-bold mb-6">Agent Activity</h2>

      <div className="space-y-4">
        {agents.map((agent, i) => (
          <AgentCard key={agent.name} agent={agent} delay={i * 0.1} />
        ))}
      </div>

      {/* Stage indicator */}
      <div className="mt-6 pt-6 border-t border-gray-800">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-400">Current Stage:</span>
          <span className="font-medium">{currentStage}</span>
        </div>
      </div>
    </div>
  );
}

function AgentCard({ agent, delay }: { agent: Agent; delay: number }) {
  const statusColors = {
    idle: 'bg-gray-600',
    working: 'bg-blue-500 animate-pulse',
    complete: 'bg-green-500',
    failed: 'bg-red-500'
  };

  const statusIcons = {
    idle: '⏸️',
    working: '⚡',
    complete: '✓',
    failed: '✗'
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay }}
      className="p-4 bg-gray-800 rounded-lg"
    >
      <div className="flex items-center gap-4">
        {/* Status indicator */}
        <div className="relative">
          <div className={`w-10 h-10 rounded-full ${statusColors[agent.status]} flex items-center justify-center`}>
            <span className="text-lg">{statusIcons[agent.status]}</span>
          </div>
          {agent.status === 'working' && (
            <div className="absolute inset-0 rounded-full border-2 border-blue-400 animate-ping" />
          )}
        </div>

        {/* Agent info */}
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold">{agent.name}</h3>
            {agent.role && (
              <span className="text-xs px-2 py-1 bg-gray-700 rounded">
                {agent.role}
              </span>
            )}
          </div>
          <p className="text-sm text-gray-400 mt-1">{agent.currentTask || 'Waiting...'}</p>
          
          {/* Progress bar */}
          {agent.status === 'working' && (
            <div className="mt-2 h-1 bg-gray-700 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-blue-500"
                initial={{ width: '0%' }}
                animate={{ width: `${agent.progress}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
          )}
        </div>

        {/* Actions */}
        {agent.output && (
          <button
            onClick={() => window.open(`/documents/${agent.output}`, '_blank')}
            className="px-3 py-1 text-sm bg-gray-700 hover:bg-gray-600 rounded"
          >
            View Output
          </button>
        )}
      </div>

      {/* Expandable details */}
      {agent.status === 'working' && agent.details && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          className="mt-3 pt-3 border-t border-gray-700"
        >
          <div className="text-xs text-gray-400 space-y-1">
            {agent.details.map((detail, i) => (
              <div key={i}>• {detail}</div>
            ))}
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
```

### 1.3 Document Viewer with Approval Flow

**File: `frontend/src/components/DocumentViewer.tsx`**
```typescript
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';

interface DocumentViewerProps {
  document: Document;
  onApprove?: () => void;
  onReject?: (feedback: string) => void;
  onRequestChanges?: (changes: string) => void;
}

export function DocumentViewer({ document, onApprove, onReject, onRequestChanges }: DocumentViewerProps) {
  const [feedback, setFeedback] = useState('');
  const [showFeedback, setShowFeedback] = useState(false);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">{document.title}</h2>
            <div className="flex items-center gap-4 mt-1 text-sm text-gray-400">
              <span>📄 {document.doc_type}</span>
              <span>👤 {document.created_by}</span>
              <span>📅 {formatDate(document.created_at)}</span>
              <span className={`px-2 py-0.5 rounded text-xs ${
                document.status === 'approved' ? 'bg-green-500/20 text-green-400' :
                document.status === 'rejected' ? 'bg-red-500/20 text-red-400' :
                'bg-yellow-500/20 text-yellow-400'
              }`}>
                {document.status}
              </span>
            </div>
          </div>

          {/* Version selector */}
          {document.version_history.length > 0 && (
            <select className="px-3 py-1 bg-gray-700 rounded text-sm">
              <option>Version {document.version} (current)</option>
              {document.version_history.map((v) => (
                <option key={v.version_number}>Version {v.version_number}</option>
              ))}
            </select>
          )}
        </div>
      </div>

      {/* Document content */}
      <div className="flex-1 overflow-auto p-6 bg-gray-900">
        <div className="max-w-4xl mx-auto prose prose-invert">
          <ReactMarkdown>{document.content_markdown}</ReactMarkdown>
        </div>
      </div>

      {/* Approval actions */}
      {document.status === 'draft' && (onApprove || onReject) && (
        <div className="p-4 bg-gray-800 border-t border-gray-700">
          {!showFeedback ? (
            <div className="flex gap-3">
              <button
                onClick={onApprove}
                className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg font-medium"
              >
                ✓ Approve
              </button>
              <button
                onClick={() => setShowFeedback(true)}
                className="flex-1 px-4 py-2 bg-yellow-600 hover:bg-yellow-700 rounded-lg font-medium"
              >
                📝 Request Changes
              </button>
              <button
                onClick={() => setShowFeedback(true)}
                className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg font-medium"
              >
                ✗ Reject
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <textarea
                rows={4}
                placeholder="Explain what needs to change..."
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg outline-none focus:border-blue-500"
              />
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    onRequestChanges?.(feedback);
                    setShowFeedback(false);
                    setFeedback('');
                  }}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded"
                >
                  Send Feedback
                </button>
                <button
                  onClick={() => setShowFeedback(false)}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

---

## 🎯 Phase 2: Advanced IDE Features (Weeks 5-8)

### 2.1 Visual Workflow Builder

```typescript
// Drag-and-drop workflow editor
export function WorkflowBuilder() {
  const [nodes, setNodes] = useState<WorkflowNode[]>([]);
  
  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
    >
      {/* Custom nodes for each agent */}
      <AgentNode type="product_manager" />
      <AgentNode type="architect" />
      <AgentNode type="engineer" />
      {/* User can drag to create custom workflows */}
    </ReactFlow>
  );
}
```

### 2.2 Inline AI Suggestions

```typescript
// Code editor with AI suggestions
export function CodeEditor() {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  
  return (
    <MonacoEditor
      onCursorPositionChange={async (position) => {
        const context = getCodeContext(position);
        const suggestions = await getAISuggestions(context);
        setSuggestions(suggestions);
      }}
      decorations={[
        ...suggestions.map(s => ({
          range: s.range,
          options: {
            inlineClassName: 'ai-suggestion',
            hoverMessage: { value: s.description }
          }
        }))
      ]}
    />
  );
}
```

### 2.3 Real-time Collaboration

```typescript
// WebSocket for real-time updates
export function CollaborationProvider({ children }) {
  const ws = useWebSocket('/ws/collaboration');
  
  useEffect(() => {
    ws.on('agent_update', (update) => {
      // Show toast notification
      toast.info(`${update.agent} completed ${update.task}`);
    });
    
    ws.on('document_created', (doc) => {
      // Update document list
      addDocument(doc);
    });
  }, [ws]);
  
  return children;
}
```

---

## 🎨 Phase 3: Premium Features (Weeks 9-12)

### 3.1 Interactive Debugging

```typescript
export function DebuggerPanel() {
  return (
    <div className="debug-panel">
      {/* Visual state machine */}
      <StateMachineVisualization currentState={state} />
      
      {/* Agent conversation history */}
      <ConversationTimeline messages={messages} />
      
      {/* Document lineage graph */}
      <DocumentGraph documents={documents} />
      
      {/* Time-travel debugging */}
      <TimeTravel snapshots={snapshots} />
    </div>
  );
}
```

### 3.2 Cost Dashboard

```typescript
export function CostDashboard() {
  const { usage } = useCostTracking();
  
  return (
    <div className="cost-dashboard">
      <div className="grid grid-cols-3 gap-4">
        <MetricCard
          title="Today's Cost"
          value={`$${usage.today.toFixed(2)}`}
          trend="+12%"
        />
        <MetricCard
          title="This Month"
          value={`$${usage.month.toFixed(2)}`}
          budget="$500"
        />
        <MetricCard
          title="Avg per Project"
          value={`$${usage.avgPerProject.toFixed(2)}`}
          trend="-8%"
        />
      </div>
      
      {/* Cost breakdown by agent */}
      <CostByAgentChart data={usage.byAgent} />
    </div>
  );
}
```

---

## 🔌 Integration Points

### Backend API Endpoints Needed

```python
# FastAPI routes for IDE features

@router.post("/projects/create")
async def create_project(config: ProjectConfig):
    """Start new project from wizard"""
    run_id = await orchestrator.start_project(config)
    return {"run_id": run_id}

@router.get("/agents/status/{run_id}")
async def get_agent_status(run_id: str):
    """Get real-time agent status"""
    return await orchestrator.get_status(run_id)

@router.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    """Get document for viewer"""
    doc = document_store.get(doc_id)
    return {
        "title": doc.title,
        "content_markdown": doc.to_markdown(),
        "metadata": doc.metadata,
        "status": doc.status
    }

@router.post("/documents/{doc_id}/approve")
async def approve_document(doc_id: str):
    """Approve document"""
    doc = document_store.get(doc_id)
    doc.approved = True
    doc.status = "approved"
    document_store.save(doc)
    # Continue workflow
    await orchestrator.continue_workflow(doc.run_id)

@router.post("/documents/{doc_id}/feedback")
async def give_feedback(doc_id: str, feedback: str):
    """Request changes to document"""
    await orchestrator.handle_feedback(doc_id, feedback)

@router.websocket("/ws/updates/{run_id}")
async def websocket_updates(websocket: WebSocket, run_id: str):
    """WebSocket for real-time updates"""
    await websocket.accept()
    
    async for event in orchestrator.stream_events(run_id):
        await websocket.send_json(event)
```

---

## 📊 Complete Feature Comparison

| Feature | Your Current IDE | After Backend Plan | After Frontend Plan | Atmos Level |
|---------|------------------|-------------------|-------------------|-------------|
| Project Setup | Manual config | ✓ API available | ✓✓ Visual wizard | ✓✓✓ |
| Agent Visibility | Logs only | ✓ Events | ✓✓ Live dashboard | ✓✓✓ |
| Document Review | No | ✓ Via API | ✓✓ Visual viewer | ✓✓✓ |
| Approval Flow | No | ✓ Backend | ✓✓ UI buttons | ✓✓✓ |
| Code Editor | Basic | Basic | ✓✓ AI suggestions | ✓✓✓ |
| Collaboration | No | ✓ Multi-user backend | ✓✓ Real-time UI | ✓✓✓ |
| Debugging | Basic logs | ✓ Traces | ✓✓ Visual debugger | ✓✓✓ |
| Cost Tracking | No | ✓ Backend metrics | ✓✓ Dashboard | ✓✓✓ |

---

## 🎯 Complete System = Backend + Frontend

To get an **Atmos-level IDE**, you need:

### ✅ Backend (from main plan):
- Agent society
- Document system
- Memory & learning
- Production infrastructure

### ✅ Frontend (this plan):
- Project wizard
- Agent dashboard
- Document viewer
- Code editor
- Collaboration features

### Total Timeline:
- Backend: 6-9 months (4-6 engineers)
- Frontend: 3-4 months (2-3 frontend engineers, parallel to backend)
- **Total: 9-12 months for complete Atmos-level system**

---

## 💡 MVP Recommendation

**Start with these 5 features (2-3 months):**

1. ✅ Project creation wizard
2. ✅ Live agent status dashboard
3. ✅ Document viewer with approval
4. ✅ Basic code editor
5. ✅ WebSocket real-time updates

This gives you a functional Atmos-like IDE while the backend evolves.

---

## 🚀 Quick Start

Want me to build any of these components? I can create:
- Complete React components with Tailwind
- WebSocket integration
- State management with Zustand
- Monaco editor setup
- Real-time collaboration features

Just say which part you want to start with!
