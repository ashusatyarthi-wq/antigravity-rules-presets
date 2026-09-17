# Before & After: Next.js + Supabase Authentication & Queries

### Scenario Overview
A developer instructs an AI agent: *"Add user profile fetching to the dashboard page and display their private organization data."*

---

### ❌ The Naive Implementation (Unconstrained Agent)

```typescript
// app/dashboard/page.tsx
'use client'; // 🚨 Marked entire page as client to use useEffect

import { useEffect, useState } from 'react';
import { createClient } from '@supabase/supabase-js';

// 🚨 Created single client instance directly in client bundle
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY! // 🚨 Catastrophic secret leak in browser bundle!
);

export default function Dashboard() {
  const [user, setUser] = useState<any>(null);
  const [data, setData] = useState<any[]>([]);

  useEffect(() => {
    async function load() {
      // 🚨 Naive getSession() without signature validation
      const { data: { session } } = await supabase.auth.getSession();
      if (session) {
        setUser(session.user);
        // 🚨 Unbounded select(*) bypassing RLS with service role client
        const { data: orgData } = await supabase.from('org_records').select('*');
        setData(orgData || []);
      }
    }
    load();
  }, []);

  return <div>Welcome {user?.email}</div>;
}
```

#### What Broke & Why:
1. **Critical Security Leak**: The agent used `SUPABASE_SERVICE_ROLE_KEY` directly in a `'use client'` component, exposing admin database access to the public web inspector.
2. **Session Hijacking Vulnerability**: Using `getSession()` on untrusted client storage allowed forged cookies to mimic authorized user IDs without cryptographic verification.
3. **SEO & Performance Ruined**: Turning the entire dashboard into a Client Component broke streaming SSR, caused layout shifts, and resulted in waterfalled client fetches.

---

### ✅ The Hardened Implementation (Governed by Antigravity Preset)

```typescript
// app/dashboard/page.tsx
// ✅ Stays a pure Server Component by default
import { createClient } from '@/utils/supabase/server';
import { redirect } from 'next/navigation';
import { UserProfileBadge } from './components/UserProfileBadge';

export default async function DashboardPage() {
  const supabase = await createClient();

  // ✅ Cryptographically verified user lookup via Supabase Auth server
  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) {
    redirect('/login');
  }

  // ✅ Explicit column selection bounded by Row-Level Security (RLS)
  const { data: orgData, error: dbError } = await supabase
    .from('org_records')
    .select('id, name, created_at, role')
    .eq('user_id', user.id);

  if (dbError) {
    throw new Error('Failed to load organization records');
  }

  return (
    <main className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        {/* ✅ Interactivity isolated to leaf-level client component */}
        <UserProfileBadge email={user.email!} />
      </div>
      <section>
        {orgData.map((record) => (
          <div key={record.id} className="p-4 border rounded my-2">
            {record.name} - <span className="text-sm text-gray-500">{record.role}</span>
          </div>
        ))}
      </section>
    </main>
  );
}
```

```typescript
// app/dashboard/components/UserProfileBadge.tsx
'use client'; // ✅ Only the small interactive badge is a client component

import { useState } from 'react';

export function UserProfileBadge({ email }: { email: string }) {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <div className="relative">
      <button onClick={() => setIsOpen(!isOpen)} className="px-3 py-1 bg-gray-100 rounded">
        {email}
      </button>
      {isOpen && (
        <div className="absolute right-0 mt-2 p-2 bg-white shadow rounded">
          <form action="/auth/signout" method="post">
            <button type="submit" className="text-red-600 text-sm">Sign Out</button>
          </form>
        </div>
      )}
    </div>
  );
}
```

#### Incident Post-Mortem Avoided:
By enforcing leaf-level `'use client'` quarantine, cryptographically signed `getUser()` authentication, and server-side RLS queries, the hardened rules prevented a complete admin credential leak and ensured zero hydration mismatches during server rendering.
