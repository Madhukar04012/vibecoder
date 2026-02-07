
import { useIDE } from './src/ide/store';

// Mock timers for faster testing? 
// No, let's run with real simulated delays to prove timing works.
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

async function runTest() {
    console.log('🤖 Starting Headless IDE Behavioral Test...\n');

    const store = useIDE;

    // 1. Initial State
    console.log('1. Checking Initial State...');
    const initialState = store.getState();
    if (initialState.mode !== 'idle') throw new Error('Mode should be idle');
    if (initialState.dbConnected) throw new Error('DB should be disconnected');
    console.log('✅ Initial state verified.\n');

    // 2. Tab Management
    console.log('2. Testing Tab Management...');
    store.getState().openFile('frontend/app/page.tsx');
    const afterOpen = store.getState();
    if (afterOpen.activeFile !== 'frontend/app/page.tsx') throw new Error('Active file did not update');
    if (!afterOpen.openFiles.includes('frontend/app/page.tsx')) throw new Error('Open files list incorrect');
    console.log(`✅ Opened tab: ${afterOpen.activeFile}`);

    // Switch back
    store.getState().setActiveFile('backend/main.py');
    if (store.getState().activeFile !== 'backend/main.py') throw new Error('Context switch failed');
    console.log(`✅ Switched context to: ${store.getState().activeFile}\n`);

    // 3. Execution Failure (Context-Aware)
    console.log('3. Testing Execution Failure (Missing Infra)...');

    // Switch to Cloud Mode to enforce DB requirement
    console.log('   > enable cloud (to trigger strict mode)');
    store.getState().toggleCloud(true);

    console.log('   Running backend/main.py without DB...');

    await store.getState().run();

    // Wait for run to finish (simulated 3-4s)
    let retries = 0;
    while (store.getState().mode === 'running' && retries < 50) {
        await sleep(200);
        process.stdout.write('.');
        retries++;
    }
    console.log('');

    const consoleLog = store.getState().console.join('\n');
    if (!consoleLog.includes('Database not provisioned')) {
        console.error('❌ Expected DB error not found in logs:');
        console.log(consoleLog);
        process.exit(1);
    }
    console.log('✅ Correctly failed: "Database not provisioned"');
    if (store.getState().mode !== 'error') throw new Error('Mode should be error');
    console.log('✅ Mode transitioned to "error"\n');

    // 4. Chat-to-Infra (Simulated)
    console.log('4. Testing Infrastructure Provisioning...');
    // Cloud already enabled in step 3
    console.log('   (Cloud already enabled)');
    console.log('   > connect db');
    store.getState().toggleDB(true);

    if (!store.getState().dbConnected || !store.getState().cloudEnabled) {
        throw new Error('Infrastructure toggles failed');
    }
    console.log('✅ Infrastructure Provisioned.\n');

    // 5. Execution Success
    console.log('5. Testing Execution Success...');
    // Reset error mode
    store.getState().reset();

    console.log('   Running backend/main.py with DB...');
    await store.getState().run();

    retries = 0;
    while (store.getState().mode === 'running' && retries < 50) {
        await sleep(200);
        process.stdout.write('.');
        retries++;
    }
    console.log('');

    const successLog = store.getState().console.join('\n');
    if (!successLog.includes('Connected to postgres')) {
        console.error('❌ Expected Postgres connection not found:');
        console.log(successLog);
        process.exit(1);
    }
    console.log('✅ Success: "Connected to postgres"');
    console.log(`✅ Final Mode: ${store.getState().mode}`);

    console.log('\n🎉 ALL BEHAVIORAL CHECKS PASSED.');
    process.exit(0);
}

runTest().catch(e => {
    console.error('\n❌ TEST FAILED:', e);
    process.exit(1);
});
