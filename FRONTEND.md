# Frontend Architecture

## Technology Stack
- **Framework**: React 19.1.1 with TypeScript
- **Build Tool**: Vite 7.1.2
- **Styling**: Tailwind CSS 3.4.14
- **Routing**: React Router DOM 7.8.2
- **Dev Server**: Port 8082 with proxy to backend

## Project Structure

```
frontend/
├── src/
│   ├── App.tsx              # Main app component with routing
│   ├── main.tsx            # Application entry point
│   ├── config.ts           # Configuration constants
│   ├── lib/
│   │   ├── api.ts          # Backend API client
│   │   ├── brandingTypes.ts # Branding type definitions
│   │   ├── brandingToStyles.ts # Dynamic styling
│   │   ├── color.ts        # Color utilities
│   │   ├── theme.ts        # Theme management
│   │   ├── voice.ts        # Voice/audio utilities
│   │   └── prompt.ts       # AI prompt templates
│   └── pages/
│       ├── ClientChat.tsx  # Main chat interface
│       ├── AdminLogin.tsx  # Admin authentication
│       └── AdminBranding.tsx # Branding configuration
├── vite.config.ts          # Vite configuration
├── package.json            # Dependencies
└── tailwind.config.js      # Tailwind configuration
```

## Vite Proxy Configuration

```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  server: {
    port: 8080,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8601',
        changeOrigin: true,
      },
    },
  },
});
```

**Development Flow:**
- Frontend serves on port 8082
- API requests to `/api/*` proxied to backend on port 8601
- Hot reload enabled for development

## Component Architecture

### App Component
```typescript
// App.tsx - Main routing and navigation
function Navigation() {
  // Show navigation only on localhost or with __devNav=1
  const shouldShowNav = isLocalhost || hasDevNav;
  return shouldShowNav ? <nav>...</nav> : null;
}

export default function App() {
  return (
    <BrowserRouter>
      <Navigation />
      <Routes>
        <Route path="/" element={<ClientChat />} />
        <Route path="/admin/login" element={<AdminLogin />} />
        <Route path="/admin/branding" element={<AdminBranding />} />
      </Routes>
    </BrowserRouter>
  );
}
```

### Chat Interface States

#### 1. Idle State
```typescript
interface IdleState {
  status: 'idle';
  message: '';
  isLoading: false;
  messages: [];
}
```

#### 2. Loading State
```typescript
interface LoadingState {
  status: 'loading';
  message: string;
  isLoading: true;
  showSpinner: true;
}
```

#### 3. Streaming State
```typescript
interface StreamingState {
  status: 'streaming';
  currentResponse: string;
  isStreaming: true;
  sources: Source[];
}
```

#### 4. Error State
```typescript
interface ErrorState {
  status: 'error';
  errorMessage: string;
  isLoading: false;
  canRetry: true;
}
```

### Message Types
```typescript
interface ChatMessage {
  id: string;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  sources?: Source[];
}

interface Source {
  name: string;      // "document.pdf (p.3)"
  url: string;       // "http://host/files/document.pdf#page=3"
}
```

## Citation Rendering

### Citation Display Component
```typescript
function CitationList({ sources }: { sources: Source[] }) {
  return (
    <div className="citations">
      {sources.map((source, idx) => (
        <a
          key={idx}
          href={source.url}
          target="_blank"
          rel="noopener noreferrer"
          className="citation-link"
        >
          📄 {source.name}
        </a>
      ))}
    </div>
  );
}
```

### URL Format
- **PDF with page**: `http://localhost:8601/files/document.pdf#page=3`
- **Non-PDF**: `http://localhost:8601/files/document.docx`
- **Encoding**: URL-safe encoding for filenames with spaces/special chars

## Branding System

### Dynamic Branding Types
```typescript
interface BrandingConfig {
  companyName?: string;
  primaryColor?: string;
  secondaryColor?: string;
  logoUrl?: string;
}
```

### Style Application
```typescript
// lib/brandingToStyles.ts
export function applyBrandingToStyles(branding: BrandingConfig) {
  const root = document.documentElement;
  
  if (branding.primaryColor) {
    root.style.setProperty('--color-primary', branding.primaryColor);
  }
  
  if (branding.secondaryColor) {
    root.style.setProperty('--color-secondary', branding.secondaryColor);
  }
}
```

### CSS Custom Properties
```css
/* Applied dynamically via JavaScript */
:root {
  --color-primary: #2563eb;    /* Blue-600 */
  --color-secondary: #64748b;  /* Slate-500 */
}

.btn-primary {
  background-color: var(--color-primary);
}
```

## API Integration

### API Client
```typescript
// lib/api.ts
class ApiClient {
  private baseUrl = '/api';
  
  async chatQuery(query: string): Promise<ChatResponse> {
    const response = await fetch(`${this.baseUrl}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    return response.json();
  }
  
  async getBranding(): Promise<BrandingConfig> {
    const response = await fetch(`${this.baseUrl}/admin/settings/public/branding`);
    return response.json();
  }
}
```

### Error Handling
```typescript
try {
  const response = await apiClient.chatQuery(query);
  setMessages([...messages, response]);
} catch (error) {
  setErrorState({
    message: 'Failed to get response. Please try again.',
    canRetry: true
  });
}
```

## State Management

### Chat State
```typescript
const [messages, setMessages] = useState<ChatMessage[]>([]);
const [isLoading, setIsLoading] = useState(false);
const [currentInput, setCurrentInput] = useState('');
```

### Branding State
```typescript
const [branding, setBranding] = useState<BrandingConfig>({});
const [isLoadingBranding, setIsLoadingBranding] = useState(true);
```

## Keyboard Navigation

### Chat Input Shortcuts
- **Enter**: Send message
- **Shift+Enter**: New line
- **Ctrl+K**: Clear conversation
- **Escape**: Clear current input

### Focus Management
```typescript
useEffect(() => {
  // Auto-focus input after message sent
  if (!isLoading && inputRef.current) {
    inputRef.current.focus();
  }
}, [isLoading]);
```

## Accessibility Features

### Screen Reader Support
```tsx
<div role="log" aria-live="polite" aria-label="Chat conversation">
  {messages.map(message => (
    <div
      key={message.id}
      role="article"
      aria-label={`${message.sender} message`}
    >
      {message.text}
    </div>
  ))}
</div>
```

### Keyboard Navigation
- All interactive elements are keyboard accessible
- Focus indicators visible
- Tab order logical
- ARIA labels for screen readers

## Performance Optimizations

### Code Splitting
```typescript
// Lazy loading for admin components
const AdminBranding = lazy(() => import('./pages/AdminBranding'));
const AdminLogin = lazy(() => import('./pages/AdminLogin'));
```

### Memoization
```typescript
const MessageList = memo(({ messages }: { messages: ChatMessage[] }) => {
  return (
    <div>
      {messages.map(message => (
        <MessageItem key={message.id} message={message} />
      ))}
    </div>
  );
});
```

## Development Tools

### Scripts
```json
{
  "scripts": {
    "dev": "vite",                    // Start dev server
    "build": "tsc -b && vite build", // Production build
    "lint": "eslint .",               // Code linting
    "preview": "vite preview",        // Preview build
    "typecheck": "tsc -b --noEmit",   // Type checking
    "test:api": "curl http://localhost:8600/api/health"
  }
}
```

### Development Features
- Hot reload for instant updates
- TypeScript for type safety
- ESLint for code quality
- Automatic proxy to backend API
- Source maps for debugging