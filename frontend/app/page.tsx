import { redirect } from 'next/navigation';

export default function HomePage() {
  // The public landing page is served from frontend/dist.
  // If you run the IDE app (Next.js), route / should go to the IDE.
  redirect('/replit-ide');
}
