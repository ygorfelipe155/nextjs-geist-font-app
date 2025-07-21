#!/usr/bin/env node
/**
 * Safe Startup Script for Next.js Application
 * Prevents 502 Bad Gateway errors and ensures stable server initialization
 */

const { spawn, exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const net = require('net');

class SafeNextStarter {
    constructor() {
        this.port = 8000;
        this.maxRetries = 5;
        this.retryDelay = 2000;
        this.healthCheckInterval = 5000;
        this.serverProcess = null;
        this.isShuttingDown = false;
        
        // Setup signal handlers
        process.on('SIGINT', () => this.gracefulShutdown());
        process.on('SIGTERM', () => this.gracefulShutdown());
        process.on('uncaughtException', (error) => {
            console.error('❌ Uncaught Exception:', error);
            this.gracefulShutdown();
        });
    }

    log(message) {
        const timestamp = new Date().toISOString();
        console.log(`[${timestamp}] ${message}`);
        
        // Also log to file
        const logEntry = `${timestamp} - ${message}\n`;
        fs.appendFileSync('server.log', logEntry);
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
                if (error) {
                    this.log(`⚠️  No process found on port ${port} or failed to kill`);
                } else {
                    this.log(`✅ Killed process on port ${port}`);
                }
                resolve();
            });
        });
    }

    async waitForServer(maxWaitTime = 30000) {
        const startTime = Date.now();
        
        while (Date.now() - startTime < maxWaitTime) {
            try {
                const response = await fetch(`http://localhost:${this.port}`);
                if (response.ok || response.status < 500) {
                    this.log('✅ Server is responding');
                    return true;
                }
            } catch (error) {
                // Server not ready yet
            }
            
            await new Promise(resolve => setTimeout(resolve, 1000));
            process.stdout.write('.');
        }
        
        return false;
    }

    async optimizeMemory() {
        this.log('🧹 Optimizing memory usage...');
        
        // Force garbage collection if available
        if (global.gc) {
            global.gc();
            this.log('✅ Garbage collection completed');
        }
        
        // Set Node.js memory optimization flags
        process.env.NODE_OPTIONS = '--max-old-space-size=1024 --optimize-for-size';
    }

    async checkSystemResources() {
        this.log('🔍 Checking system resources...');
        
        try {
            const memInfo = await new Promise((resolve, reject) => {
                exec('free -m', (error, stdout) => {
                    if (error) reject(error);
                    else resolve(stdout);
                });
            });
            
            const lines = memInfo.split('\n');
            const memLine = lines.find(line => line.startsWith('Mem:'));
            if (memLine) {
                const parts = memLine.split(/\s+/);
                const available = parseInt(parts[6] || parts[3]);
                
                this.log(`💾 Available memory: ${available}MB`);
                
                if (available < 256) {
                    this.log('⚠️  Low memory detected, applying optimizations...');
                    await this.optimizeMemory();
                }
            }
        } catch (error) {
            this.log('⚠️  Could not check memory, continuing...');
        }
    }

    async startServer() {
        this.log('🚀 Starting Next.js development server...');
        
        // Ensure port is free
        const isPortFree = await this.checkPort(this.port);
        if (!isPortFree) {
            this.log(`⚠️  Port ${this.port} is in use, attempting to free it...`);
            await this.killProcessOnPort(this.port);
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
        
        // Start the server
        this.serverProcess = spawn('npm', ['run', 'dev'], {
            stdio: ['pipe', 'pipe', 'pipe'],
            env: {
                ...process.env,
                PORT: this.port.toString(),
                NODE_ENV: 'development',
                NEXT_TELEMETRY_DISABLED: '1'
            }
        });

        // Handle server output
        this.serverProcess.stdout.on('data', (data) => {
            const output = data.toString().trim();
            if (output) {
                console.log(output);
            }
        });

        this.serverProcess.stderr.on('data', (data) => {
            const output = data.toString().trim();
            if (output && !output.includes('ExperimentalWarning')) {
                console.error(output);
            }
        });

        this.serverProcess.on('close', (code) => {
            if (!this.isShuttingDown) {
                this.log(`❌ Server process exited with code ${code}`);
                this.handleServerCrash();
            }
        });

        this.serverProcess.on('error', (error) => {
            this.log(`❌ Server process error: ${error.message}`);
            this.handleServerCrash();
        });

        // Wait for server to be ready
        this.log('⏳ Waiting for server to be ready...');
        process.stdout.write('Loading');
        
        const isReady = await this.waitForServer();
        console.log(''); // New line after dots
        
        if (isReady) {
            this.log('🎉 Server is ready and responding!');
            this.log(`🌐 Access your application at: http://localhost:${this.port}`);
            this.startHealthCheck();
            return true;
        } else {
            this.log('❌ Server failed to start within timeout period');
            return false;
        }
    }

    startHealthCheck() {
        this.log('💓 Starting health monitoring...');
        
        const healthCheck = setInterval(async () => {
            if (this.isShuttingDown) {
                clearInterval(healthCheck);
                return;
            }

            try {
                const response = await fetch(`http://localhost:${this.port}`, {
                    timeout: 5000
                });
                
                if (!response.ok && response.status >= 500) {
                    this.log('⚠️  Server health check failed, restarting...');
                    this.restartServer();
                }
            } catch (error) {
                this.log('⚠️  Server is not responding, checking process...');
                
                if (this.serverProcess && this.serverProcess.killed) {
                    this.log('❌ Server process died, restarting...');
                    this.restartServer();
                }
            }
        }, this.healthCheckInterval);
    }

    async restartServer() {
        this.log('🔄 Restarting server...');
        
        if (this.serverProcess) {
            this.serverProcess.kill('SIGTERM');
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
        
        await this.killProcessOnPort(this.port);
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        await this.startServer();
    }

    handleServerCrash() {
        if (this.isShuttingDown) return;
        
        this.log('💥 Server crashed, attempting restart...');
        setTimeout(() => this.restartServer(), this.retryDelay);
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
        this.log('=' .repeat(60));
        this.log('🚀 SAFE NEXT.JS STARTUP - PREVENTING 502 ERRORS');
        this.log('=' .repeat(60));
        
        try {
            // Pre-flight checks
            await this.checkSystemResources();
            await this.optimizeMemory();
            
            // Start server with retries
            let attempt = 1;
            while (attempt <= this.maxRetries) {
                this.log(`🎯 Startup attempt ${attempt}/${this.maxRetries}`);
                
                const success = await this.startServer();
                if (success) {
                    this.log('🎉 Startup completed successfully!');
                    
                    // Keep process alive
                    process.stdin.resume();
                    return;
                }
                
                if (attempt < this.maxRetries) {
                    this.log(`⏳ Waiting ${this.retryDelay}ms before retry...`);
                    await new Promise(resolve => setTimeout(resolve, this.retryDelay));
                }
                
                attempt++;
            }
            
            this.log('❌ Failed to start server after all attempts');
            process.exit(1);
            
        } catch (error) {
            this.log(`❌ Critical error during startup: ${error.message}`);
            process.exit(1);
        }
    }
}

// Start the safe launcher
const launcher = new SafeNextStarter();
launcher.start().catch(error => {
    console.error('❌ Fatal error:', error);
    process.exit(1);
});
