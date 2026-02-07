
interface Diagnostic {
    message: string;
    startLine: number;
    endLine: number;
    severity: 'error' | 'warning' | 'info';
}

export class LSP {
    static async validate(content: string, language: string): Promise<Diagnostic[]> {
        // Simulate server latency
        await new Promise(r => setTimeout(r, 600));

        const lines = content.split('\n');
        const diagnostics: Diagnostic[] = [];

        // Simple heuristic-based diagnostics

        if (language === 'python') {
            // Python heuristics
            lines.forEach((line, i) => {
                // Check for missing colon in def/if/for/while
                if (/^\s*(def|if|for|while|class)\s/.test(line) && !line.trim().endsWith(':')) {
                    diagnostics.push({
                        message: "SyntaxError: expected ':'",
                        startLine: i + 1,
                        endLine: i + 1,
                        severity: 'error'
                    });
                }

                // Check for print statement usage (Python 2 style check just for fun)
                if (/print\s+".*"/.test(line)) {
                    diagnostics.push({
                        message: "SyntaxError: Missing parentheses in call to 'print'. Did you mean print(...)?",
                        startLine: i + 1,
                        endLine: i + 1,
                        severity: 'error'
                    });
                }
            });
        }

        if (language === 'typescript') {
            // TS heuristics
            lines.forEach((line, i) => {
                // Check for console.log usage (warning)
                if (line.includes('console.log')) {
                    diagnostics.push({
                        message: "No console.log allowed in production code",
                        startLine: i + 1,
                        endLine: i + 1,
                        severity: 'warning'
                    });
                }

                // Check for explicit 'any' type
                if (line.includes(': any')) {
                    diagnostics.push({
                        message: "Unexpected any. Specify a different type.",
                        startLine: i + 1,
                        endLine: i + 1,
                        severity: 'warning'
                    });
                }
            });
        }

        return diagnostics;
    }
}
