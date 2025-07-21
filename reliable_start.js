#!/usr/bin/env node
/**
 * Reliable Next.js Startup Script
 * Simple and stable server initialization without problematic flags
 */

const { spawn, exec } = require('child_process');
const fs = require('fs');
const net = require('net');

class ReliableStarter {
    constructor() {
        this.port = 8000;
        this.serverProcess = null;
        this.isShuttingDown = false;
        
        // Setup signal handlers
        process.on('SIGINT', () => this.gracefulShutdown());
        process.on('SIGTERM', () => this.gracefulShutdown());
    }

    log(message) {
        const timestamp = new Date().toISOString();
        console.log(`[${timestamp}] ${message}`);
    }

    async checkPort(port) {
        return new Promise((resolve) => {
            const server = net.createServer();
            
            server.listen(port, () => {
                server.once('close', () => resolve(true));
                server.close();
            });
            
            server.on('error', () => resolve(false));
        });
    }

    async killProcessOnPort(port) {
        return new Promise((resolve) => {
            exec(`fuser -k ${port}/tcp`, (error) => {
                setTimeout(resolve, 1000); // Always wait a bit
            });
        });
    }

    async waitForServer(maxWaitTime = 45000) {
        const startTime = Date.now();
        let dots = 0;
        
        this.log('⏳ Waiting for server to be ready...');
        
        while (Date.now() - startTime < maxWaitTime) {
            try {
                // Try to connect to the server
                const response = await fetch(`http://localhost:${this.port}`, {
                    signal: AbortSignal.timeout(3000)
                });
                
                if (response.status < 500) {
                    console.log(''); // New line
                    this.log('✅ Server is responding!');
                    return true;
                }
            } catch (error) {
                // Server not ready yet, continue waiting
            }
            
            // Show progress
            process.stdout.write('.');
            dots++;
            if (dots % 50 === 0) {
                console.log(''); // New line every 50 dots
            }
            
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
        
        console.log(''); // New line
        return false;
    }

    async startServer() {
        this.log('🚀 Starting Next.js development server...');
        
        // Ensure port is free
        const isPortFree = await this.checkPort(this.port);
        if (!isPortFree) {
            this.log(`⚠️  Port ${this.port} is in use, freeing it...`);
            await this.killProcessOnPort(this.port);
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
        
        // Start the server with clean environment
        this.serverProcess = spawn('npm', ['run', 'dev'], {
            stdio: ['pipe', 'pipe', 'pipe'],
            env: {
                ...process.env,
                PORT: this.port.toString(),
                NODE_ENV: 'development',
                NEXT_TELEMETRY_DISABLED: '1',
                // Remove problematic NODE_OPTIONS
                NODE_OPTIONS: '--max-old-space-size=1024'
            }
        });

        // Handle server output
        this.serverProcess.stdout.on('data', (data) => {
            const output = data.toString().trim();
            if (output && !output.includes('webpack') && !output.includes('compiled')) {
                console.log(output);
            }
        });

        this.serverProcess.stderr.on('data', (data) => {
            const output = data.toString().trim();
            if (output && 
                !output.includes('ExperimentalWarning') && 
                !output.includes('webpack') &&
                !output.includes('Fast Refresh')) {
                console.error(output);
            }
        });

        this.serverProcess.on('close', (code) => {
            if (!this.isShuttingDown) {
                this.log(`❌ Server process exited with code ${code}`);
            }
        });

        this.serverProcess.on('error', (error) => {
            this.log(`❌ Server process error: ${error.message}`);
        });

        // Wait for server to be ready
        const isReady = await this.waitForServer();
        
        if (isReady) {
            this.log('🎉 Server is ready and responding!');
            this.log(`🌐 Access your application at: http://localhost:${this.port}`);
            this.log('💡 Press Ctrl+C to stop the server');
            return true;
        } else {
            this.log('❌ Server failed to start within timeout period');
            return false;
        }
    }

    async gracefulShutdown() {
        if (this.isShuttingDown) return;
        
        this.isShuttingDown = true;
        this.log('⏹️  Shutting down gracefully...');
        
        if (this.serverProcess) {
            this.serverProcess.kill('SIGTERM');
            
            // Wait for graceful shutdown
            await new Promise(resolve => {
                const timeout = setTimeout(() => {
                    this.log('⚠️  Force killing server process...');
                    this.serverProcess.kill('SIGKILL');
                    resolve();
                }, 5000);
                
                this.serverProcess.on('close', () => {
                    clearTimeout(timeout);
                    resolve();
                });
            });
        }
        
        this.log('✅ Shutdown complete');
        process.exit(0);
    }

    async start() {
        this.log('=' .repeat(50));
        this.log('🚀 RELIABLE NEXT.JS STARTUP');
        this.log('=' .repeat(50));
        
        try {
            const success = await this.startServer();
            
            if (success) {
                this.log('🎉 Startup completed successfully!');
                
                // Keep process alive
                process.stdin.resume();
                
                // Simple health monitoring
                setInterval(async () => {
                    if (this.isShuttingDown) return;
                    
                    try {
                        await fetch(`http://localhost:${this.port}`, {
                            signal: AbortSignal.timeout(5000)
                        });
                    } catch (error) {
                        this.log('⚠️  Server health check failed');
                    }
                }, 30000); // Check every 30 seconds
                
            } else {
                this.log('❌ Failed to start server');
                process.exit(1);
            }
            
        } catch (error) {
            this.log(`❌ Critical error during startup: ${error.message}`);
            process.exit(1);
        }
    }
}

// Start the reliable launcher
const launcher = new ReliableStarter();
launcher.start().catch(error => {
    console.error('❌ Fatal error:', error);
    process.exit(1);
});
