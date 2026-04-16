# TypeScript/React Code Standards

## File Organization

**Naming Convention:**
- Components: `PascalCase.tsx` (e.g., `AgentEditor.tsx`)
- Hooks: `use<Feature>.ts` (e.g., `useSearch.ts`)
- Utils: `snake_case.ts` (e.g., `format_utils.ts`)
- Types: `snake_case.types.ts` or inline in files
- Styles: `<ComponentName>.module.css` or Tailwind

**Directory Structure:**
```
web/src/
├── pages/          # Page components (lazy-loaded)
├── components/     # Reusable UI components
├── hooks/          # Custom React hooks
├── services/       # API clients, business logic
├── stores/         # Zustand state
├── types/          # TypeScript interfaces
├── utils/          # Utility functions
└── styles/         # Global CSS, theme
```

## Type Definitions

**Always define types:**
```typescript
// types/document.types.ts
export interface Document {
    id: string;
    name: string;
    kb_id: string;
    status: "PARSING" | "DONE" | "ERROR";
    created_at: string;
}

export interface SearchResult {
    chunks: ChunkData[];
    total: number;
}

export type DocumentStatus = Document["status"];
```

**Use in components:**
```typescript
import { Document } from "@/types/document.types";

interface DocumentListProps {
    documents: Document[];
    onSelect: (doc: Document) => void;
}

export function DocumentList({ documents, onSelect }: DocumentListProps) {
    return (
        <ul>
            {documents.map(doc => (
                <li key={doc.id} onClick={() => onSelect(doc)}>
                    {doc.name}
                </li>
            ))}
        </ul>
    );
}
```

## Component Best Practices

**Small, focused components:**
```typescript
// Good: Single responsibility
interface ButtonProps {
    label: string;
    onClick: () => void;
    disabled?: boolean;
}

export function Button({ label, onClick, disabled }: ButtonProps) {
    return (
        <button
            onClick={onClick}
            disabled={disabled}
            className="px-4 py-2 bg-blue-500 text-white rounded"
        >
            {label}
        </button>
    );
}
```

**Use hooks for logic:**
```typescript
// hooks/useDocumentSearch.ts
export function useDocumentSearch(query: string) {
    const { data, isLoading, error } = useQuery({
        queryKey: ["documents", query],
        queryFn: () => api.search(query),
    });
    
    return { documents: data || [], isLoading, error };
}

// components/SearchResults.tsx
export function SearchResults() {
    const [query, setQuery] = useState("");
    const { documents, isLoading } = useDocumentSearch(query);
    
    return (
        <>
            <input value={query} onChange={e => setQuery(e.target.value)} />
            {isLoading && <p>Loading...</p>}
            <DocumentList documents={documents} />
        </>
    );
}
```

## State Management

**TanStack Query for server state:**
```typescript
const { data: documents } = useQuery({
    queryKey: ["documents"],
    queryFn: () => api.listDocuments(),
    staleTime: 5 * 60 * 1000, // 5 minutes
});

const { mutate: uploadDocument } = useMutation({
    mutationFn: (file: File) => api.uploadDocument(file),
    onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
});
```

**Zustand for UI state:**
```typescript
import { create } from "zustand";

interface UIState {
    sidebarOpen: boolean;
    toggleSidebar: () => void;
}

export const useUIStore = create<UIState>(set => ({
    sidebarOpen: true,
    toggleSidebar: () => set(state => ({
        sidebarOpen: !state.sidebarOpen
    })),
}));

// Usage
export function Layout() {
    const { sidebarOpen, toggleSidebar } = useUIStore();
    return (
        <>
            <button onClick={toggleSidebar}>Toggle</button>
            {sidebarOpen && <Sidebar />}
        </>
    );
}
```

## API Integration

**Typed API methods:**
```typescript
// services/documentService.ts
export const documentService = {
    list: async (): Promise<Document[]> => {
        const res = await apiClient.get("/api/v1/documents");
        return res.data.data;
    },
    
    upload: async (file: File): Promise<Document> => {
        const formData = new FormData();
        formData.append("file", file);
        const res = await apiClient.post("/api/v1/documents", formData);
        return res.data.data;
    },
    
    delete: async (id: string): Promise<void> => {
        await apiClient.delete(`/api/v1/documents/${id}`);
    },
};
```

**Axios client with interceptors:**
```typescript
export const apiClient = axios.create({
    baseURL: process.env.REACT_APP_API_URL,
    timeout: 30000,
});

apiClient.interceptors.request.use(config => {
    const token = localStorage.getItem("auth_token");
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

apiClient.interceptors.response.use(
    response => response,
    error => {
        if (error.response?.status === 401) {
            localStorage.removeItem("auth_token");
            window.location.href = "/login";
        }
        return Promise.reject(error);
    }
);
```

## Testing

**Jest + React Testing Library:**
```typescript
import { render, screen, fireEvent } from "@testing-library/react";
import { Button } from "@/components/Button";

describe("Button component", () => {
    it("renders with label", () => {
        render(<Button label="Click me" onClick={() => {}} />);
        expect(screen.getByText("Click me")).toBeInTheDocument();
    });
    
    it("calls onClick handler", () => {
        const onClick = jest.fn();
        render(<Button label="Click" onClick={onClick} />);
        fireEvent.click(screen.getByText("Click"));
        expect(onClick).toHaveBeenCalled();
    });
    
    it("disables button when disabled prop set", () => {
        render(<Button label="Click" onClick={() => {}} disabled />);
        expect(screen.getByRole("button")).toBeDisabled();
    });
});
```

---

**Version:** 0.24.0  
**Last Updated:** 2026-04-16
