import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { DottedSurface } from "@/components/ui/dotted-surface"
import { Link } from "react-router-dom"

export default function Signup() {
  return (
    <div className="relative min-h-screen flex items-center justify-center bg-gradient-to-b from-white via-white to-gray-50 dark:from-black dark:via-zinc-900 dark:to-black">
      <DottedSurface className="opacity-60 dark:opacity-90" />
      <Card className="relative z-10 w-full max-w-md bg-white/70 border-gray-200/70 dark:bg-zinc-900 dark:border-zinc-800">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl text-gray-900 dark:text-white">Create an account</CardTitle>
          <CardDescription className="text-gray-600 dark:text-zinc-400">
            Start building with VibeCober
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name" className="text-gray-700 dark:text-zinc-300">
              Name
            </Label>
            <Input
              id="name"
              placeholder="Madhukar Reddy"
              className="bg-white/80 border-gray-200 text-gray-900 placeholder:text-gray-500 dark:bg-zinc-800 dark:border-zinc-700 dark:text-white dark:placeholder:text-zinc-400"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="email" className="text-gray-700 dark:text-zinc-300">
              Email
            </Label>
            <Input
              id="email"
              type="email"
              placeholder="you@vibecober.ai"
              className="bg-white/80 border-gray-200 text-gray-900 placeholder:text-gray-500 dark:bg-zinc-800 dark:border-zinc-700 dark:text-white dark:placeholder:text-zinc-400"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password" className="text-gray-700 dark:text-zinc-300">
              Password
            </Label>
            <Input
              id="password"
              type="password"
              className="bg-white/80 border-gray-200 text-gray-900 placeholder:text-gray-500 dark:bg-zinc-800 dark:border-zinc-700 dark:text-white dark:placeholder:text-zinc-400"
            />
          </div>

          <Button className="w-full">Create Account</Button>

          <p className="text-sm text-center text-gray-600 dark:text-zinc-400">
            Already have an account?{" "}
            <Link to="/login" className="text-gray-900 hover:underline dark:text-white">
              Sign in
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
