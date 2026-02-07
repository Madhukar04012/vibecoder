interface ExecutionResult {
    success: boolean;
    logs: string[];
    error?: string;
}

interface ExecutionContext {
    file: string;
    isLocal: boolean;
    cloudEnabled: boolean;
    dbConnected: boolean;
    githubConnected: boolean;
}

export class RuntimeEngine {
    private static readonly DELAYS = {
        BOOT: 800,
        COMPILE: 1200,
        TEST: 600,
        DB_CHECK: 400,
    };

    static async execute(ctx: ExecutionContext, onLog: (log: string) => void): Promise<ExecutionResult> {
        const { file, dbConnected } = ctx;
        const isTest = file.includes('test');
        const isPython = file.endsWith('.py');
        const isBackend = file.includes('backend');

        // Helper for streaming logs with delay
        const stream = async (msg: string, delay: number = 300) => {
            await new Promise(r => setTimeout(r, delay));
            const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false });
            const prefix = isBackend ? '[backend]' : '[frontend]';
            onLog(`${timestamp} ${prefix} ${msg}`);
        };

        // 1. Boot / Compile Phase
        if (isPython) {
            await stream('Spawned process (PID 14203)...', this.DELAYS.BOOT);
            await stream('Loading environment variables from .env');
        } else {
            await stream('vite v5.1.4 dev server running at:', this.DELAYS.BOOT);
            await stream('  ➜  Local:   http://localhost:5173/');
        }

        // 2. Dependency Check (The "Real" Integration)
        if (isBackend) {
            await stream('Checking database connection...', this.DELAYS.DB_CHECK);

            if (!dbConnected && !ctx.isLocal) {
                // If we are in "cloud mode" (simulated via chat) but DB is missing
                await stream('ERROR: Connection refused at postgres:5432');
                await stream('HINT: Database not provisioned. Run "connect db" in command surface.');
                return {
                    success: false,
                    logs: [],
                    error: 'Database connection failed'
                };
            }

            if (dbConnected) {
                await stream('✓ Connected to postgres:15 (0.4ms)');
                await stream('Running migrations...');
                await stream('✓ User schema up to date');
            } else {
                await stream('⚠ Warning: Running with local SQLite fallback (Production DB required for deep tasks)');
            }
        }

        // 3. Execution Phase
        await stream(isTest ? 'Running test suite...' : 'Starting application server...', this.DELAYS.COMPILE);

        if (isTest) {
            await stream('PASS  tests/auth.test.ts');
            await stream('PASS  tests/integration.test.ts');
            await stream('Test Suites: 2 passed, 2 total');
            return { success: true, logs: [] };
        }

        // 4. Runtime (Simulated loop)
        await stream('Application ready in 2.4s');
        if (isPython) {
            await stream('INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)');
            await stream('INFO:     Started server process [14203]');
            await stream('INFO:     Waiting for application startup.');
            await stream('INFO:     Application startup complete.');
        }

        return { success: true, logs: [] };
    }
}
