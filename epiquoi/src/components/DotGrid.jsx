import React, { useRef, useEffect } from 'react';

export const DotGrid = ({ children, className = "" }) => {
    const canvasRef = useRef(null);
    const containerRef = useRef(null);
    const mouse = useRef({ x: -1000, y: -1000 });

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        let animationFrameId;

        // Configuration for "Subtle & Professional"
        const spacing = 40;     // Wider spacing = less noise
        const dotSize = 1.5;    // Delicate dots
        const effectRadius = 180; // Larger area of influence
        const colors = ['#013afb', '#4871fb', '#8faeff', '#013afb'];

        const resize = () => {
            if (containerRef.current) {
                canvas.width = containerRef.current.offsetWidth;
                canvas.height = containerRef.current.offsetHeight;
            }
        };

        window.addEventListener('resize', resize);
        resize();

        class Dot {
            constructor(x, y) {
                this.x = x;
                this.y = y;
                this.baseX = x;
                this.baseY = y;
                this.vx = 0;
                this.vy = 0;
                this.targetColor = '#e2e8f0';
            }

            draw() {
                const dx = mouse.current.x - this.baseX;
                const dy = mouse.current.y - this.baseY;
                const distance = Math.sqrt(dx * dx + dy * dy);

                let targetX = this.baseX;
                let targetY = this.baseY;

                // Interaction
                if (distance < effectRadius) {
                    const force = (effectRadius - distance) / effectRadius;
                    const angle = Math.atan2(dy, dx);
                    // Smooth Magnet Pull (Bouncy)
                    const moveDistance = force * 50;
                    targetX = this.baseX + Math.cos(angle) * moveDistance;
                    targetY = this.baseY + Math.sin(angle) * moveDistance;

                    // Color mapping
                    const colorIndex = Math.floor((this.baseX + this.baseY) % colors.length);
                    this.targetColor = colors[colorIndex];
                } else {
                    this.targetColor = '#e2e8f0';
                }

                // Spring Physics (The "Bounce")
                const ax = (targetX - this.x) * 0.04; // Low stiffness = soft bounce
                const ay = (targetY - this.y) * 0.04;

                this.vx += ax;
                this.vy += ay;
                this.vx *= 0.85; // Friction
                this.vy *= 0.85;

                this.x += this.vx;
                this.y += this.vy;

                // Draw with VERY low opacity for subtle high-tech feel
                // Active: 0.5 opacity, Inactive: 0.15 (barely visible structure)
                const alpha = distance < effectRadius ? 0.5 : 0.15;

                ctx.globalAlpha = alpha;
                ctx.fillStyle = this.targetColor;

                ctx.beginPath();
                ctx.arc(this.x, this.y, dotSize, 0, Math.PI * 2);
                ctx.fill();
                ctx.globalAlpha = 1.0; // Reset
            }
        }

        let dots = [];
        const initDots = () => {
            dots = [];
            for (let x = 0; x < canvas.width; x += spacing) {
                for (let y = 0; y < canvas.height; y += spacing) {
                    dots.push(new Dot(x, y));
                }
            }
        }

        initDots();
        window.addEventListener('resize', initDots);

        const render = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            dots.forEach(dot => dot.draw());
            animationFrameId = requestAnimationFrame(render);
        };

        render();

        return () => {
            window.removeEventListener('resize', resize);
            window.removeEventListener('resize', initDots);
            cancelAnimationFrame(animationFrameId);
        };
    }, []);

    const handleMouseMove = (e) => {
        if (!containerRef.current) return;
        const rect = containerRef.current.getBoundingClientRect();
        mouse.current = {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
    };

    const handleMouseLeave = () => {
        mouse.current = { x: -1000, y: -1000 };
    };

    return (
        <div
            ref={containerRef}
            onMouseMove={handleMouseMove}
            onMouseLeave={handleMouseLeave}
            className={`relative w-full h-full bg-slate-50 overflow-hidden ${className}`}
        >
            <canvas
                ref={canvasRef}
                className="absolute inset-0 z-0 pointer-events-none"
            />
            <div className="relative z-10 w-full h-full flex flex-col pointer-events-auto">
                {children}
            </div>
        </div>
    );
};
